"""
Model da entidade Tenant (hospital-cliente).

Fase 1 - Fundação multi-tenant do Hellux. É o nível raiz da hierarquia de
dados: toda entidade de negócio (usuários, pacientes, catálogos, exames)
pertence a exatamente um Tenant via `tenant_id` (ver `TenantScopedMixin`
em app/models/mixins.py). Deliberadamente SEM Row Level Security nesta
própria tabela - RLS filtra "dentro" de um tenant, e a tabela de tenants
é o nível acima disso (ver migration da Fase 1 e app/db/session.py).
"""
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "tenants"

    nome_fantasia: Mapped[str] = mapped_column(String(200), nullable=False)
    razao_social: Mapped[str | None] = mapped_column(String(200), nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subtitulo_cabecalho: Mapped[str | None] = mapped_column(String(200), nullable=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tenant {self.nome_fantasia}>"
