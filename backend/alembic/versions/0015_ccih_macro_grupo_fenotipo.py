"""adiciona Setor.macro_grupo e Microrganismo.grupo_fenotipico (Matriz CCIH)

Revision ID: 0015_ccih_macro_grupo_fenotipo
Revises: 0014_multi_tenant_exame
Create Date: 2026-09-18

Fase 1.5 do Hellux (Matriz de Sensibilidade CCIH):

1. `setores.macro_grupo` (string opcional, catálogo livre por tenant -
   mesma filosofia do catálogo `tipos_cultura`, não enum fixo). Nullable
   de propósito, sem backfill - setor sem `macro_grupo` cai num balde
   "Não classificado" na matriz (ver `ccih_repository.py`).
2. `microrganismos.grupo_fenotipico` (enum fechado: CONS, S_AUREUS,
   BGN_F, BGN_NF, LEVEDURAS, OUTROS_GRAM_POSITIVOS, OUTROS). Adiciona a
   coluna com `server_default='OUTROS'` e então faz o UPDATE de
   classificação das ~31 espécies já seedadas em
   `0012_add_taxonomia_micro.py`, por nome - `gram`/`tipo`/`morfologia`/
   `fermentador` não bastam pra distinguir S. aureus de um CoNS (mesmos
   valores nesses 4 campos para as duas espécies), então essa
   classificação é dado de conhecimento clínico validado pelo usuário do
   sistema, não algo derivável. Linhas fora desta lista (cadastradas
   depois, por qualquer tenant) ficam em `OUTROS` via o
   `server_default` até serem editadas manualmente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
# OBS: mantenha o revision id com no máximo 32 caracteres (ver comentário
# equivalente em 0012_add_taxonomia_micro.py).
revision: str = "0015_ccih_macro_grupo_fenotipo"
down_revision: Union[str, None] = "0014_multi_tenant_exame"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

GRUPO_FENOTIPICO_ENUM = sa.Enum(
    "CONS",
    "S_AUREUS",
    "BGN_F",
    "BGN_NF",
    "LEVEDURAS",
    "OUTROS_GRAM_POSITIVOS",
    "OUTROS",
    name="grupo_fenotipico_enum",
)

# nome (unique em `microrganismos`) -> grupo_fenotipico. Classificação
# clínica validada pelo usuário do sistema - ver docstring do módulo.
# Cobre as 31 espécies seedadas em 0012_add_taxonomia_micro.py; nenhuma
# fica sem classificação explícita aqui (as que "sobrariam" pro
# server_default OUTROS - Dietzia timorensis e Haemophilus influenzae -
# estão listadas de propósito, não por omissão).
CLASSIFICACAO = {
    # S. aureus x CoNS - a distinção que motivou este campo (ver docstring).
    "Staphylococcus aureus": "S_AUREUS",
    "Staphylococcus haemolyticus": "CONS",
    "Staphylococcus epidermidis": "CONS",
    "Staphylococcus capitis": "CONS",
    "Staphylococcus hominis": "CONS",
    "Staphylococcus saprophyticus": "CONS",
    # Demais Gram-positivos.
    "Micrococcus luteus": "OUTROS_GRAM_POSITIVOS",
    "Streptococcus agalactiae": "OUTROS_GRAM_POSITIVOS",
    "Streptococcus pyogenes": "OUTROS_GRAM_POSITIVOS",
    "Streptococcus pneumoniae": "OUTROS_GRAM_POSITIVOS",
    "Streptococcus viridans (grupo)": "OUTROS_GRAM_POSITIVOS",
    "Enterococcus faecalis": "OUTROS_GRAM_POSITIVOS",
    "Enterococcus faecium": "OUTROS_GRAM_POSITIVOS",
    # Gram-positivo atípico, fora dos grupos acima -> catch-all.
    "Dietzia timorensis": "OUTROS",
    # Bacilos Gram-negativos fermentadores (Enterobacterales).
    "Escherichia coli": "BGN_F",
    "Klebsiella pneumoniae": "BGN_F",
    "Klebsiella oxytoca": "BGN_F",
    "Proteus mirabilis": "BGN_F",
    "Proteus vulgaris": "BGN_F",
    "Enterobacter hormaechei ssp hormaechei": "BGN_F",
    "Morganella morganii": "BGN_F",
    "Serratia marcescens": "BGN_F",
    "Citrobacter freundii": "BGN_F",
    # Bacilos Gram-negativos não-fermentadores.
    "Pseudomonas aeruginosa": "BGN_NF",
    "Pseudomonas stutzeri": "BGN_NF",
    "Acinetobacter baumannii": "BGN_NF",
    "Stenotrophomonas maltophilia": "BGN_NF",
    # Cocobacilo Gram-negativo fastidioso, fora dos dois grupos de bacilo
    # acima -> catch-all.
    "Haemophilus influenzae": "OUTROS",
    # Leveduras.
    "Candida albicans": "LEVEDURAS",
    "Candida duobushaemulonis": "LEVEDURAS",
    "Rhodotorula mucilaginosa": "LEVEDURAS",
}

UPDATE_SQL = sa.text(
    "UPDATE microrganismos SET grupo_fenotipico = :grupo WHERE nome = :nome"
)


def upgrade() -> None:
    op.add_column(
        "setores",
        sa.Column("macro_grupo", sa.String(length=100), nullable=True),
    )
    op.create_index("ix_setores_macro_grupo", "setores", ["macro_grupo"])

    GRUPO_FENOTIPICO_ENUM.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "microrganismos",
        sa.Column(
            "grupo_fenotipico",
            GRUPO_FENOTIPICO_ENUM,
            nullable=False,
            server_default="OUTROS",
        ),
    )

    bind = op.get_bind()
    for nome, grupo in CLASSIFICACAO.items():
        bind.execute(UPDATE_SQL, {"nome": nome, "grupo": grupo})


def downgrade() -> None:
    op.drop_column("microrganismos", "grupo_fenotipico")
    GRUPO_FENOTIPICO_ENUM.drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_setores_macro_grupo", table_name="setores")
    op.drop_column("setores", "macro_grupo")
