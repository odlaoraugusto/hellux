"""renomeia email para login (usuarios e logs_auditoria)

Revision ID: 0013_rename_email_to_login
Revises: 0012_add_taxonomia_micro
Create Date: 2026-09-18

Rebrand MicroGest -> Hellux: login deixa de exigir formato de e-mail
(era validado como EmailStr no schema) e passa a aceitar um username
livre (letras, números, ponto, hífen, underscore). O valor já
cadastrado é preservado como está - só a coluna/constraints/índice
mudam de nome, nenhum dado é reescrito.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0013_rename_email_to_login"
down_revision: Union[str, None] = "0012_add_taxonomia_micro"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("usuarios", "email", new_column_name="login")
    op.alter_column(
        "usuarios",
        "login",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
    )
    op.execute("ALTER TABLE usuarios RENAME CONSTRAINT uq_usuarios_email TO uq_usuarios_login")
    op.execute("ALTER INDEX ix_usuarios_email RENAME TO ix_usuarios_login")

    op.alter_column("logs_auditoria", "usuario_email", new_column_name="usuario_login")
    op.alter_column(
        "logs_auditoria",
        "usuario_login",
        existing_type=sa.String(length=255),
        type_=sa.String(length=50),
    )


def downgrade() -> None:
    op.alter_column(
        "logs_auditoria",
        "usuario_login",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
    )
    op.alter_column("logs_auditoria", "usuario_login", new_column_name="usuario_email")

    op.execute("ALTER INDEX ix_usuarios_login RENAME TO ix_usuarios_email")
    op.execute("ALTER TABLE usuarios RENAME CONSTRAINT uq_usuarios_login TO uq_usuarios_email")
    op.alter_column(
        "usuarios",
        "login",
        existing_type=sa.String(length=50),
        type_=sa.String(length=255),
    )
    op.alter_column("usuarios", "login", new_column_name="email")
