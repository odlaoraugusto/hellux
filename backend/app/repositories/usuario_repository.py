"""
Repository do módulo Usuários.
"""
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
        stmt = select(Usuario).where(func.lower(Usuario.login) == login.lower())
        return self.db.scalars(stmt).first()

    def existe_algum_usuario(self) -> bool:
        stmt = select(Usuario.id).limit(1)
        return self.db.scalars(stmt).first() is not None
