"""
Teste de isolamento de Row Level Security (Fase 1 - fundação multi-tenant).

RLS é uma feature exclusiva do Postgres - não existe no SQLite usado
pela suíte padrão (ver tests/conftest.py), então este teste só roda
contra um Postgres real e descartável, apontado pela variável de
ambiente `HELLUX_TEST_POSTGRES_URL`. Sem essa variável definida, os
testes deste arquivo são pulados (skip), não falham.

Cobre exatamente o que o plano da Fase 1 pede: cria 2 tenants, um dado
em cada, e confirma que uma sessão com `SET LOCAL` do tenant A não
enxerga o dado do tenant B (nem o contrário) - e que o contexto
`app.is_super_admin` enxerga os dois.

Como rodar localmente (contra um Postgres descartável, NUNCA um banco
com dados reais):

    HELLUX_TEST_POSTGRES_URL="postgresql+psycopg2://user:pass@localhost:5432/hellux_test" \
        python -m pytest tests/test_rls_isolamento.py -q
"""
import os
import uuid

import pytest
from sqlalchemy import create_engine, text

POSTGRES_TEST_URL = os.environ.get("HELLUX_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason=(
        "Requer HELLUX_TEST_POSTGRES_URL (Postgres real e descartável) - RLS "
        "não existe no SQLite usado pela suíte padrão. Ver docstring do módulo."
    ),
)


@pytest.fixture()
def postgres_engine():
    from alembic import command
    from alembic.config import Config

    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    cfg = Config(os.path.join(backend_dir, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(backend_dir, "alembic"))
    cfg.set_main_option("sqlalchemy.url", POSTGRES_TEST_URL)

    command.upgrade(cfg, "head")
    engine = create_engine(POSTGRES_TEST_URL, future=True)
    try:
        yield engine
    finally:
        engine.dispose()
        command.downgrade(cfg, "base")


def _set_local(conn, tenant_id=None, is_super_admin=False):
    """
    Espelha o listener `after_begin` de app/db/session.py: sempre reseta os
    DOIS GUCs explicitamente, nunca só quando aplicável - depois de um SET
    LOCAL anterior na mesma conexão (mesmo em transação já encerrada), o
    Postgres não volta pra NULL, volta pra string vazia. Sem esse reset
    explícito aqui, este teste ficaria "sortudo" com a ordem das asserções
    em vez de testar de verdade o comportamento de produção.
    """
    if tenant_id:
        conn.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))
    else:
        conn.execute(text("SET LOCAL app.current_tenant_id = ''"))
    conn.execute(text(f"SET LOCAL app.is_super_admin = '{'true' if is_super_admin else 'false'}'"))


def test_rls_isola_pacientes_entre_tenants(postgres_engine):
    engine = postgres_engine
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()

    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO tenants (id, nome_fantasia) VALUES (:id, 'Tenant A')"),
            {"id": tenant_a},
        )
        conn.execute(
            text("INSERT INTO tenants (id, nome_fantasia) VALUES (:id, 'Tenant B')"),
            {"id": tenant_b},
        )

    paciente_a, paciente_b = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:
        _set_local(conn, tenant_id=tenant_a)
        conn.execute(
            text(
                "INSERT INTO pacientes (id, tenant_id, nome, prontuario) "
                "VALUES (:id, :tenant_id, 'Paciente A', 'pa-1')"
            ),
            {"id": paciente_a, "tenant_id": tenant_a},
        )
    with engine.begin() as conn:
        _set_local(conn, tenant_id=tenant_b)
        conn.execute(
            text(
                "INSERT INTO pacientes (id, tenant_id, nome, prontuario) "
                "VALUES (:id, :tenant_id, 'Paciente B', 'pb-1')"
            ),
            {"id": paciente_b, "tenant_id": tenant_b},
        )

    # Sessão do tenant A não enxerga o paciente do tenant B - nem via
    # SELECT direto, nem contando linhas.
    with engine.begin() as conn:
        _set_local(conn, tenant_id=tenant_a)
        ids = {row[0] for row in conn.execute(text("SELECT id FROM pacientes")).all()}
    assert ids == {paciente_a}

    # E vice-versa.
    with engine.begin() as conn:
        _set_local(conn, tenant_id=tenant_b)
        ids = {row[0] for row in conn.execute(text("SELECT id FROM pacientes")).all()}
    assert ids == {paciente_b}

    # SUPER_ADMIN (app.is_super_admin='true') enxerga os dois tenants.
    with engine.begin() as conn:
        _set_local(conn, is_super_admin=True)
        ids = {row[0] for row in conn.execute(text("SELECT id FROM pacientes")).all()}
    assert ids == {paciente_a, paciente_b}

    # Sem contexto nenhum definido, RLS bloqueia tudo (fail-closed).
    with engine.begin() as conn:
        resultado = conn.execute(text("SELECT id FROM pacientes")).all()
    assert resultado == []


def test_rls_bloqueia_insercao_cruzada_entre_tenants(postgres_engine):
    engine = postgres_engine
    tenant_a, tenant_b = uuid.uuid4(), uuid.uuid4()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO tenants (id, nome_fantasia) VALUES (:id, 'Tenant A2')"),
            {"id": tenant_a},
        )
        conn.execute(
            text("INSERT INTO tenants (id, nome_fantasia) VALUES (:id, 'Tenant B2')"),
            {"id": tenant_b},
        )

    # Contexto de RLS setado pro tenant A, tentando inserir uma linha
    # marcada como sendo do tenant B - a policy (WITH CHECK implícito da
    # USING) tem que rejeitar.
    with pytest.raises(Exception):
        with engine.begin() as conn:
            _set_local(conn, tenant_id=tenant_a)
            conn.execute(
                text(
                    "INSERT INTO pacientes (id, tenant_id, nome, prontuario) "
                    "VALUES (:id, :tenant_id, 'Invasor', 'inv-1')"
                ),
                {"id": uuid.uuid4(), "tenant_id": tenant_b},
            )
