"""
Utilitários de segurança do Hellux.

Centraliza hashing de senha (bcrypt via passlib) e criação/validação de
tokens JWT (via python-jose). Nenhuma senha em texto puro é armazenada
ou logada em nenhum ponto do sistema.
"""
import uuid
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

settings = get_settings()

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


def hash_senha(senha_texto_puro: str) -> str:
    return _pwd_context.hash(senha_texto_puro)


def verificar_senha(senha_texto_puro: str, senha_hash: str) -> bool:
    return _pwd_context.verify(senha_texto_puro, senha_hash)


def criar_access_token(usuario_id: uuid.UUID, perfil: str, login: str) -> str:
    expira_em = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(usuario_id),
        "perfil": perfil,
        "login": login,
        "exp": expira_em,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=JWT_ALGORITHM)


def decodificar_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except JWTError:
        return None
