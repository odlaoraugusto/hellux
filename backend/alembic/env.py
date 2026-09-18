"""
Configuração do ambiente Alembic.

Lê a DATABASE_URL das configurações da aplicação (não do alembic.ini),
para que o mesmo .env sirva tanto a aplicação quanto as migrações.
"""
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.db.session import Base
from app.models import *  # noqa: F401,F403  (garante que todos os models sejam registrados)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = get_settings()
# Só cai pra DATABASE_URL do .env se quem chamou (CLI normal via
# alembic.ini, que tem "sqlalchemy.url =" vazio de propósito) não tiver
# passado uma URL explícita - é o que permite testes automatizados
# (ver tests/test_rls_isolamento.py) apontar pra um Postgres descartável
# via `Config.set_main_option("sqlalchemy.url", ...)` sem risco de cair
# no banco real por engano. NUNCA sobrescrever incondicionalmente aqui de
# novo - foi exatamente esse comportamento que já aplicou uma migration
# no banco de demonstração ao vivo por acidente numa sessão anterior.
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
