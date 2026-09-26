"""
Testes do Painel de Acompanhamento (`GET /api/exames/painel`) - uma
linha achatada por exame, com antibiograma agrupado por resultado.
"""
from tests.helpers import criar_antimicrobiano, criar_exame, criar_microrganismo, criar_setor


def test_painel_achata_isolados_e_antibiograma(authenticated_client):
    kpc = criar_microrganismo(authenticated_client, nome="Klebsiella pneumoniae")
    mrsa = criar_microrganismo(authenticated_client, nome="Staphylococcus aureus")
    meropenem = criar_antimicrobiano(authenticated_client, nome="Meropenem")
    amicacina = criar_antimicrobiano(authenticated_client, nome="Amicacina")
    cefepime = criar_antimicrobiano(authenticated_client, nome="Cefepime")
    oxacilina = criar_antimicrobiano(authenticated_client, nome="Oxacilina")
    setor = criar_setor(authenticated_client, nome="UTI Adulto")

    criar_exame(
        authenticated_client,
        prontuario="200100-1",
        nome="Maria Souza",
        numero_solicitacao="SOL-2026-1",
        setor_id=setor["id"],
        data_coleta="2026-09-10T08:00:00Z",
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": kpc["id"],
                "mecanismo_resistencia": "CARBAPENEMASE_KPC",
                "antibiograma": [
                    {"antimicrobiano_id": meropenem["id"], "resultado": "RESISTENTE"},
                    {"antimicrobiano_id": amicacina["id"], "resultado": "SENSIVEL"},
                    {"antimicrobiano_id": cefepime["id"], "resultado": "INTERMEDIARIO"},
                ],
            },
            {
                "microrganismo_id": mrsa["id"],
                "mecanismo_resistencia": "MRSA",
                "antibiograma": [
                    {"antimicrobiano_id": oxacilina["id"], "resultado": "RESISTENTE"},
                    {"antimicrobiano_id": amicacina["id"], "resultado": "SENSIVEL"},
                ],
            },
        ],
    )

    response = authenticated_client.get("/api/exames/painel")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    linha = data["items"][0]
    assert linha["prontuario"] == "200100-1"
    assert linha["paciente_nome"] == "Maria Souza"
    assert linha["numero_solicitacao"] == "SOL-2026-1"
    assert linha["setor"] == "UTI Adulto"
    assert linha["status_painel"] == "POSITIVA"
    assert sorted(linha["microrganismos"]) == ["Klebsiella pneumoniae", "Staphylococcus aureus"]
    assert sorted(linha["resistencia"]) == ["Meropenem", "Oxacilina"]
    assert linha["sensibilidade"] == ["Amicacina"]
    assert linha["sensivel_exposicao_aumentada"] == ["Cefepime"]
    assert sorted(linha["mecanismos_resistencia"]) == ["Carbapenemase (KPC)", "MRSA"]


def test_painel_filtra_por_mes_e_ano_da_coleta(authenticated_client):
    criar_exame(authenticated_client, prontuario="a", data_coleta="2026-08-15T10:00:00Z")
    criar_exame(authenticated_client, prontuario="b", data_coleta="2026-09-01T10:00:00Z")
    criar_exame(authenticated_client, prontuario="c", data_coleta="2025-09-20T10:00:00Z")

    def prontuarios(params):
        items = authenticated_client.get("/api/exames/painel", params=params).json()["data"]["items"]
        return sorted(i["prontuario"] for i in items)

    assert prontuarios({}) == ["a", "b", "c"]
    assert prontuarios({"ano": 2026}) == ["a", "b"]
    assert prontuarios({"mes": 9}) == ["b", "c"]
    assert prontuarios({"mes": 9, "ano": 2026}) == ["b"]


def test_painel_agrupa_parciais_como_em_andamento(authenticated_client):
    criar_exame(authenticated_client, prontuario="x", status="NEGATIVO_PARCIAL")
    criar_exame(authenticated_client, prontuario="y", status="AMOSTRA_INADEQUADA")

    items = authenticated_client.get("/api/exames/painel").json()["data"]["items"]
    por_prontuario = {i["prontuario"]: i["status_painel"] for i in items}

    assert por_prontuario == {"x": "EM_ANDAMENTO", "y": "AMOSTRA_INADEQUADA"}


def test_painel_valida_mes(authenticated_client):
    assert authenticated_client.get("/api/exames/painel?mes=13").status_code == 422
