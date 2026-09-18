"""
Model do catálogo de Microrganismos.

Parte da Base de Conhecimento (Documento Mestre, seção 7). Ao cadastrar
um microrganismo aqui uma única vez, o sistema passa a "saber" seu
Gram e tipo automaticamente em todas as culturas relacionadas — a
ideia da "IA silenciosa" descrita no planejamento do projeto (dashboards
mostrando ex.: "82% dos isolados foram bacilos Gram-negativos" sem
cadastro manual extra).
"""
from sqlalchemy import Enum, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.mixins import (
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

import enum


class GramEnum(str, enum.Enum):
    POSITIVO = "POSITIVO"
    NEGATIVO = "NEGATIVO"
    NAO_SE_APLICA = "NAO_SE_APLICA"


class TipoMicrorganismoEnum(str, enum.Enum):
    BACTERIA = "BACTERIA"
    FUNGO = "FUNGO"
    MICOBACTERIA = "MICOBACTERIA"
    VIRUS = "VIRUS"
    PARASITA = "PARASITA"
    OUTRO = "OUTRO"


class MorfologiaEnum(str, enum.Enum):
    COCO = "COCO"
    BACILO = "BACILO"
    COCOBACILO = "COCOBACILO"
    LEVEDURA = "LEVEDURA"
    NAO_SE_APLICA = "NAO_SE_APLICA"


class GrupoFenotipicoEnum(str, enum.Enum):
    """
    Família fenotípica usada pela Matriz de Sensibilidade CCIH (Fase 1.5)
    para agrupar o perfil de resistência - é uma distinção clínica real
    que não dá para derivar de `gram`/`tipo`/`morfologia`/`fermentador`
    (ex.: Staphylococcus aureus e os CoNS têm exatamente os mesmos
    valores nesses campos, mas perfis de resistência muito diferentes).

    `OUTROS` é o catch-all pro que não se encaixa nos demais grupos
    (micobactérias, parasitas, gram-negativos não-bacilo, etc.).
    """

    CONS = "CONS"
    S_AUREUS = "S_AUREUS"
    BGN_F = "BGN_F"
    BGN_NF = "BGN_NF"
    LEVEDURAS = "LEVEDURAS"
    OUTROS_GRAM_POSITIVOS = "OUTROS_GRAM_POSITIVOS"
    OUTROS = "OUTROS"


class Microrganismo(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "microrganismos"
    __table_args__ = (
        UniqueConstraint("tenant_id", "nome", name="uq_microrganismos_tenant_nome"),
    )

    nome: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    nome_cientifico: Mapped[str | None] = mapped_column(String(150), nullable=True)
    gram: Mapped[GramEnum] = mapped_column(
        Enum(GramEnum, name="gram_enum"), default=GramEnum.NAO_SE_APLICA
    )
    tipo: Mapped[TipoMicrorganismoEnum] = mapped_column(
        Enum(TipoMicrorganismoEnum, name="tipo_microrganismo_enum"),
        default=TipoMicrorganismoEnum.BACTERIA,
    )
    morfologia: Mapped[MorfologiaEnum] = mapped_column(
        Enum(MorfologiaEnum, name="morfologia_enum"),
        default=MorfologiaEnum.NAO_SE_APLICA,
        nullable=False,
    )
    # None = "não se aplica" (só é relevante pra bacilos Gram-negativos: True =
    # fermentador de glicose, ex.: Enterobacterales; False = não-fermentador,
    # ex.: Pseudomonas/Acinetobacter). Nos demais grupos (Gram-positivo, fungo
    # etc.) o campo permanece None.
    fermentador: Mapped[bool | None] = mapped_column(nullable=True)
    familia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    relevancia_clinica: Mapped[str | None] = mapped_column(String(500), nullable=True)
    grupo_fenotipico: Mapped[GrupoFenotipicoEnum] = mapped_column(
        Enum(GrupoFenotipicoEnum, name="grupo_fenotipico_enum"),
        default=GrupoFenotipicoEnum.OUTROS,
        server_default=GrupoFenotipicoEnum.OUTROS.value,
        nullable=False,
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Microrganismo {self.nome}>"
