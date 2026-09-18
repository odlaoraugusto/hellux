"""
Model do catálogo de Materiais biológicos.

Módulo: Configurações (Documento Mestre, seção 6 - Sprint 11). Usado para
padronizar o campo "material" das Solicitações (ex.: Hemocultura, Urina,
Escarro) e evitar variações de digitação que fragmentariam relatórios e
indicadores.
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


class Material(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "materiais"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_materiais_tenant_nome"),
    )

    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    descricao: Mapped[str | None] = mapped_column(String(300), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Material {self.nome}>"
