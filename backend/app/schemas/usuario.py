"""
Schemas de validação de entrada/saída do módulo Usuários.
"""
import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.usuario import PerfilUsuarioEnum

LOGIN_PATTERN = re.compile(r"^[a-zA-Z0-9_.-]+$")


class UsuarioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    login: str = Field(..., min_length=3, max_length=50)
    senha: str = Field(..., min_length=8, max_length=100)
    perfil: PerfilUsuarioEnum = PerfilUsuarioEnum.VISUALIZADOR

    @field_validator("login")
    @classmethod
    def _login_sem_espacos_ou_simbolos(cls, v: str) -> str:
        if not LOGIN_PATTERN.match(v):
            raise ValueError(
                "Login só pode ter letras, números, ponto, hífen e underscore (sem espaços)."
            )
        return v


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=200)
    perfil: PerfilUsuarioEnum | None = None
    senha: str | None = Field(default=None, min_length=8, max_length=100)


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    login: str
    perfil: PerfilUsuarioEnum
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UsuarioListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[UsuarioOut]
