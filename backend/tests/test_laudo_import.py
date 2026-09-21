"""
Testes da Importação de Laudo (extração assistida por IA).

Não chama a API de verdade da Anthropic: injeta um `FakeAnthropicClient`
direto no `LaudoImportService`, simulando a resposta da tool ("tool
use") que o service espera ler. Por isso os testes chamam
`LaudoImportService.importar()` diretamente (não passam pelo endpoint
HTTP) - o exame usado é obtido do mesmo `db_session` da fixture
`authenticated_client` (mesma sessão usada pelo TestClient via
`override_get_db`, ver conftest.py).
"""
import uuid
from types import SimpleNamespace

from tests.helpers import criar_antimicrobiano, criar_exame, criar_microrganismo

from app.models.exame import StatusExameEnum
from app.repositories.exame_repository import ExameRepository
from app.services.laudo_import_service import LaudoImportService


class FakeAnthropicClient:
    """
    Simula `anthropic.Anthropic`: só o suficiente para
    `LaudoImportService._chamar_ia` conseguir ler `.content[0].input`,
    exatamente como faria com o bloco `tool_use` de uma resposta real.
    """

    def __init__(self, input_extraido: dict):
        self._input_extraido = input_extraido
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        bloco = SimpleNamespace(type="tool_use", input=self._input_extraido)
        return SimpleNamespace(content=[bloco])


def _obter_exame(db_session, exame_id: str):
    return ExameRepository(db_session).get_by_id(uuid.UUID(exame_id))


def test_importar_laudo_resolve_isolado_e_antimicrobiano_cadastrados(authenticated_client, db_session):
    microrganismo = criar_microrganismo(authenticated_client, nome="Klebsiella pneumoniae")
    antimicrobiano = criar_antimicrobiano(authenticated_client, nome="Meropenem")
    criado = criar_exame(authenticated_client, status=StatusExameEnum.POSITIVO.value).json()["data"]
    exame = _obter_exame(db_session, criado["id"])

    fake_client = FakeAnthropicClient(
        {
            "prontuario": None,
            "nome_paciente": None,
            "isolados": [
                {
                    "microrganismo_nome": "klebsiella pneumoniae",  # case diferente do cadastro
                    "mecanismo_resistencia": "ESBL",
                    "antibiograma": [
                        {"antimicrobiano_nome": "meropenem", "resultado": "RESISTENTE"}
                    ],
                }
            ],
        }
    )
    service = LaudoImportService(db_session, anthropic_client=fake_client)

    resultado = service.importar(exame, "laudo de teste")

    assert len(resultado.isolados) == 1
    isolado = resultado.isolados[0]
    assert str(isolado.microrganismo_id) == microrganismo["id"]
    assert isolado.microrganismo_nome_laudo == "klebsiella pneumoniae"
    assert isolado.mecanismo_resistencia.value == "ESBL"
    assert len(isolado.antibiograma) == 1
    assert str(isolado.antibiograma[0].antimicrobiano_id) == antimicrobiano["id"]
    assert isolado.antibiograma[0].resultado.value == "RESISTENTE"


def test_importar_laudo_nome_nao_cadastrado_vem_com_id_nulo(authenticated_client, db_session):
    criado = criar_exame(authenticated_client, status=StatusExameEnum.POSITIVO.value).json()["data"]
    exame = _obter_exame(db_session, criado["id"])

    fake_client = FakeAnthropicClient(
        {
            "prontuario": None,
            "nome_paciente": None,
            "isolados": [
                {
                    "microrganismo_nome": "Microrganismo Nunca Cadastrado",
                    "mecanismo_resistencia": "NENHUM",
                    "antibiograma": [
                        {
                            "antimicrobiano_nome": "Antimicrobiano Nunca Cadastrado",
                            "resultado": "SENSIVEL",
                        }
                    ],
                }
            ],
        }
    )
    service = LaudoImportService(db_session, anthropic_client=fake_client)

    resultado = service.importar(exame, "laudo de teste")

    isolado = resultado.isolados[0]
    assert isolado.microrganismo_id is None
    assert isolado.microrganismo_nome_laudo == "Microrganismo Nunca Cadastrado"
    assert isolado.antibiograma[0].antimicrobiano_id is None
    assert isolado.antibiograma[0].antimicrobiano_nome_laudo == "Antimicrobiano Nunca Cadastrado"


def test_importar_laudo_paciente_diferente_nao_confere(authenticated_client, db_session):
    criado = criar_exame(
        authenticated_client, prontuario="p-original", nome="Paciente Original"
    ).json()["data"]
    exame = _obter_exame(db_session, criado["id"])

    fake_client = FakeAnthropicClient(
        {"prontuario": "outro-prontuario", "nome_paciente": None, "isolados": []}
    )
    service = LaudoImportService(db_session, anthropic_client=fake_client)

    resultado = service.importar(exame, "laudo de teste")

    assert resultado.paciente_confere is False
    assert resultado.prontuario_laudo == "outro-prontuario"


def test_importar_laudo_paciente_igual_confere(authenticated_client, db_session):
    criado = criar_exame(
        authenticated_client, prontuario="p-original", nome="Paciente Original"
    ).json()["data"]
    exame = _obter_exame(db_session, criado["id"])

    fake_client = FakeAnthropicClient(
        {"prontuario": "P-Original", "nome_paciente": "paciente original", "isolados": []}
    )
    service = LaudoImportService(db_session, anthropic_client=fake_client)

    resultado = service.importar(exame, "laudo de teste")

    assert resultado.paciente_confere is True


def test_importar_laudo_sem_mencao_a_paciente_confere(authenticated_client, db_session):
    criado = criar_exame(authenticated_client).json()["data"]
    exame = _obter_exame(db_session, criado["id"])

    fake_client = FakeAnthropicClient({"prontuario": None, "nome_paciente": None, "isolados": []})
    service = LaudoImportService(db_session, anthropic_client=fake_client)

    resultado = service.importar(exame, "laudo de teste")

    assert resultado.paciente_confere is True
    assert resultado.prontuario_laudo is None
    assert resultado.nome_paciente_laudo is None
