"""
Service da Importação de Laudo (extração assistida por IA).

Usa a API da Anthropic (Claude) com "tool use" forçado para extrair, de
forma estruturada, os isolados e o antibiograma de um laudo de
microbiologia colado pelo usuário - NUNCA grava nada no banco sozinho,
apenas devolve um preview (`LaudoImportadoOut`) para revisão manual no
formulário de edição do exame (ver `app/routers/exame_router.py`).

Princípio central (não relaxar sem alinhar com o time): a IA nunca
cadastra ou adivinha um item de catálogo clínico. Um nome extraído do
laudo só vira `*_id` preenchido quando bate EXATO (case-insensitive) com
um microrganismo/antimicrobiano já cadastrado no tenant - caso
contrário, o campo some vazio (`id: null`) + o nome bruto do laudo, para
o usuário escolher manualmente.
"""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.models.exame import Exame, MecanismoResistenciaEnum, ResultadoSIREnum
from app.repositories.antimicrobiano_repository import AntimicrobianoRepository
from app.repositories.microrganismo_repository import MicrorganismoRepository
from app.schemas.laudo_import import (
    LaudoImportadoAntibiogramaOut,
    LaudoImportadoIsoladoOut,
    LaudoImportadoOut,
)

MODEL_NAME = "claude-sonnet-5"
MAX_TOKENS = 4096
TOOL_NAME = "extrair_laudo_microbiologia"

_MENSAGEM_ERRO_GENERICA = "Não foi possível processar o laudo. Tente novamente."


def _tool_schema() -> dict:
    """
    JSON Schema da tool única usada para forçar saída estruturada
    (`tool_choice={"type": "tool", ...}`) - os `enum` de
    `mecanismo_resistencia`/`resultado` usam os valores EXATOS dos
    enums do domínio (`MecanismoResistenciaEnum`/`ResultadoSIREnum`,
    ver app/models/exame.py), para o modelo nunca inventar um valor
    fora do vocabulário que o banco aceita.
    """
    mecanismos = [item.value for item in MecanismoResistenciaEnum]
    resultados = [item.value for item in ResultadoSIREnum]

    return {
        "name": TOOL_NAME,
        "description": "Extrai os dados estruturados de um laudo de laboratório de microbiologia.",
        "input_schema": {
            "type": "object",
            "properties": {
                "prontuario": {
                    "type": ["string", "null"],
                    "description": "Número de prontuário do paciente, se mencionado no laudo.",
                },
                "nome_paciente": {
                    "type": ["string", "null"],
                    "description": "Nome do paciente, se mencionado no laudo.",
                },
                "isolados": {
                    "type": "array",
                    "description": "Microrganismos isolados na cultura (uma cultura pode ser polimicrobiana).",
                    "items": {
                        "type": "object",
                        "properties": {
                            "microrganismo_nome": {
                                "type": "string",
                                "description": "Nome do microrganismo exatamente como escrito no laudo.",
                            },
                            "mecanismo_resistencia": {
                                "type": "string",
                                "enum": mecanismos,
                                "description": "Use NENHUM se o laudo não mencionar nenhum mecanismo de resistência.",
                            },
                            "antibiograma": {
                                "type": "array",
                                "description": "Resultado de cada antimicrobiano testado contra este isolado.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "antimicrobiano_nome": {
                                            "type": "string",
                                            "description": "Nome do antimicrobiano exatamente como escrito no laudo.",
                                        },
                                        "resultado": {"type": "string", "enum": resultados},
                                    },
                                    "required": ["antimicrobiano_nome", "resultado"],
                                },
                            },
                        },
                        "required": ["microrganismo_nome", "mecanismo_resistencia", "antibiograma"],
                    },
                },
            },
            "required": ["isolados"],
        },
    }


def _mensagem_usuario(texto: str) -> str:
    return (
        "Extraia os dados de microbiologia deste laudo de laboratório:\n\n"
        f"{texto}\n\n"
        "Se o laudo não mencionar prontuário ou nome do paciente, deixe esses "
        "campos null. Para cada isolado, extraia o microrganismo, o mecanismo "
        "de resistência (NENHUM se não for mencionado) e cada antimicrobiano "
        "testado com seu resultado."
    )


