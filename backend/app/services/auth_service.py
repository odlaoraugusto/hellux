"""
Service do módulo de Autenticação (Sprint 12).

Fase 1 (fundação multi-tenant): o login precede qualquer JWT, então a
sessão de banco ainda não tem nenhum tenant no contexto (ver
app/core/tenant_context.py). Como a tabela `usuarios` tem Row Level
Security FORÇADA (ver migration da Fase 1), uma busca por login sem
contexto de tenant não enxergaria nenhuma linha - por isso o login:

1. Primeiro tenta como SUPER_ADMIN (contexto `is_super_admin=True`, que
   enxerga todas as linhas via a policy permissiva extra - ver migration)
   restringindo a busca a `tenant_id IS NULL` na própria query (não dá
   pra confiar só no contexto de RLS aqui, porque login não é único
   globalmente - só por tenant).
2. Se não achar, itera os tenants ativos (hoje, tipicamente só um)
   tentando localizar o login sob o contexto de RLS de cada um, até
   achar uma senha que bata.

Isso funciona bem na escala atual (poucos tenants). Quando o "componente
de login novo" (fase futura) passar a pedir o tenant/subdomínio antes da
senha, esse loop deixa de ser necessário - a request já chega sabendo o
tenant.
"""
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import criar_access_token, verificar_senha
from app.core.tenant_context import set_tenant_context
from app.models.usuario import PerfilUsuarioEnum
from app.repositories.tenant_repository import TenantRepository
from app.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuarioRepository(db)
        self.tenant_repository = TenantRepository(db)

    def autenticar(self, login: str, senha: str) -> str:
        credenciais_invalidas = AuthenticationError("Usuário ou senha inválidos.")
        login_normalizado = login.lower()

        set_tenant_context(self.db, None, is_super_admin=True)
        super_admin = self.repository.get_super_admin_by_login(login_normalizado)
        if (
            super_admin
            and super_admin.is_active
            and super_admin.perfil == PerfilUsuarioEnum.SUPER_ADMIN
            and verificar_senha(senha, super_admin.senha_hash)
        ):
            return criar_access_token(
                super_admin.id, super_admin.perfil.value, super_admin.login, None
            )

        for tenant in self.tenant_repository.listar_ativos():
            set_tenant_context(self.db, tenant.id)
            usuario = self.repository.get_by_login(login_normalizado)
            if not usuario or not usuario.is_active or usuario.tenant_id != tenant.id:
                continue
            if not verificar_senha(senha, usuario.senha_hash):
                continue
            return criar_access_token(
                usuario.id, usuario.perfil.value, usuario.login, usuario.tenant_id
            )

        raise credenciais_invalidas
