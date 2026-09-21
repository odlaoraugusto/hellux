"""remove Paciente.status_internacao

Revision ID: 0016_remove_status_internacao
Revises: 0015_ccih_macro_grupo_fenotipo
Create Date: 2026-09-21

O campo nunca foi usado em nenhuma regra de negócio (nem CCIH, nem
Exame) - era só um dado cadastral solto sem consequência no resto do
sistema. Usuário pediu pra remover do cadastro de paciente.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0016_remove_status_internacao"
down_revision: Union[str, None] = "0015_ccih_macro_grupo_fenotipo"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STATUS_INTERNACAO_ENUM = sa.Enum(
    "INTERNADO", "AMBULATORIAL", "ALTA", "OBITO", name="status_internacao_enum"
)


def upgrade() -> None:
    op.drop_column("pacientes", "status_internacao")
    STATUS_INTERNACAO_ENUM.drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    STATUS_INTERNACAO_ENUM.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "pacientes",
        sa.Column(
            "status_internacao",
            STATUS_INTERNACAO_ENUM,
            nullable=False,
            server_default="AMBULATORIAL",
        ),
    )
