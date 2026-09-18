"""
Contexto de tenant da sessão de banco (Fase 1 - fundação multi-tenant).

`session.info` é um dict simples que vive com a Session do SQLAlchemy -
usamos ele para carregar qual tenant (e se é um SUPER_ADMIN, que não tem
tenant nenhum) a request atual está operando. `app/db/session.py` tem um
listener `after_begin` que lê esses valores e reaplica `SET LOCAL
app.current_tenant_id`/`app.is_super_admin` a cada nova transação (ver
docstring lá) - a Row Level Security do Postgres faz o resto.

Este módulo concentra o "set" (usado só em poucos lugares: login,
resolução do usuário autenticado, bootstrap do primeiro usuário) e o
"get" (usado por todo Service que precisa saber de qual tenant é a linha
que está criando).
"""
import uuid

from sqlalchemy.orm import Session

from app.db.session import SUPER_ADMIN_SESSION_INFO_KEY, TENANT_SESSION_INFO_KEY


def set_tenant_context(
    db: Session, tenant_id: uuid.UUID | str | None, is_super_admin: bool = False
) -> None:
    """
    Define o tenant (e/ou o modo SUPER_ADMIN) da sessão atual e força a
    próxima query a abrir uma nova transação (fazendo o listener
    `after_begin` reaplicar o `SET LOCAL` já com o novo valor).

    `tenant_id=None` é o caso normal de um SUPER_ADMIN (não pertence a
    tenant nenhum) - só faz sentido combinado com `is_super_admin=True`.

    Só deve ser chamado em pontos que sabem que não há trabalho pendente
    não commitado na sessão (login, resolução do usuário autenticado no
    início da request, bootstrap do primeiro usuário/tenant) - um
    `rollback()` no meio de uma operação descartaria o que ainda não foi
    commitado.
    """
    db.info[TENANT_SESSION_INFO_KEY] = str(tenant_id) if tenant_id else None
    db.info[SUPER_ADMIN_SESSION_INFO_KEY] = is_super_admin
    db.rollback()


def get_current_tenant_id(db: Session) -> uuid.UUID:
    """
    Lê o tenant da sessão atual (setado por `set_tenant_context`).

    Levanta `RuntimeError` se nenhum tenant foi definido ainda (inclui o
    caso de um SUPER_ADMIN, que não tem tenant próprio - services que
    criam dado tenant-scoped não devem ser chamados nesse contexto sem
    um tenant explícito, ver `UsuarioService.criar`/`TenantService`).
    """
    valor = db.info.get(TENANT_SESSION_INFO_KEY)
    if not valor:
        raise RuntimeError(
            "Nenhum tenant definido no contexto da sessão atual - "
            "set_tenant_context() precisa ser chamado antes de qualquer "
            "operação tenant-scoped."
        )
    return uuid.UUID(valor)


def is_current_super_admin(db: Session) -> bool:
    return bool(db.info.get(SUPER_ADMIN_SESSION_INFO_KEY, False))
