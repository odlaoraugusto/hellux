"""
Model do catálogo de Setores hospitalares.

Módulo: Configurações (Documento Mestre, seção 6 - Sprint 11). Usado para
padronizar o campo "origem" das Solicitações (ex.: UTI, Enfermaria,
Ambulatório) - importante para os indicadores de distribuição por setor
da CCIH não ficarem fragmentados por variações de digitação ("UTI",
"uti", "U.T.I.").
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


class Setor(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "setores"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_setores_tenant_nome"),
    )

    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Setor {self.nome}>"
