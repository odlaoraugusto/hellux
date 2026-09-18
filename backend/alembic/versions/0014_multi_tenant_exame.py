"""fundação multi-tenant (RLS + SUPER_ADMIN) e fluxo de Exame unificado

Revision ID: 0014_multi_tenant_exame
Revises: 0013_rename_email_to_login
Create Date: 2026-09-18

Fase 1 do Hellux (ver docs/plano da Fase 1):

1. Cria `tenants` (raiz da hierarquia multi-tenant, sem RLS nela mesma) e
   um único tenant, atribuído a TODOS os dados já existentes.
2. Adiciona `tenant_id` a `usuarios` (nullable - só é NULL para o perfil
   SUPER_ADMIN), `pacientes`, `setores`, `materiais`, `microrganismos`,
   `antimicrobianos` (NOT NULL) e `logs_auditoria` (nullable, sem RLS -
   é só um snapshot de auditoria).
3. Adiciona o perfil SUPER_ADMIN ao enum de usuários - um usuário desse
   perfil não pertence a tenant nenhum, gerencia a lista de tenants.
4. Cria o catálogo `tipos_cultura` (tenant-scoped) e as 3 tabelas do
   fluxo de Exame unificado (`exames`, `exame_isolados`,
   `exame_antibiogramas`), migra os dados de
   `solicitacoes`+`culturas`+`cultura_microrganismos`+`antibiogramas`+
   `antibiograma_resultados` para elas, e então DROPA as tabelas antigas.
5. Habilita Row Level Security "de verdade" (ENABLE + FORCE + policy) em
   toda tabela tenant-scoped, com uma SEGUNDA policy permissiva (RLS
   combina policies permissivas com OR) que libera acesso total quando
   `app.is_super_admin = 'true'`.

Mapeamento de status (Solicitação+Cultura -> Exame, ver
`StatusExameEnum` em app/models/exame.py):

- Sem cultura associada (solicitação nunca chegou a virar cultura):
  AGUARDANDO_COLETA/COLETADO/EM_ANALISE/LIBERADO -> AGUARDANDO_TRIAGEM;
  CANCELADO -> AGUARDANDO_TRIAGEM (o enum novo não tem um equivalente a
  "cancelado" - o dado original fica preservado em `observacoes`).
- Com cultura: EM_ANALISE -> AGUARDANDO_TRIAGEM; NEGATIVA -> NEGATIVO ou
  NEGATIVO_PARCIAL (conforme `liberado_tecnicamente`); POSITIVA ->
  POSITIVO ou POSITIVO_PARCIAL (idem); CONTAMINADA -> CONTAMINACAO
  (não existe variante parcial pra contaminação no novo enum).

IMPORTANTE: rodar primeiro contra uma cópia do banco de demonstração
(hellux-demo), NUNCA direto no ambiente real - ver seção "Sequenciamento"
do plano da Fase 1.
"""
import uuid
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0014_multi_tenant_exame"
down_revision: Union[str, None] = "0013_rename_email_to_login"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID_COL = postgresql.UUID(as_uuid=True)

NOME_TENANT_MIGRADO = "Hellux (tenant migrado)"

GRUPOS_CULTURA_ANTIGOS = ["HEMOCULTURA", "CULTURA_GERAL", "VIGILANCIA", "BK", "FUNGOS"]

# Tabelas que recebem Row Level Security de verdade (ENABLE + FORCE +
# policy de isolamento por tenant + policy extra de SUPER_ADMIN).
TABELAS_COM_RLS = [
    "usuarios",
    "pacientes",
    "setores",
    "materiais",
    "microrganismos",
    "antimicrobianos",
    "tipos_cultura",
    "exames",
    "exame_isolados",
    "exame_antibiogramas",
]


