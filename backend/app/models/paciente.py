"""
Model da entidade Paciente.

Módulo: Pacientes (Documento Mestre, seção 6).
Campos cobrem cadastro, busca por prontuário e histórico microbiológico
associado (relacionamento futuro com Solicitações).
"""
from datetime import date

from sqlalchemy import Date, Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import (
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

import enum


class SexoEnum(str, enum.Enum):
    MASCULINO = "MASCULINO"
    FEMININO = "FEMININO"
    NAO_INFORMADO = "NAO_INFORMADO"


class Paciente(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "pacientes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "prontuario", name="uq_pacientes_tenant_prontuario"),
    )

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    prontuario: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    data_nascimento: Mapped[date | None] = mapped_column(Date, nullable=True)
    sexo: Mapped[SexoEnum] = mapped_column(
        Enum(SexoEnum, name="sexo_enum"), default=SexoEnum.NAO_INFORMADO
    )
    setor: Mapped[str | None] = mapped_column(String(100), nullable=True)
    leito: Mapped[str | None] = mapped_column(String(20), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Paciente {self.prontuario} - {self.nome}>"
