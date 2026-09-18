"""
Model da entidade Usuario.

Módulo: Autenticação / Configurações (Documento Mestre, seção 9 -
Segurança, e seção 6 - Sprint 11/12). Guarda apenas o hash da senha,
nunca a senha em texto puro (ver app/core/security.py).
"""
from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin

import enum


class PerfilUsuarioEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    BIOMEDICO = "BIOMEDICO"
    TECNICO = "TECNICO"
    VISUALIZADOR = "VISUALIZADOR"


class Usuario(UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "usuarios"

    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    login: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    perfil: Mapped[PerfilUsuarioEnum] = mapped_column(
        Enum(PerfilUsuarioEnum, name="perfil_usuario_enum"),
        default=PerfilUsuarioEnum.VISUALIZADOR,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Usuario {self.login} ({self.perfil})>"
