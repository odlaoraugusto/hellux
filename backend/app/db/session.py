"""
Configuração de conexão com o PostgreSQL via SQLAlchemy.
"""
import uuid
from collections.abc import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, future=True
)


class Base(DeclarativeBase):
    """Classe base declarativa para todos os models do Hellux."""

    pass


TENANT_SESSION_INFO_KEY = "tenant_id"
SUPER_ADMIN_SESSION_INFO_KEY = "is_super_admin"


@event.listens_for(Session, "after_begin")
def _reaplicar_contexto_de_tenant(session: Session, transaction, connection) -> None:
    """
    Reaplica `SET LOCAL app.current_tenant_id`/`app.is_super_admin` toda
    vez que uma NOVA transação começa na sessão - não apenas uma vez por
    request.

    Ponto crítico da Fase 1 (fundação multi-tenant): `SET LOCAL` só vale
    para a transação atual, e `BaseRepository.create()`/`update()` chamam
    `db.commit()`, o que encerra a transação e apagaria o `SET LOCAL`
    antes da próxima query da mesma request (ex.: `ExameService.criar`,
    que grava paciente e exame em `commit()`s separados). Um listener em
    `after_begin` garante que TODA nova transação da sessão reaplica o
    contexto, lendo o tenant atual de `session.info["tenant_id"]`
    (setado por `app/core/deps.py::get_current_user` e por
    `app/core/tenant_context.py::set_tenant_context`).

    `app.is_super_admin` é a segunda metade do contexto: um usuário
    SUPER_ADMIN não pertence a tenant nenhum (`tenant_id` fica None), e
    cada tabela tenant-scoped tem uma SEGUNDA policy PERMISSIVE (RLS
    combina policies permissivas com OR) que libera acesso quando esse
    GUC é 'true' - ver migration da Fase 1.

    Só faz sentido contra Postgres (é lá que existe RLS/`current_setting`)
    - em SQLite (usado pela suíte de testes, ver tests/conftest.py) esses
    comandos nem existem, então o listener não faz nada.
    """
    if connection.dialect.name != "postgresql":
        return

    # Sempre reafirma os DOIS GUCs explicitamente nesta transação - nunca só
    # quando aplicável. Depois que um GUC customizado (`app.*`) é setado uma
    # vez numa conexão (mesmo via SET LOCAL, mesmo em uma transação que já
    # terminou), o Postgres não volta pra NULL - volta pra STRING VAZIA
    # (confirmado na prática). Com pooling de conexão, uma conexão que já
    # serviu a request de um tenant pode ser reaproveitada por uma request
    # de outro tenant (ou de um SUPER_ADMIN) - sem resetar explicitamente
    # aqui, o valor "residual" da request anterior vazaria pra dentro desta
    # transação sempre que esta request não precisasse setar aquele GUC
    # específico. As policies de RLS comparam como texto (ver migration da
    # Fase 1), então '' nunca dá erro de cast - só nunca deve bater com um
    # tenant_id de verdade nem com 'true'.
    tenant_id = session.info.get(TENANT_SESSION_INFO_KEY)
    if tenant_id:
        # Não dá pra usar bind parameter aqui - o comando `SET` do Postgres
        # não aceita parâmetro na posição do valor (erro de sintaxe). Em vez
        # disso, validamos que o valor é mesmo um UUID (levanta ValueError
        # se não for) e interpolamos o literal já validado - não há como
        # injetar SQL por aqui, já que `uuid.UUID(...)` só aceita a forma
        # canônica de um UUID.
        tenant_uuid = uuid.UUID(str(tenant_id))
        connection.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_uuid}'"))
    else:
        connection.execute(text("SET LOCAL app.current_tenant_id = ''"))

    if session.info.get(SUPER_ADMIN_SESSION_INFO_KEY):
        connection.execute(text("SET LOCAL app.is_super_admin = 'true'"))
    else:
        connection.execute(text("SET LOCAL app.is_super_admin = 'false'"))


def get_db() -> Generator:
    """Dependency do FastAPI: fornece uma sessão de banco por requisição."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
