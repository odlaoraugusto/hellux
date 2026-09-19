"""
Dependências de autenticação/autorização usadas pelos routers.

- get_current_user: extrai e valida o JWT do header Authorization,
  devolvendo o Usuario correspondente.
- require_perfil: fábrica de dependência para restringir um endpoint a
  um conjunto de perfis (ex.: apenas ADMIN pode gerenciar usuários).
"""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decodificar_access_token
from app.core.tenant_context import set_tenant_context
from app.db.session import get_db
from app.models.tenant import Tenant
from app.models.usuario import PerfilUsuarioEnum, Usuario
from app.services.tenant_service import TenantService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

CREDENCIAIS_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciais inválidas ou sessão expirada.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Usuario:
    if not token:
        raise CREDENCIAIS_INVALIDAS

    payload = decodificar_access_token(token)
    if not payload or "sub" not in payload:
        raise CREDENCIAIS_INVALIDAS

    try:
        usuario_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise CREDENCIAIS_INVALIDAS

    # SUPER_ADMIN não pertence a tenant nenhum - a claim `tenant_id` vem
    # None/ausente nesse caso (ver app/core/security.py::criar_access_token).
    perfil_claim = payload.get("perfil")
    eh_super_admin_claim = perfil_claim == PerfilUsuarioEnum.SUPER_ADMIN.value
    tenant_id_raw = payload.get("tenant_id")

    tenant_id: uuid.UUID | None = None
    if tenant_id_raw:
        try:
            tenant_id = uuid.UUID(tenant_id_raw)
        except ValueError:
            raise CREDENCIAIS_INVALIDAS
    elif not eh_super_admin_claim:
        # Todo perfil que não é SUPER_ADMIN precisa ter tenant_id na claim.
        raise CREDENCIAIS_INVALIDAS

    # Precisa vir ANTES do db.get() - a tabela `usuarios` também tem Row
    # Level Security (Fase 1), então sem o contexto de tenant (ou o modo
    # SUPER_ADMIN) já definido a própria busca do usuário autenticado
    # retornaria vazia.
    set_tenant_context(db, tenant_id, is_super_admin=eh_super_admin_claim)

    usuario = db.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise CREDENCIAIS_INVALIDAS

    if eh_super_admin_claim:
        if usuario.perfil != PerfilUsuarioEnum.SUPER_ADMIN or usuario.tenant_id is not None:
            raise CREDENCIAIS_INVALIDAS
    elif usuario.tenant_id != tenant_id:
        raise CREDENCIAIS_INVALIDAS

    return usuario


def get_current_tenant(
    usuario: Usuario = Depends(get_current_user), db: Session = Depends(get_db)
) -> Tenant | None:
    """
    Devolve o Tenant completo do usuário autenticado (usado pelos
    relatórios white-label, que precisam de mais do que o `tenant_id`
    cru - nome fantasia, logo etc.).

    Um SUPER_ADMIN não pertence a tenant nenhum (`usuario.tenant_id` é
    `None`) - devolve `None` em vez de levantar erro; não é foco desta
    fase consertar o fluxo de relatório do SUPER_ADMIN, os pontos que
    dependem disso tratam `tenant is None` com um fallback genérico.
    """
    if usuario.tenant_id is None:
        return None

    return TenantService(db).obter(usuario.tenant_id)


def require_perfil(*perfis_permitidos: PerfilUsuarioEnum):
    """Dependência que restringe o acesso a um endpoint por perfil de usuário."""

    def verificador(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfis_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Você não tem permissão para acessar este recurso.",
            )
        return usuario

    return verificador