class LaudoImportService:
    def __init__(self, db: Session, anthropic_client=None):
        self.db = db
        self.microrganismo_repository = MicrorganismoRepository(db)
        self.antimicrobiano_repository = AntimicrobianoRepository(db)
        # Client injetável para os testes conseguirem passar um fake sem
        # chamar a API de verdade - None cria um cliente real preguiçosamente
        # (só na primeira chamada), para a suíte não exigir
        # ANTHROPIC_API_KEY configurada só para importar este módulo.
        self._client = anthropic_client

    def _get_client(self):
        if self._client is None:
            from anthropic import Anthropic

            from app.core.config import get_settings

            self._client = Anthropic(api_key=get_settings().ANTHROPIC_API_KEY)
        return self._client

    def _chamar_ia(self, texto: str) -> dict:
        try:
            response = self._get_client().messages.create(
                model=MODEL_NAME,
                max_tokens=MAX_TOKENS,
                tools=[_tool_schema()],
                tool_choice={"type": "tool", "name": TOOL_NAME},
                messages=[{"role": "user", "content": _mensagem_usuario(texto)}],
            )
        except Exception as exc:  # noqa: BLE001 - qualquer falha de rede/API vira erro de negócio genérico
            raise BusinessRuleError(_MENSAGEM_ERRO_GENERICA) from exc

        for bloco in response.content:
            if getattr(bloco, "type", None) == "tool_use":
                return bloco.input

        raise BusinessRuleError(_MENSAGEM_ERRO_GENERICA)

    def _paciente_confere(
        self, exame: Exame, prontuario_laudo: str | None, nome_paciente_laudo: str | None
    ) -> bool:
        # Laudo não menciona paciente nenhum -> não há como estar "errado",
        # não bloqueia o usuário por falta de dado.
        if prontuario_laudo is None and nome_paciente_laudo is None:
            return True

        paciente = exame.paciente
        if prontuario_laudo is not None:
            if prontuario_laudo.strip().lower() != (paciente.prontuario or "").strip().lower():
                return False
        if nome_paciente_laudo is not None:
            if nome_paciente_laudo.strip().lower() != (paciente.nome or "").strip().lower():
                return False
        return True

    def _resolver_isolado(self, isolado_raw: dict) -> LaudoImportadoIsoladoOut:
        nome_microrganismo = isolado_raw.get("microrganismo_nome", "")
        microrganismo = self.microrganismo_repository.get_by_nome(nome_microrganismo)

        try:
            mecanismo = MecanismoResistenciaEnum(
                isolado_raw.get("mecanismo_resistencia", MecanismoResistenciaEnum.NENHUM.value)
            )
        except ValueError as exc:
            raise BusinessRuleError(_MENSAGEM_ERRO_GENERICA) from exc

        antibiograma = [
            self._resolver_antibiograma(item) for item in isolado_raw.get("antibiograma", [])
        ]

        return LaudoImportadoIsoladoOut(
            microrganismo_id=microrganismo.id if microrganismo else None,
            microrganismo_nome_laudo=nome_microrganismo,
            mecanismo_resistencia=mecanismo,
            antibiograma=antibiograma,
        )

    def _resolver_antibiograma(self, item_raw: dict) -> LaudoImportadoAntibiogramaOut:
        nome_antimicrobiano = item_raw.get("antimicrobiano_nome", "")
        antimicrobiano = self.antimicrobiano_repository.get_by_nome(nome_antimicrobiano)

        try:
            resultado = ResultadoSIREnum(item_raw.get("resultado"))
        except ValueError as exc:
            raise BusinessRuleError(_MENSAGEM_ERRO_GENERICA) from exc

        return LaudoImportadoAntibiogramaOut(
            antimicrobiano_id=antimicrobiano.id if antimicrobiano else None,
            antimicrobiano_nome_laudo=nome_antimicrobiano,
            resultado=resultado,
        )

    def importar(self, exame: Exame, texto: str) -> LaudoImportadoOut:
        extraido = self._chamar_ia(texto)

        prontuario_laudo = extraido.get("prontuario")
        nome_paciente_laudo = extraido.get("nome_paciente")

        return LaudoImportadoOut(
            paciente_confere=self._paciente_confere(
                exame, prontuario_laudo, nome_paciente_laudo
            ),
            prontuario_laudo=prontuario_laudo,
            nome_paciente_laudo=nome_paciente_laudo,
            isolados=[
                self._resolver_isolado(isolado_raw)
                for isolado_raw in extraido.get("isolados", [])
            ],
        )
