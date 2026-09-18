"""
Service do módulo de Autenticação (Sprint 12).
"""
from sqlalchemy.orm import Session

from app.core.exceptions import AuthenticationError
from app.core.security import criar_access_token, verificar_senha
from app.repositories.usuario_repository import UsuarioRepository


class AuthService:
    def __init__(self, db: Session):
        self.repository = UsuarioRepository(db)

    def autenticar(self, login: str, senha: str) -> str:
        usuario = self.repository.get_by_login(login.lower())

        credenciais_invalidas = AuthenticationError("Usuário ou senha inválidos.")

        if not usuario or not usuario.is_active:
            raise credenciais_invalidas

        if not verificar_senha(senha, usuario.senha_hash):
            raise credenciais_invalidas

        return criar_access_token(usuario.id, usuario.perfil.value, usuario.login)
