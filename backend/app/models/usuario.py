"""
Model da entidade Usuario.

Módulo: Autenticação / Configurações (Documento Mestre, seção 9 -
Segurança, e seção 6 - Sprint 11/12). Guarda apenas o hash da senha,
nunca a senha em texto puro (ver app/core/security.py).
"""
import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Index, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.db.types import GUID
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

import enum


class PerfilUsuarioEnum(str, enum.Enum):
    # Não pertence a nenhum tenant - administra a lista de tenants em si
    # (cria/edita/ativa/desativa) e, dentro de cada um, o usuário ADMIN
    # inicial (ver app/routers/tenant_router.py). Usuario.tenant_id é
    # NULL exclusivamente para este perfil (ver __table_args__ abaixo).
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    BIOMEDICO = "BIOMEDICO"
    TECNICO = "TECNICO"
    VISUALIZADOR = "VISUALIZADOR"


class Usuario(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        # Fase 1 - multi-tenant: o login deixa de ser único globalmente e
        # passa a ser único por tenant (dois hospitais podem ter, cada um,
        # um usuário "admin"). Não cobre SUPER_ADMIN (tenant_id nulo) -
        # ver índice parcial abaixo.
        UniqueConstraint("tenant_id", "login", name="uq_usuarios_tenant_login"),
        # NULL nunca é igual a NULL num UNIQUE constraint normal do
        # Postgres, então dois SUPER_ADMIN com o mesmo login NÃO seriam
        # barrados pela constraint acima - por isso um índice único
        # parcial, só sobre as linhas sem tenant.
        Index(
            "uq_usuarios_super_admin_login",
            "login",
            unique=True,
            postgresql_where=text("tenant_id IS NULL"),
            sqlite_where=text("tenant_id IS NULL"),
        ),
        # tenant_id NULL <=> perfil SUPER_ADMIN, nunca as duas coisas
        # juntas nem separadas.
        CheckConstraint(
            "(perfil = 'SUPER_ADMIN' AND tenant_id IS NULL) OR "
            "(perfil <> 'SUPER_ADMIN' AND tenant_id IS NOT NULL)",
            name="ck_usuarios_super_admin_sem_tenant",
        ),
    )

    # Nullable de propósito (só para SUPER_ADMIN - ver CheckConstraint
    # acima) - por isso não usa `TenantScopedMixin` (que é NOT NULL),
    # a coluna é declarada manualmente aqui.
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("tenants.id"), nullable=True, index=True
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    login: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuarioEnum] = mapped_column(
        Enum(PerfilUsuarioEnum, name="perfil_usuario_enum"),
        default=PerfilUsuarioEnum.VISUALIZADOR,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario {self.login} ({self.perfil})>"
