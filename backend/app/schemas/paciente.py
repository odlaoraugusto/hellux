"""
Schemas de validação de entrada/saída do módulo Pacientes.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.paciente import SexoEnum


class PacienteBase(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200)
    prontuario: str = Field(..., min_length=1, max_length=50)
    data_nascimento: date | None = None
    sexo: SexoEnum = SexoEnum.NAO_INFORMADO
    setor: str | None = Field(default=None, max_length=100)
    leito: str | None = Field(default=None, max_length=20)
    observacoes: str | None = Field(default=None, max_length=1000)


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    """Todos os campos opcionais - permite atualização parcial (PATCH)."""

    nome: str | None = Field(default=None, min_length=2, max_length=200)
    prontuario: str | None = Field(default=None, min_length=1, max_length=50)
    data_nascimento: date | None = None
    sexo: SexoEnum | None = None
    setor: str | None = Field(default=None, max_length=100)
    leito: str | None = Field(default=None, max_length=20)
    observacoes: str | None = Field(default=None, max_length=1000)


class PacienteOut(PacienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class PacienteListOut(BaseModel):
    """Resposta paginada da listagem de pacientes."""

    total: int
    page: int
    page_size: int
    items: list[PacienteOut]
