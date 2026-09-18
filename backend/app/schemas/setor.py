"""
Schemas de validação de entrada/saída do catálogo de Setores.
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SetorCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=300)
    macro_grupo: str | None = Field(
        default=None,
        max_length=100,
        description="Agrupamento livre por tenant (ex.: 'UTI', 'Enfermaria', "
        "'PA/Ambulatório'), usado pela Matriz de Sensibilidade CCIH para "
        "não fragmentar o indicador por setor individual.",
    )


class SetorUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=100)
    descricao: str | None = Field(default=None, max_length=300)
    macro_grupo: str | None = Field(default=None, max_length=100)


class SetorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    nome: str
    descricao: str | None
    macro_grupo: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SetorListOut(BaseModel):
    total: int
    items: list[SetorOut]
