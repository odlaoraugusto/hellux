"""
Schemas de validação de entrada/saída do catálogo de Tipos de Cultura.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TipoCulturaCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=300)


class TipoCulturaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=300)


class TipoCulturaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    descricao: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TipoCulturaListOut(BaseModel):
    total: int
    items: list[TipoCulturaOut]