def _catalogo_colunas_padrao():
    return [
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id", UUID_COL, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("descricao", sa.String(length=300), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    ]


def upgrade() -> None:
    bind = op.get_bind()
    tenant_id = uuid.uuid4()
    agora = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # 1. Tabela `tenants` + o único tenant migrado.
    # ------------------------------------------------------------------
    op.create_table(
        "tenants",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("nome_fantasia", sa.String(length=200), nullable=False),
        sa.Column("razao_social", sa.String(length=200), nullable=True),
        sa.Column("cnpj", sa.String(length=20), nullable=True, unique=True),
        sa.Column("logo_url", sa.String(length=500), nullable=True),
        sa.Column("subtitulo_cabecalho", sa.String(length=200), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    tenants_tbl = sa.table(
        "tenants", sa.column("id", UUID_COL), sa.column("nome_fantasia", sa.String)
    )
    op.bulk_insert(tenants_tbl, [{"id": tenant_id, "nome_fantasia": NOME_TENANT_MIGRADO}])

    # ------------------------------------------------------------------
    # 2. `tenant_id` nas tabelas de catálogo/negócio já existentes.
    # ------------------------------------------------------------------
    tabelas_nao_null = ["pacientes", "setores", "materiais", "microrganismos", "antimicrobianos"]
    for tabela in tabelas_nao_null:
        op.add_column(tabela, sa.Column("tenant_id", UUID_COL, nullable=True))
        op.execute(f"UPDATE {tabela} SET tenant_id = '{tenant_id}'")
        op.alter_column(tabela, "tenant_id", nullable=False)
        op.create_foreign_key(f"fk_{tabela}_tenant_id", tabela, "tenants", ["tenant_id"], ["id"])
        op.create_index(f"ix_{tabela}_tenant_id", tabela, ["tenant_id"])

    # `usuarios.tenant_id` fica NULLABLE (só é NULL para SUPER_ADMIN).
    op.add_column("usuarios", sa.Column("tenant_id", UUID_COL, nullable=True))
    op.execute(f"UPDATE usuarios SET tenant_id = '{tenant_id}'")
    op.create_foreign_key("fk_usuarios_tenant_id", "usuarios", "tenants", ["tenant_id"], ["id"])
    op.create_index("ix_usuarios_tenant_id", "usuarios", ["tenant_id"])

    # `logs_auditoria.tenant_id` fica nullable e sem RLS (snapshot de
    # auditoria - ver app/models/log_auditoria.py).
    op.add_column("logs_auditoria", sa.Column("tenant_id", UUID_COL, nullable=True))
    op.create_foreign_key(
        "fk_logs_auditoria_tenant_id", "logs_auditoria", "tenants", ["tenant_id"], ["id"]
    )
    op.create_index("ix_logs_auditoria_tenant_id", "logs_auditoria", ["tenant_id"])

    # ------------------------------------------------------------------
    # 3. Uniques antigas (globais) viram uniques compostas por tenant.
    # ------------------------------------------------------------------
    op.drop_index("ix_pacientes_prontuario", table_name="pacientes")
    op.drop_constraint("uq_pacientes_prontuario", "pacientes", type_="unique")
    op.create_unique_constraint(
        "uq_pacientes_tenant_prontuario", "pacientes", ["tenant_id", "prontuario"]
    )
    op.create_index("ix_pacientes_prontuario", "pacientes", ["prontuario"])

    op.drop_index("ix_setores_nome", table_name="setores")
    op.drop_constraint("uq_setores_nome", "setores", type_="unique")
    op.create_unique_constraint("uq_setores_tenant_nome", "setores", ["tenant_id", "nome"])
    op.create_index("ix_setores_nome", "setores", ["nome"])

    op.drop_index("ix_materiais_nome", table_name="materiais")
    op.drop_constraint("uq_materiais_nome", "materiais", type_="unique")
    op.create_unique_constraint("uq_materiais_tenant_nome", "materiais", ["tenant_id", "nome"])
    op.create_index("ix_materiais_nome", "materiais", ["nome"])

    op.drop_index("ix_microrganismos_nome", table_name="microrganismos")
    op.drop_constraint("uq_microrganismos_nome", "microrganismos", type_="unique")
    op.create_unique_constraint(
        "uq_microrganismos_tenant_nome", "microrganismos", ["tenant_id", "nome"]
    )
    op.create_index("ix_microrganismos_nome", "microrganismos", ["nome"])

    op.drop_index("ix_antimicrobianos_nome", table_name="antimicrobianos")
    op.drop_constraint("uq_antimicrobianos_nome", "antimicrobianos", type_="unique")
    op.create_unique_constraint(
        "uq_antimicrobianos_tenant_nome", "antimicrobianos", ["tenant_id", "nome"]
    )
    op.create_index("ix_antimicrobianos_nome", "antimicrobianos", ["nome"])

    # ------------------------------------------------------------------
    # 4. Perfil SUPER_ADMIN + regras de tenant_id em `usuarios`.
    # ------------------------------------------------------------------
    op.execute("ALTER TYPE perfil_usuario_enum ADD VALUE IF NOT EXISTS 'SUPER_ADMIN'")

    op.drop_index("ix_usuarios_login", table_name="usuarios")
    op.drop_constraint("uq_usuarios_login", "usuarios", type_="unique")
    op.create_unique_constraint("uq_usuarios_tenant_login", "usuarios", ["tenant_id", "login"])
    op.create_index("ix_usuarios_login", "usuarios", ["login"])
    op.create_index(
        "uq_usuarios_super_admin_login",
        "usuarios",
        ["login"],
        unique=True,
        postgresql_where=sa.text("tenant_id IS NULL"),
    )
    op.create_check_constraint(
        "ck_usuarios_super_admin_sem_tenant",
        "usuarios",
        "(perfil::text = 'SUPER_ADMIN' AND tenant_id IS NULL) OR "
        "(perfil::text <> 'SUPER_ADMIN' AND tenant_id IS NOT NULL)",
    )

    # ------------------------------------------------------------------
    # 5. Catálogo `tipos_cultura` + as 3 tabelas do fluxo de Exame.
    # ------------------------------------------------------------------
    op.create_table("tipos_cultura", *_catalogo_colunas_padrao())
    op.create_unique_constraint(
        "uq_tipos_cultura_tenant_nome", "tipos_cultura", ["tenant_id", "nome"]
    )
    op.create_index("ix_tipos_cultura_nome", "tipos_cultura", ["nome"])
    op.create_index("ix_tipos_cultura_tenant_id", "tipos_cultura", ["tenant_id"])

    tipos_cultura_tbl = sa.table(
        "tipos_cultura",
        sa.column("id", UUID_COL),
        sa.column("tenant_id", UUID_COL),
        sa.column("nome", sa.String),
    )
    mapa_tipo_cultura: dict[str, uuid.UUID] = {}
    linhas_tipo_cultura = []
    for nome in GRUPOS_CULTURA_ANTIGOS:
        novo_id = uuid.uuid4()
        mapa_tipo_cultura[nome] = novo_id
        linhas_tipo_cultura.append({"id": novo_id, "tenant_id": tenant_id, "nome": nome})
    op.bulk_insert(tipos_cultura_tbl, linhas_tipo_cultura)
    tipo_cultura_padrao_id = mapa_tipo_cultura["CULTURA_GERAL"]

    status_exame_enum = postgresql.ENUM(
        "AGUARDANDO_TRIAGEM",
        "NEGATIVO_PARCIAL",
        "POSITIVO_PARCIAL",
        "NEGATIVO",
        "POSITIVO",
        "CONTAMINACAO",
        name="status_exame_enum",
    )
    mecanismo_resistencia_enum = postgresql.ENUM(
        "NENHUM", "MRSA", "ESBL", "CARBAPENEMASE_KPC", "VRE", "D_TESTE_POSITIVO", "OUTRO",
        name="mecanismo_resistencia_enum",
    )
    status_exame_enum.create(bind, checkfirst=True)
    mecanismo_resistencia_enum.create(bind, checkfirst=True)
    status_exame_enum.create_type = False
    mecanismo_resistencia_enum.create_type = False
    # `resultado_sir_enum` já existe (usado antes por `antibiograma_resultados`)
    # e é reaproveitado tal e qual por `exame_antibiogramas` - não recriar.
    resultado_sir_enum = postgresql.ENUM(
        "SENSIVEL", "INTERMEDIARIO", "RESISTENTE", name="resultado_sir_enum"
    )
    resultado_sir_enum.create_type = False

    op.create_table(
        "exames",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id", UUID_COL, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("paciente_id", UUID_COL, sa.ForeignKey("pacientes.id"), nullable=False),
        sa.Column("setor_id", UUID_COL, sa.ForeignKey("setores.id"), nullable=True),
        sa.Column("tipo_cultura_id", UUID_COL, sa.ForeignKey("tipos_cultura.id"), nullable=False),
        sa.Column("material_id", UUID_COL, sa.ForeignKey("materiais.id"), nullable=False),
        sa.Column("data_coleta", sa.DateTime(timezone=True), nullable=False),
        sa.Column("previsao_liberacao", sa.Date(), nullable=True),
        sa.Column(
            "status", status_exame_enum, nullable=False, server_default="AGUARDANDO_TRIAGEM"
        ),
        sa.Column("identificacao_preliminar", sa.String(length=300), nullable=True),
        sa.Column("observacoes", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for coluna in ("tenant_id", "paciente_id", "setor_id", "tipo_cultura_id", "material_id", "status"):
        op.create_index(f"ix_exames_{coluna}", "exames", [coluna])

    op.create_table(
        "exame_isolados",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id", UUID_COL, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("exame_id", UUID_COL, sa.ForeignKey("exames.id"), nullable=False),
        sa.Column(
            "microrganismo_id", UUID_COL, sa.ForeignKey("microrganismos.id"), nullable=False
        ),
        sa.Column(
            "mecanismo_resistencia",
            mecanismo_resistencia_enum,
            nullable=False,
            server_default="NENHUM",
        ),
        sa.Column(
            "nao_realizado_tecnico", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("motivo_dispensa_tsa", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for coluna in ("tenant_id", "exame_id", "microrganismo_id"):
        op.create_index(f"ix_exame_isolados_{coluna}", "exame_isolados", [coluna])

    op.create_table(
        "exame_antibiogramas",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("tenant_id", UUID_COL, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("isolado_id", UUID_COL, sa.ForeignKey("exame_isolados.id"), nullable=False),
        sa.Column(
            "antimicrobiano_id", UUID_COL, sa.ForeignKey("antimicrobianos.id"), nullable=False
        ),
        sa.Column("resultado", resultado_sir_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    for coluna in ("tenant_id", "isolado_id", "antimicrobiano_id"):
        op.create_index(f"ix_exame_antibiogramas_{coluna}", "exame_antibiogramas", [coluna])

    # ------------------------------------------------------------------
    # 6. Migração de dados: Solicitação+Cultura -> Exame, etc.
    # ------------------------------------------------------------------
    _migrar_dados_exame(bind, tenant_id, tipo_cultura_padrao_id, mapa_tipo_cultura)

    # ------------------------------------------------------------------
    # 7. Dropa as tabelas antigas (e seus enums, exceto o reaproveitado
    #    resultado_sir_enum).
    # ------------------------------------------------------------------
    op.drop_table("antibiograma_resultados")
    op.drop_index("ix_antibiogramas_cultura_microrganismo_id", table_name="antibiogramas")
    op.drop_table("antibiogramas")
    op.drop_index("ix_cultura_microrganismos_microrganismo_id", table_name="cultura_microrganismos")
    op.drop_index("ix_cultura_microrganismos_cultura_id", table_name="cultura_microrganismos")
    op.drop_table("cultura_microrganismos")
    op.drop_index("ix_culturas_grupo", table_name="culturas")
    op.drop_index("ix_culturas_solicitacao_id", table_name="culturas")
    op.drop_table("culturas")
    op.drop_index("ix_solicitacoes_paciente_id", table_name="solicitacoes")
    op.drop_table("solicitacoes")

    postgresql.ENUM(name="grupo_cultura_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="resultado_cultura_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="status_solicitacao_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="prioridade_enum").drop(bind, checkfirst=True)

    # ------------------------------------------------------------------
    # 8. Row Level Security de verdade.
    # ------------------------------------------------------------------
    for tabela in TABELAS_COM_RLS:
        op.execute(f"ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY")
        # Comparação como TEXTO, não `current_setting(...)::uuid`. Depois que
        # um GUC customizado como `app.current_tenant_id` é setado (mesmo via
        # SET LOCAL) numa transação da conexão, o Postgres não volta pra NULL
        # quando a transação termina - volta pra STRING VAZIA (confirmado na
        # prática: current_setting(..., true) depois de um SET LOCAL anterior
        # na mesma sessão retorna '' , não NULL). Isso é inofensivo numa
        # comparação de texto (`tenant_id::text = ''` só dá false), mas
        # ""::uuid explode com erro - e como esta policy é combinada via OR
        # com a de SUPER_ADMIN, um erro aqui quebra a query inteira mesmo
        # quando é a OUTRA policy que deveria liberar o acesso. Isso morde
        # de verdade com pooling de conexão: uma conexão reaproveitada que já
        # serviu uma request de um tenant, numa request seguinte de
        # SUPER_ADMIN (que só seta app.is_super_admin, não mexe em
        # app.current_tenant_id), herdaria o resíduo '' do tenant anterior.
        op.execute(
            f"CREATE POLICY {tabela}_tenant_isolation ON {tabela} "
            "USING (tenant_id::text = current_setting('app.current_tenant_id', true))"
        )
        op.execute(
            f"CREATE POLICY {tabela}_super_admin ON {tabela} "
            "USING (current_setting('app.is_super_admin', true) = 'true')"
        )


def _buscar_ou_criar_catalogo(bind, tabela: str, tenant_id, cache: dict, nome: str | None):
    """
    Devolve o id de uma linha do catálogo (`materiais`/`setores`) por
    nome (case-insensitive), criando uma nova linha na hora se ainda não
    existir - usado pra migrar os antigos campos de texto livre
    `Solicitacao.material`/`Solicitacao.origem` pros novos FKs de
    `Exame`.
    """
    if not nome:
        return None
    chave = nome.strip().lower()
    if not chave:
        return None
    if chave in cache:
        return cache[chave]

    linha = bind.execute(
        sa.text(f"SELECT id FROM {tabela} WHERE tenant_id = :tenant_id AND lower(nome) = :nome"),
        {"tenant_id": tenant_id, "nome": chave},
    ).first()
    if linha:
        cache[chave] = linha[0]
        return linha[0]

    novo_id = uuid.uuid4()
    bind.execute(
        sa.text(f"INSERT INTO {tabela} (id, tenant_id, nome) VALUES (:id, :tenant_id, :nome)"),
        {"id": novo_id, "tenant_id": tenant_id, "nome": nome.strip()},
    )
    cache[chave] = novo_id
    return novo_id


def _migrar_dados_exame(bind, tenant_id, tipo_cultura_padrao_id, mapa_tipo_cultura) -> None:
    materiais_cache: dict = {}
    setores_cache: dict = {}

    solicitacoes = bind.execute(
        sa.text(
            "SELECT id, paciente_id, material, origem, status, data_solicitacao, "
            "data_coleta, observacoes FROM solicitacoes"
        )
    ).mappings().all()

    for sol in solicitacoes:
        cultura = bind.execute(
            sa.text(
                "SELECT id, grupo, resultado, liberado_tecnicamente, previsao_liberacao, "
                "observacoes FROM culturas WHERE solicitacao_id = :sid"
            ),
            {"sid": sol["id"]},
        ).mappings().first()

        material_id = _buscar_ou_criar_catalogo(
            bind, "materiais", tenant_id, materiais_cache, sol["material"]
        )
        if material_id is None:
            # `Exame.material_id` é obrigatório - solicitações antigas sem
            # material preenchido (não deveria acontecer, mas o campo era
            # uma string livre) caem num material genérico "Não informado".
            material_id = _buscar_ou_criar_catalogo(
                bind, "materiais", tenant_id, materiais_cache, "Não informado"
            )
        setor_id = _buscar_ou_criar_catalogo(bind, "setores", tenant_id, setores_cache, sol["origem"])

        observacoes_partes = [p for p in (sol["observacoes"], cultura["observacoes"] if cultura else None) if p]

        if cultura is None:
            tipo_cultura_id = tipo_cultura_padrao_id
            status_novo = "AGUARDANDO_TRIAGEM"
            previsao_liberacao = None
            if sol["status"] == "CANCELADO":
                observacoes_partes.append("[migrado] solicitação original estava CANCELADA.")
        else:
            tipo_cultura_id = mapa_tipo_cultura.get(cultura["grupo"], tipo_cultura_padrao_id)
            previsao_liberacao = cultura["previsao_liberacao"]
            resultado = cultura["resultado"]
            liberado = cultura["liberado_tecnicamente"]
            if resultado == "EM_ANALISE":
                status_novo = "AGUARDANDO_TRIAGEM"
            elif resultado == "NEGATIVA":
                status_novo = "NEGATIVO" if liberado else "NEGATIVO_PARCIAL"
            elif resultado == "POSITIVA":
                status_novo = "POSITIVO" if liberado else "POSITIVO_PARCIAL"
            else:  # CONTAMINADA
                status_novo = "CONTAMINACAO"

        data_coleta = sol["data_coleta"]
        if data_coleta is None:
            data_solicitacao = sol["data_solicitacao"]
            data_coleta = (
                datetime.combine(data_solicitacao, datetime.min.time(), tzinfo=timezone.utc)
                if data_solicitacao
                else datetime.now(timezone.utc)
            )

        exame_id = uuid.uuid4()
        bind.execute(
            sa.text(
                "INSERT INTO exames (id, tenant_id, paciente_id, setor_id, tipo_cultura_id, "
                "material_id, data_coleta, previsao_liberacao, status, observacoes) "
                "VALUES (:id, :tenant_id, :paciente_id, :setor_id, :tipo_cultura_id, "
                ":material_id, :data_coleta, :previsao_liberacao, :status, :observacoes)"
            ),
            {
                "id": exame_id,
                "tenant_id": tenant_id,
                "paciente_id": sol["paciente_id"],
                "setor_id": setor_id,
                "tipo_cultura_id": tipo_cultura_id,
                "material_id": material_id,
                "data_coleta": data_coleta,
                "previsao_liberacao": previsao_liberacao,
                "status": status_novo,
                "observacoes": " | ".join(observacoes_partes) if observacoes_partes else None,
            },
        )

        if cultura is None:
            continue

        isolados = bind.execute(
            sa.text(
                "SELECT id, microrganismo_id, sem_antibiograma_padronizado FROM "
                "cultura_microrganismos WHERE cultura_id = :cid"
            ),
            {"cid": cultura["id"]},
        ).mappings().all()

        for isolado in isolados:
            isolado_novo_id = uuid.uuid4()
            dispensado = bool(isolado["sem_antibiograma_padronizado"])
            bind.execute(
                sa.text(
                    "INSERT INTO exame_isolados (id, tenant_id, exame_id, microrganismo_id, "
                    "mecanismo_resistencia, nao_realizado_tecnico, motivo_dispensa_tsa) "
                    "VALUES (:id, :tenant_id, :exame_id, :microrganismo_id, 'NENHUM', "
                    ":dispensado, :motivo)"
                ),
                {
                    "id": isolado_novo_id,
                    "tenant_id": tenant_id,
                    "exame_id": exame_id,
                    "microrganismo_id": isolado["microrganismo_id"],
                    "dispensado": dispensado,
                    "motivo": (
                        "[migrado] sem antibiograma padronizado (BrCAST)."
                        if dispensado
                        else None
                    ),
                },
            )

            antibiograma = bind.execute(
                sa.text(
                    "SELECT id FROM antibiogramas WHERE cultura_microrganismo_id = :cmid"
                ),
                {"cmid": isolado["id"]},
            ).first()
            if not antibiograma:
                continue

            resultados = bind.execute(
                sa.text(
                    "SELECT antimicrobiano_id, resultado FROM antibiograma_resultados "
                    "WHERE antibiograma_id = :aid"
                ),
                {"aid": antibiograma[0]},
            ).mappings().all()
            for resultado_ab in resultados:
                bind.execute(
                    sa.text(
                        "INSERT INTO exame_antibiogramas (id, tenant_id, isolado_id, "
                        "antimicrobiano_id, resultado) VALUES (:id, :tenant_id, :isolado_id, "
                        ":antimicrobiano_id, :resultado)"
                    ),
                    {
                        "id": uuid.uuid4(),
                        "tenant_id": tenant_id,
                        "isolado_id": isolado_novo_id,
                        "antimicrobiano_id": resultado_ab["antimicrobiano_id"],
                        "resultado": resultado_ab["resultado"],
                    },
                )


def downgrade() -> None:
    """
    Downgrade estrutural (não reconstrói os dados migrados de volta em
    Solicitação/Cultura/Antibiograma - essa reshape é considerada
    irreversível na prática, mesmo padrão de outras migrations grandes
    de reshape de dados). Restaura o schema anterior para permitir voltar
    a rodar a versão de código anterior da aplicação.
    """
    bind = op.get_bind()

    for tabela in TABELAS_COM_RLS:
        op.execute(f"DROP POLICY IF EXISTS {tabela}_super_admin ON {tabela}")
        op.execute(f"DROP POLICY IF EXISTS {tabela}_tenant_isolation ON {tabela}")
        op.execute(f"ALTER TABLE {tabela} NO FORCE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY")

    op.drop_table("exame_antibiogramas")
    op.drop_table("exame_isolados")
    op.drop_table("exames")
    postgresql.ENUM(name="mecanismo_resistencia_enum").drop(bind, checkfirst=True)
    postgresql.ENUM(name="status_exame_enum").drop(bind, checkfirst=True)

    op.drop_table("tipos_cultura")

    op.drop_constraint("ck_usuarios_super_admin_sem_tenant", "usuarios", type_="check")
    op.drop_index("uq_usuarios_super_admin_login", table_name="usuarios")
    op.drop_index("ix_usuarios_login", table_name="usuarios")
    op.drop_constraint("uq_usuarios_tenant_login", "usuarios", type_="unique")
    op.create_unique_constraint("uq_usuarios_login", "usuarios", ["login"])
    op.create_index("ix_usuarios_login", "usuarios", ["login"])
    # Não há suporte direto do Postgres para remover um valor de ENUM -
    # o label 'SUPER_ADMIN' fica órfão no tipo (inofensivo: nenhuma linha
    # o usa depois deste downgrade, já que o CHECK constraint acima
    # impedia qualquer usuário SUPER_ADMIN de existir sem tenant).

    op.drop_index("ix_logs_auditoria_tenant_id", table_name="logs_auditoria")
    op.drop_constraint("fk_logs_auditoria_tenant_id", "logs_auditoria", type_="foreignkey")
    op.drop_column("logs_auditoria", "tenant_id")

    op.drop_index("ix_usuarios_tenant_id", table_name="usuarios")
    op.drop_constraint("fk_usuarios_tenant_id", "usuarios", type_="foreignkey")
    op.drop_column("usuarios", "tenant_id")

    for tabela, uq_nova, uq_antiga, coluna in (
        ("antimicrobianos", "uq_antimicrobianos_tenant_nome", "uq_antimicrobianos_nome", "nome"),
        ("microrganismos", "uq_microrganismos_tenant_nome", "uq_microrganismos_nome", "nome"),
        ("materiais", "uq_materiais_tenant_nome", "uq_materiais_nome", "nome"),
        ("setores", "uq_setores_tenant_nome", "uq_setores_nome", "nome"),
        ("pacientes", "uq_pacientes_tenant_prontuario", "uq_pacientes_prontuario", "prontuario"),
    ):
        op.drop_index(f"ix_{tabela}_{coluna}", table_name=tabela)
        op.drop_constraint(uq_nova, tabela, type_="unique")
        op.create_unique_constraint(uq_antiga, tabela, [coluna])
        op.create_index(f"ix_{tabela}_{coluna}", tabela, [coluna])

        op.drop_index(f"ix_{tabela}_tenant_id", table_name=tabela)
        op.drop_constraint(f"fk_{tabela}_tenant_id", tabela, type_="foreignkey")
        op.drop_column(tabela, "tenant_id")

    op.drop_table("tenants")

    # Recria a estrutura antiga (vazia) para a versão anterior do código
    # voltar a funcionar.
    prioridade_enum = postgresql.ENUM("ROTINA", "URGENTE", "EMERGENCIA", name="prioridade_enum")
    status_solicitacao_enum = postgresql.ENUM(
        "AGUARDANDO_COLETA", "COLETADO", "EM_ANALISE", "LIBERADO", "CANCELADO",
        name="status_solicitacao_enum",
    )
    resultado_cultura_enum = postgresql.ENUM(
        "EM_ANALISE", "POSITIVA", "NEGATIVA", "CONTAMINADA", name="resultado_cultura_enum"
    )
    grupo_cultura_enum = postgresql.ENUM(
        "HEMOCULTURA", "CULTURA_GERAL", "VIGILANCIA", "BK", "FUNGOS", name="grupo_cultura_enum"
    )
    prioridade_enum.create(bind, checkfirst=True)
    status_solicitacao_enum.create(bind, checkfirst=True)
    resultado_cultura_enum.create(bind, checkfirst=True)
    grupo_cultura_enum.create(bind, checkfirst=True)
    for e in (prioridade_enum, status_solicitacao_enum, resultado_cultura_enum, grupo_cultura_enum):
        e.create_type = False

    op.create_table(
        "solicitacoes",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("paciente_id", UUID_COL, sa.ForeignKey("pacientes.id"), nullable=False),
        sa.Column("material", sa.String(length=100), nullable=False),
        sa.Column("origem", sa.String(length=100), nullable=True),
        sa.Column("prioridade", prioridade_enum, nullable=False, server_default="ROTINA"),
        sa.Column("status", status_solicitacao_enum, nullable=False, server_default="AGUARDANDO_COLETA"),
        sa.Column("data_solicitacao", sa.Date(), nullable=False),
        sa.Column("data_coleta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observacoes", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_solicitacoes_paciente_id", "solicitacoes", ["paciente_id"])

    op.create_table(
        "culturas",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("solicitacao_id", UUID_COL, sa.ForeignKey("solicitacoes.id"), nullable=False),
        sa.Column("grupo", grupo_cultura_enum, nullable=False, server_default="CULTURA_GERAL"),
        sa.Column("resultado", resultado_cultura_enum, nullable=False, server_default="EM_ANALISE"),
        sa.Column("liberado_tecnicamente", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("data_liberacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("previsao_liberacao", sa.Date(), nullable=True),
        sa.Column("observacoes", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_culturas_solicitacao_id", "culturas", ["solicitacao_id"])
    op.create_index("ix_culturas_grupo", "culturas", ["grupo"])

    op.create_table(
        "cultura_microrganismos",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("cultura_id", UUID_COL, sa.ForeignKey("culturas.id"), nullable=False),
        sa.Column("microrganismo_id", UUID_COL, sa.ForeignKey("microrganismos.id"), nullable=False),
        sa.Column("sem_antibiograma_padronizado", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_cultura_microrganismos_cultura_id", "cultura_microrganismos", ["cultura_id"])
    op.create_index(
        "ix_cultura_microrganismos_microrganismo_id", "cultura_microrganismos", ["microrganismo_id"]
    )

    op.create_table(
        "antibiogramas",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column(
            "cultura_microrganismo_id",
            UUID_COL,
            sa.ForeignKey("cultura_microrganismos.id"),
            nullable=False,
        ),
        sa.Column("data_liberacao", sa.DateTime(timezone=True), nullable=True),
        sa.Column("observacoes", sa.String(length=1000), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_antibiogramas_cultura_microrganismo_id", "antibiogramas", ["cultura_microrganismo_id"]
    )

    # `resultado_sir_enum` nunca foi dropado (upgrade() o reaproveita tal e
    # qual em `exame_antibiogramas` - ver comentário lá em cima) - aqui
    # também só referenciamos o tipo já existente, sem tentar recriá-lo
    # (create_type=False), senão o Postgres reclama de tipo duplicado.
    resultado_sir_enum_downgrade = postgresql.ENUM(
        "SENSIVEL", "INTERMEDIARIO", "RESISTENTE", name="resultado_sir_enum"
    )
    resultado_sir_enum_downgrade.create_type = False

    op.create_table(
        "antibiograma_resultados",
        sa.Column("id", UUID_COL, primary_key=True, default=uuid.uuid4),
        sa.Column("antibiograma_id", UUID_COL, sa.ForeignKey("antibiogramas.id"), nullable=False),
        sa.Column("antimicrobiano_id", UUID_COL, sa.ForeignKey("antimicrobianos.id"), nullable=False),
        sa.Column("resultado", resultado_sir_enum_downgrade, nullable=False),
    )
    op.create_index(
        "ix_antibiograma_resultados_antibiograma_id", "antibiograma_resultados", ["antibiograma_id"]
    )
    op.create_index(
        "ix_antibiograma_resultados_antimicrobiano_id",
        "antibiograma_resultados",
        ["antimicrobiano_id"],
    )
