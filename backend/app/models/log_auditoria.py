"""
Model de Log de Auditoria.

Módulo: Auditoria (Documento Mestre, seção 9 - Segurança, Sprint 13).
Registra toda requisição que altera dados (POST/PUT/PATCH/DELETE),
capturada de forma transversal por um middleware (ver
app/core/audit_middleware.py) - nenhum service precisa chamar isso
manualmente.

`usuario_login` é uma cópia (snapshot) do login no momento da ação,
para que o log continue legível mesmo se o usuário for removido depois.
"""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.db.types import GUID


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)
    # Nullable de propósito (mesmo padrão de snapshot de `usuario_login`):
    # o middleware de auditoria decodifica o tenant_id direto da claim do
    # JWT (sem consultar o banco - ver app/core/audit_middleware.py), então
    # requisições sem token válido (ex.: tentativa de login que falhou)
    # geram log sem tenant_id. Esta tabela NÃO tem RLS (ver migration da
    # Fase 1) - é auditoria administrativa, não dado de negócio do tenant.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("tenants.id"), nullable=True, index=True
    )
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(GUID(), nullable=True, index=True)
    usuario_login: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metodo: Mapped[str] = mapped_column(String(10), nullable=False)
    caminho: Mapped[str] = mapped_column(String(300), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    ip_origem: Mapped[str | None] = mapped_column(String(64), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<LogAuditoria {self.metodo} {self.caminho} ({self.status_code})>"
