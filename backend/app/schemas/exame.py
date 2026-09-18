"""
Schemas do módulo Exames.

O módulo Exames é uma camada aditiva que compõe Solicitação + Cultura
numa única operação, refletindo o fluxo real do laboratório (a coleta
já aconteceu no sistema do hospital antes de qualquer coisa chegar ao
Hellux). Ele não substitui os módulos Solicitações/Microbiologia,
que continuam existindo intactos para o caso de agendamento antecipado.

Não há um `ExameOut` próprio: a resposta de todos os endpoints reutiliza
`CulturaOut` (ver app.schemas.cultura), já que uma Cultura com sua
Solicitação aninhada É a representação completa de um "exame".
"""
import uuid
from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.cultura import GrupoCulturaEnum, ResultadoCulturaEnum
from app.models.solicitacao import PrioridadeEnum


class ExameCreate(BaseModel):
    # Campos da Solicitação
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
    material: str = Field(..., min_length=2, max_length=100)
    origem: str | None = Field(default=None, max_length=100)
    prioridade: PrioridadeEnum = PrioridadeEnum.ROTINA
    data_coleta: datetime | None = Field(
        default=None,
        description="Se não informada, usa o momento do cadastro (assume que a "
        "coleta acabou de acontecer).",
    )
    observacoes_solicitacao: str | None = Field(default=None, max_length=1000)

    # Campos da Cultura
    grupo: GrupoCulturaEnum = GrupoCulturaEnum.CULTURA_GERAL
    resultado: ResultadoCulturaEnum = ResultadoCulturaEnum.EM_ANALISE
    microrganismo_ids: list[uuid.UUID] = Field(default_factory=list)
    previsao_liberacao: date | None = Field(
        default=None,
        description="Se não informado, é calculada automaticamente a partir do "
        "parâmetro 'prazo_solicitacao_dias'.",
    )
    observacoes_cultura: str | None = Field(default=None, max_length=1000)


class ExameUpdate(BaseModel):
    """Todos os campos opcionais - permite atualização parcial (PATCH)."""

    # Campos da Solicitação
    material: str | None = Field(default=None, min_length=2, max_length=100)
    origem: str | None = Field(default=None, max_length=100)
    prioridade: PrioridadeEnum | None = None
    data_coleta: datetime | None = None
    observacoes_solicitacao: str | None = Field(default=None, max_length=1000)

    # Campos da Cultura
    grupo: GrupoCulturaEnum | None = None
    resultado: ResultadoCulturaEnum | None = None
    microrganismo_ids: list[uuid.UUID] | None = None
    previsao_liberacao: date | None = None
    observacoes_cultura: str | None = Field(default=None, max_length=1000)
