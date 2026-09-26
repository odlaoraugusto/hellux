"""painel de acompanhamento: Exame.numero_solicitacao + status AMOSTRA_INADEQUADA

Revision ID: 0017_painel_acompanhamento
Revises: 0016_remove_status_internacao
Create Date: 2026-09-26

O novo Painel de Acompanhamento das culturas mostra o nº da solicitação
do sistema do hospital (campo livre, opcional) e separa as amostras
rejeitadas pelo laboratório num status final próprio, em vez de
misturá-las com "Contaminação".
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0017_painel_acompanhamento"
down_revision: Union[str, None] = "0016_remove_status_internacao"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exames", sa.Column("numero_solicitacao", sa.String(length=50), nullable=True)
    )
    # `ALTER TYPE ... ADD VALUE` não pode ser usado na mesma transação em
    # que o valor novo é gravado - roda fora do bloco transacional.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TYPE status_exame_enum ADD VALUE IF NOT EXISTS 'AMOSTRA_INADEQUADA'"
        )


def downgrade() -> None:
    # Postgres não remove valor de enum - recria o tipo sem ele.
    op.execute(
        "UPDATE exames SET status = 'CONTAMINACAO' WHERE status = 'AMOSTRA_INADEQUADA'"
    )
    op.execute("ALTER TABLE exames ALTER COLUMN status DROP DEFAULT")
    op.execute("ALTER TYPE status_exame_enum RENAME TO status_exame_enum_old")
    op.execute(
        "CREATE TYPE status_exame_enum AS ENUM ('AGUARDANDO_TRIAGEM', 'NEGATIVO_PARCIAL', "
        "'POSITIVO_PARCIAL', 'NEGATIVO', 'POSITIVO', 'CONTAMINACAO')"
    )
    op.execute(
        "ALTER TABLE exames ALTER COLUMN status TYPE status_exame_enum "
        "USING status::text::status_exame_enum"
    )
    op.execute("ALTER TABLE exames ALTER COLUMN status SET DEFAULT 'AGUARDANDO_TRIAGEM'")
    op.execute("DROP TYPE status_exame_enum_old")
    op.drop_column("exames", "numero_solicitacao")
