"""
Schemas do módulo de Autenticação (Sprint 12).
"""
from pydantic import BaseModel


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    login: str
    senha: str
