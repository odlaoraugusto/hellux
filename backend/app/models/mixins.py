"""
Mixins reutilizáveis pelos models do Hellux.

Center para regras transversais definidas no Documento Mestre (seção 9 -
Segurança): soft delete, timestamps e auditoria básica de criação/edição.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.types import GUID


class UUIDPrimaryKeyMixin:
    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )


class TenantScopedMixin:
    """
    Mixin de multi-tenancy (Fase 1 - Fundação multi-tenant).

    Toda entidade "de negócio" (paciente, catálogo, exame, etc.) carrega o
    `tenant_id` do hospital-cliente dono do registro. O isolamento real
    entre tenants acontece via Row Level Security no Postgres (ver
    `enable_rls.sql`/migration e `app/db/session.py`) - esta coluna é o
    que a policy de RLS de cada tabela compara contra
    `current_setting('app.current_tenant_id')`.
    """

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tenants.id"), nullable=False, index=True
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SoftDeleteMixin:
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
