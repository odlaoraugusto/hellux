"""
Repository do módulo Usuários.
"""
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.usuario import Usuario
from app.repositories.base import BaseRepository


class UsuarioRepository(BaseRepository[Usuario]):
    def __init__(self, db: Session):
        super().__init__(db, Usuario)

    def get_by_login(self, login: str) -> Usuario | None:
        # Comparação case-insensitive EXATA - de propósito não usa .ilike(),
        # que interpreta "%" e "_" como wildcard SQL. Como o login vem via
        # OAuth2PasswordRequestForm, um valor com "%"/"_" viraria wildcard e
        # poderia casar com uma conta diferente da que o usuário digitou.
        #
        # Não filtra por tenant explicitamente aqui - quem chama (AuthService)
        # já deixou a sessão no contexto do tenant sendo tentado (RLS filtra
        # em Postgres; ver app/services/auth_service.py). Em bancos sem RLS
        # (SQLite dos testes) isso devolve o primeiro usuário com esse login
        # em qualquer tenant.
        stmt = select(Usuario).where(func.lower(Usuario.login) == login.lower())
        return self.db.scalars(stmt).first()

    def search(
        self, tenant_id: uuid.UUID | None = None, skip: int = 0, limit: int = 20
    ) -> tuple[list[Usuario], int]:
        """
        `tenant_id=None` não filtra nada - pra perfis normais isso é
        irrelevante (RLS já limita ao próprio tenant); pra um SUPER_ADMIN,
        significa "ver usuários de todos os tenants".
        """
        stmt = select(Usuario).where(Usuario.is_active.is_(True))
        if tenant_id:
            stmt = stmt.where(Usuario.tenant_id == tenant_id)

        total = len(self.db.scalars(stmt).all())
        items = (
            self.db.scalars(stmt.offset(skip).limit(limit).order_by(Usuario.created_at.desc()))
            .all()
        )
        return list(items), total

    def get_super_admin_by_login(self, login: str) -> Usuario | None:
        """
        Mesma comparação exata (sem wildcard) de `get_by_login`, mas
        restrita explicitamente a `tenant_id IS NULL` - usado pelo login
        e pelo cadastro de SUPER_ADMIN, já que sob o contexto de RLS de
        SUPER_ADMIN uma busca sem esse filtro enxergaria usuários de
        QUALQUER tenant com o mesmo login (login só é único por tenant).
        """
        stmt = select(Usuario).where(
            func.lower(Usuario.login) == login.lower(), Usuario.tenant_id.is_(None)
        )
        return self.db.scalars(stmt).first()

    def existe_usuario_do_tenant(self, tenant_id: uuid.UUID) -> bool:
        """
        Checagem EXPLICITAMENTE filtrada por tenant_id na query (não só
        via RLS) - usada pelo gatekeeping do bootstrap de usuários
        (UsuarioService), que precisa funcionar corretamente também sob
        SQLite (testes), onde não existe Row Level Security nenhuma.
        """
        stmt = select(Usuario.id).where(Usuario.tenant_id == tenant_id).limit(1)
        return self.db.scalars(stmt).first() is not None
