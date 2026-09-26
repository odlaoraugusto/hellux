"""
Schemas do fluxo de Exame unificado (Fase 1).

`Exame` é agora a entidade "dona" de todo o fluxo (não compõe mais
Solicitação + Cultura) - resolve o paciente por prontuário (cria se não
existir) e grava diretamente o pedido + resultado + isolados +
antibiograma numa única operação. Ver app/services/exame_service.py.
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.exame import MecanismoResistenciaEnum, ResultadoSIREnum, StatusExameEnum
from app.schemas.antimicrobiano import AntimicrobianoOut
from app.schemas.material import MaterialOut
from app.schemas.microrganismo import MicrorganismoOut
from app.schemas.paciente import PacienteOut
from app.schemas.setor import SetorOut
from app.schemas.tipo_cultura import TipoCulturaOut


class ExameAntibiogramaIn(BaseModel):
    antimicrobiano_id: uuid.UUID
    resultado: ResultadoSIREnum


class ExameIsoladoIn(BaseModel):
    microrganismo_id: uuid.UUID
    mecanismo_resistencia: MecanismoResistenciaEnum = MecanismoResistenciaEnum.NENHUM
    nao_realizado_tecnico: bool = Field(
        default=False,
        description="Dispensa este isolado específico da exigência de "
        "antibiograma (ex.: microrganismo sem protocolo BrCAST).",
    )
    motivo_dispensa_tsa: str | None = Field(default=None, max_length=500)
    antibiograma: list[ExameAntibiogramaIn] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validar_motivo_dispensa(self) -> "ExameIsoladoIn":
        if self.nao_realizado_tecnico and not self.motivo_dispensa_tsa:
            raise ValueError(
                "motivo_dispensa_tsa é obrigatório quando nao_realizado_tecnico=True."
            )
        return self


class ExameCreate(BaseModel):
    paciente_prontuario: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Se já existir um paciente com este prontuário, ele é "
        "reaproveitado (o nome cadastrado NÃO é sobrescrito). Caso "
        "contrário, um novo paciente é criado com 'paciente_nome'.",
    )
    paciente_nome: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Usado apenas para cadastrar um paciente novo, quando o "
        "prontuário informado ainda não existe.",
    )
    setor_id: uuid.UUID | None = None
    numero_solicitacao: str | None = Field(default=None, max_length=50)
    tipo_cultura_id: uuid.UUID
    material_id: uuid.UUID
    data_coleta: datetime | None = Field(
        default=None,
        description="Se não informada, usa o momento do cadastro (assume que a "
        "coleta acabou de acontecer).",
    )
    previsao_liberacao: date | None = Field(
        default=None,
        description="Se não informado, é calculado automaticamente a partir do "
        "parâmetro 'prazo_solicitacao_dias'.",
    )
    status: StatusExameEnum = StatusExameEnum.AGUARDANDO_TRIAGEM
    identificacao_preliminar: str | None = Field(default=None, max_length=300)
    observacoes: str | None = Field(default=None, max_length=1000)
    isolados: list[ExameIsoladoIn] = Field(default_factory=list)


class ExameUpdate(BaseModel):
    """Todos os campos opcionais - permite atualização parcial (PATCH)."""

    setor_id: uuid.UUID | None = None
    numero_solicitacao: str | None = Field(default=None, max_length=50)
    tipo_cultura_id: uuid.UUID | None = None
    material_id: uuid.UUID | None = None
    data_coleta: datetime | None = None
    previsao_liberacao: date | None = None
    status: StatusExameEnum | None = None
    identificacao_preliminar: str | None = Field(default=None, max_length=300)
    observacoes: str | None = Field(default=None, max_length=1000)
    isolados: list[ExameIsoladoIn] | None = None


class ExameAntibiogramaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    antimicrobiano: AntimicrobianoOut
    resultado: ResultadoSIREnum


class ExameIsoladoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    microrganismo: MicrorganismoOut
    mecanismo_resistencia: MecanismoResistenciaEnum
    nao_realizado_tecnico: bool
    motivo_dispensa_tsa: str | None
    antibiograma: list[ExameAntibiogramaOut] = []


class ExameOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    paciente_id: uuid.UUID
    paciente: PacienteOut | None = None
    setor_id: uuid.UUID | None
    setor: SetorOut | None = None
    tipo_cultura_id: uuid.UUID
    tipo_cultura: TipoCulturaOut | None = None
    material_id: uuid.UUID
    material: MaterialOut | None = None
    numero_solicitacao: str | None = None
    data_coleta: datetime
    previsao_liberacao: date | None
    status: StatusExameEnum
    identificacao_preliminar: str | None
    observacoes: str | None
    isolados: list[ExameIsoladoOut] = []
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ExameParcialOut(ExameOut):
    pendencia: str


class ExameListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ExameOut]


class ExameParcialListOut(BaseModel):
    total: int
    items: list[ExameParcialOut]


class PainelLinhaOut(BaseModel):
    """Linha do Painel de Acompanhamento (ver ExameService.painel_acompanhamento)."""

    id: uuid.UUID
    prontuario: str | None
    paciente_nome: str | None
    numero_solicitacao: str | None
    data_coleta: datetime
    tipo_cultura: str | None
    material: str | None
    setor: str | None
    status: StatusExameEnum
    status_painel: str
    microrganismos: list[str]
    resistencia: list[str]
    sensibilidade: list[str]
    sensivel_exposicao_aumentada: list[str]
    mecanismos_resistencia: list[str]
