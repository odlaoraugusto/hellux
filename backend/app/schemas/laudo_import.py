"""
Schemas da Importação de Laudo (extração assistida por IA).

O texto colado de um laudo de microbiologia é enviado para a API da
Anthropic (ver `app/services/laudo_import_service.py`), que devolve um
preview estruturado - NUNCA grava nada no banco sozinho. A IA também
nunca cadastra/adivinha um item novo do catálogo clínico: quando o nome
extraído do laudo não bate exatamente (case-insensitive) com um
microrganismo/antimicrobiano já cadastrado no tenant, o `*_id`
correspondente vem `null` e o nome bruto do laudo é preservado em
`*_nome_laudo`, para o usuário resolver manualmente no formulário.
"""
import uuid

from pydantic import BaseModel, Field

from app.models.exame import MecanismoResistenciaEnum, ResultadoSIREnum


class LaudoImportarIn(BaseModel):
    texto: str = Field(..., min_length=10, description="Texto colado do laudo de laboratório.")


class LaudoImportadoAntibiogramaOut(BaseModel):
    antimicrobiano_id: uuid.UUID | None = Field(
        default=None,
        description="Preenchido apenas se o nome do laudo bateu exato com um "
        "antimicrobiano já cadastrado no tenant.",
    )
    antimicrobiano_nome_laudo: str
    resultado: ResultadoSIREnum


class LaudoImportadoIsoladoOut(BaseModel):
    microrganismo_id: uuid.UUID | None = Field(
        default=None,
        description="Preenchido apenas se o nome do laudo bateu exato com um "
        "microrganismo já cadastrado no tenant.",
    )
    microrganismo_nome_laudo: str
    mecanismo_resistencia: MecanismoResistenciaEnum
    antibiograma: list[LaudoImportadoAntibiogramaOut] = Field(default_factory=list)


class LaudoImportadoOut(BaseModel):
    paciente_confere: bool = Field(
        description="False se o laudo trouxe prontuário e/ou nome de paciente "
        "e algum dos dois não bate com o exame sendo editado."
    )
    prontuario_laudo: str | None = None
    nome_paciente_laudo: str | None = None
    isolados: list[LaudoImportadoIsoladoOut] = Field(default_factory=list)
