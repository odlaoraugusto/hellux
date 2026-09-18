"""
Model do catálogo de Tipos de Cultura.

Fase 1 - Fluxo de Exame unificado. Substitui o enum fixo
`GrupoCulturaEnum` (HEMOCULTURA/CULTURA_GERAL/VIGILANCIA/BK/FUNGOS) por
um catálogo tenant-scoped, no mesmo padrão dos catálogos de Setores e
Materiais (app/models/setor.py, app/models/material.py) - cada hospital
pode ter sua própria taxonomia de tipos de cultura em vez de ficar preso
a uma lista fixa no código.
"""
from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import SoftDeleteMixin, TenantScopedMixin, TimestampMixin, UUIDPrimaryKeyMixin


class TipoCultura(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "tipos_cultura"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_tipos_cultura_tenant_nome"),
    )

    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<TipoCultura {self.nome}>"
