"""
Model do catálogo de Antimicrobianos.

Parte da Base de Conhecimento (Documento Mestre, seção 7). Cadastro
único de cada antimicrobiano, reutilizado em todos os antibiogramas.
"""
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import (
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class Antimicrobiano(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "antimicrobianos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_antimicrobianos_tenant_nome"),
    )

    nome: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    sigla: Mapped[str | None] = mapped_column(String(20), nullable=True)
    classe: Mapped[str | None] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Antimicrobiano {self.nome}>"
