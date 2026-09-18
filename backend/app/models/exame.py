"""
Models do fluxo de Exame unificado (Fase 1).

Substitui a composição antiga Solicitação -> Cultura -> CulturaMicrorganismo
-> Antibiograma -> AntibiogramaResultado por três tabelas:

- `Exame`: o pedido + o resultado da cultura numa única entidade (a coleta
  já aconteceu antes de chegar ao Hellux - não existe mais uma tela de
  "Solicitação" separada). Substitui `Solicitacao` + `Cultura`.
- `ExameIsolado`: um microrganismo isolado num exame positivo (uma cultura
  pode ser polimicrobiana). Substitui `CulturaMicrorganismo`, com dois
  campos novos: `mecanismo_resistencia` (MRSA/ESBL/KPC/...) e o par
  `nao_realizado_tecnico`/`motivo_dispensa_tsa` (dispensa individual da
  exigência de antibiograma, mesmo espírito do antigo
  `sem_antibiograma_padronizado`, mas com o motivo registrado).
- `ExameAntibiograma`: substitui `Antibiograma` + `AntibiogramaResultado`
  achatados numa tabela só (isolado + antimicrobiano + resultado S/I/R) -
  não existe mais uma entidade "Antibiograma" com liberação própria; a
  liberação de todo o exame é controlada pelo `status` do `Exame`.

`status_exame_enum` unifica os dois enums antigos (`StatusSolicitacaoEnum`
+ `ResultadoCulturaEnum`) num único status "simplificado", incluindo
estados parciais (a cultura já deu positivo/negativo preliminarmente, mas
o antibiograma ainda não fechou).
"""
import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.db.types import GUID
from app.models.mixins import (
    SoftDeleteMixin,
    TenantScopedMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)

import enum


class StatusExameEnum(str, enum.Enum):
    AGUARDANDO_TRIAGEM = "AGUARDANDO_TRIAGEM"
    NEGATIVO_PARCIAL = "NEGATIVO_PARCIAL"
    POSITIVO_PARCIAL = "POSITIVO_PARCIAL"
    NEGATIVO = "NEGATIVO"
    POSITIVO = "POSITIVO"
    CONTAMINACAO = "CONTAMINACAO"


# Estados "em andamento" (ainda não finalizados) x "finais" - usados pelo
# Dashboard/CCIH para separar pendências de indicadores fechados.
STATUS_EM_ANDAMENTO = (
    StatusExameEnum.AGUARDANDO_TRIAGEM,
    StatusExameEnum.NEGATIVO_PARCIAL,
    StatusExameEnum.POSITIVO_PARCIAL,
)
STATUS_FINAIS = (
    StatusExameEnum.NEGATIVO,
    StatusExameEnum.POSITIVO,
    StatusExameEnum.CONTAMINACAO,
)
STATUS_POSITIVO = (StatusExameEnum.POSITIVO_PARCIAL, StatusExameEnum.POSITIVO)


class MecanismoResistenciaEnum(str, enum.Enum):
    NENHUM = "NENHUM"
    MRSA = "MRSA"
    ESBL = "ESBL"
    CARBAPENEMASE_KPC = "CARBAPENEMASE_KPC"
    VRE = "VRE"
    D_TESTE_POSITIVO = "D_TESTE_POSITIVO"
    OUTRO = "OUTRO"


# Reaproveita o mesmo enum S/I/R de antes - o valor não muda, só a tabela
# que o guarda (ver docstring do módulo).
class ResultadoSIREnum(str, enum.Enum):
    SENSIVEL = "SENSIVEL"
    INTERMEDIARIO = "INTERMEDIARIO"
    RESISTENTE = "RESISTENTE"


class Exame(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "exames"

    paciente_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("pacientes.id"), nullable=False, index=True
    )
    setor_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID(), ForeignKey("setores.id"), nullable=True, index=True
    )
    tipo_cultura_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("tipos_cultura.id"), nullable=False, index=True
    )
    material_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("materiais.id"), nullable=False, index=True
    )
    data_coleta: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    previsao_liberacao: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[StatusExameEnum] = mapped_column(
        Enum(StatusExameEnum, name="status_exame_enum"),
        default=StatusExameEnum.AGUARDANDO_TRIAGEM,
        nullable=False,
        index=True,
    )
    identificacao_preliminar: Mapped[str | None] = mapped_column(String(300), nullable=True)
    observacoes: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    paciente = relationship("Paciente", lazy="joined")
    setor = relationship("Setor", lazy="joined")
    tipo_cultura = relationship("TipoCultura", lazy="joined")
    material = relationship("Material", lazy="joined")
    isolados = relationship(
        "ExameIsolado",
        back_populates="exame",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Exame {self.id} - {self.status}>"


class ExameIsolado(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Microrganismo isolado num exame (positivo/positivo parcial) - uma
    cultura pode ser polimicrobiana, por isso é uma tabela filha (N:N via
    FK simples pra microrganismo, não uma associação pura).

    Sem soft delete de propósito - a lista de isolados de um exame é
    substituída por inteiro a cada edição (ver
    `ExameRepository.definir_isolados`), mesmo padrão do antigo
    `CulturaMicrorganismo`.
    """

    __tablename__ = "exame_isolados"

    exame_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("exames.id"), nullable=False, index=True
    )
    microrganismo_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("microrganismos.id"), nullable=False, index=True
    )
    mecanismo_resistencia: Mapped[MecanismoResistenciaEnum] = mapped_column(
        Enum(MecanismoResistenciaEnum, name="mecanismo_resistencia_enum"),
        default=MecanismoResistenciaEnum.NENHUM,
        nullable=False,
    )
    nao_realizado_tecnico: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, server_default="false"
    )
    motivo_dispensa_tsa: Mapped[str | None] = mapped_column(Text, nullable=True)

    exame = relationship("Exame", back_populates="isolados")
    microrganismo = relationship("Microrganismo", lazy="joined")
    antibiograma = relationship(
        "ExameAntibiograma",
        back_populates="isolado",
        lazy="joined",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExameIsolado exame={self.exame_id} micro={self.microrganismo_id}>"


class ExameAntibiograma(TenantScopedMixin, UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """
    Resultado S/I/R de um antimicrobiano testado contra um isolado.

    Achata o antigo par Antibiograma + AntibiogramaResultado numa única
    tabela (isolado + antimicrobiano + resultado) - não existe mais uma
    "liberação" própria do antibiograma; a liberação de todo o exame é
    controlada pelo `status` do `Exame` (ver docstring do módulo).
    """

    __tablename__ = "exame_antibiogramas"

    isolado_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("exame_isolados.id"), nullable=False, index=True
    )
    antimicrobiano_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("antimicrobianos.id"), nullable=False, index=True
    )
    resultado: Mapped[ResultadoSIREnum] = mapped_column(
        Enum(ResultadoSIREnum, name="resultado_sir_enum"), nullable=False
    )

    isolado = relationship("ExameIsolado", back_populates="antibiograma")
    antimicrobiano = relationship("Antimicrobiano", lazy="joined")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<ExameAntibiograma {self.antimicrobiano_id} = {self.resultado}>"
