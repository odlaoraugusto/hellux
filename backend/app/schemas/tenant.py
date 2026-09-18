"""
Schemas de validação de entrada/saída do módulo Tenants.

Restrito a SUPER_ADMIN (ver app/routers/tenant_router.py). O cadastro de
um tenant já cria, na mesma chamada, o primeiro usuário ADMIN dele -
elimina o passo manual de logar como o admin recém-criado só para criar
a si mesmo.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.usuario import UsuarioOut


class TenantCreate(BaseModel):
    nome_fantasia: str = Field(..., min_length=2, max_length=200)
    razao_social: str | None = Field(default=None, max_length=200)
    cnpj: str | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=500)
    subtitulo_cabecalho: str | None = Field(default=None, max_length=200)

    admin_nome: str = Field(..., min_length=2, max_length=200)
    admin_login: str = Field(..., min_length=3, max_length=50)
    admin_senha: str = Field(..., min_length=8, max_length=100)


class TenantUpdate(BaseModel):
    nome_fantasia: str | None = Field(default=None, min_length=2, max_length=200)
    razao_social: str | None = Field(default=None, max_length=200)
    cnpj: str | None = Field(default=None, max_length=20)
    logo_url: str | None = Field(default=None, max_length=500)
    subtitulo_cabecalho: str | None = Field(default=None, max_length=200)
    ativo: bool | None = None


class TenantOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome_fantasia: str
    razao_social: str | None
    cnpj: str | None
    logo_url: str | None
    subtitulo_cabecalho: str | None
    ativo: bool
    created_at: datetime
    updated_at: datetime


class TenantListOut(BaseModel):
    total: int
    items: list[TenantOut]


class TenantComAdminOut(BaseModel):
    tenant: TenantOut
    admin: UsuarioOut
