"""
Testes do módulo CCIH (Sprint 9).

Fase 1 (fluxo de Exame unificado): reescrito sobre `/api/exames` no
lugar de `/api/solicitacoes` + `/api/microbiologia/culturas` +
`/api/antibiogramas` (removidos nesta mesma fase). O filtro que antes
era por `origem` (string livre) agora é por `setor_id` (FK de verdade).
"""
from datetime import date, timedelta

from tests.helpers import criar_antimicrobiano, criar_exame, criar_microrganismo, criar_setor


def _fluxo_positivo_com_antibiograma(
    client,
    prontuario,
    setor_nome="UTI",
    nome_micro="Klebsiella pneumoniae",
    resultado_sir="RESISTENTE",
):
    setor = criar_setor(client, setor_nome)
    microrganismo = criar_microrganismo(client, nome_micro)
    antimicrobiano = criar_antimicrobiano(client, f"Antimicrobiano {prontuario}")

    exame = criar_exame(
        client,
        prontuario=prontuario,
        setor_id=setor["id"],
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": microrganismo["id"],
                "antibiograma": [
                    {"antimicrobiano_id": antimicrobiano["id"], "resultado": resultado_sir}
                ],
            }
        ],
    ).json()["data"]

    return exame, setor


def test_indicadores_estrutura_basica(authenticated_client):
    response = authenticated_client.get("/api/ccih/indicadores")
    assert response.status_code == 200
    body = response.json()["data"]
    for campo in (
        "periodo_inicio",
        "periodo_fim",
        "total_solicitacoes",
        "total_culturas_positivas",
        "taxa_positividade",
        "distribuicao_por_setor",
        "perfil_microbiologico",
        "taxa_resistencia",
    ):
        assert campo in body


def test_total_solicitacoes_e_culturas_positivas(authenticated_client):
    _fluxo_positivo_com_antibiograma(authenticated_client, "c1")
    _fluxo_positivo_com_antibiograma(authenticated_client, "c2")

    body = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    assert body["total_solicitacoes"] == 2
    assert body["total_culturas_positivas"] == 2
    assert body["taxa_positividade"] == 100.0


def test_distribuicao_por_setor(authenticated_client):
    _fluxo_positivo_com_antibiograma(authenticated_client, "c3", setor_nome="UTI")
    _fluxo_positivo_com_antibiograma(authenticated_client, "c4", setor_nome="Enfermaria")

    body = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    setores = {item["setor"]: item["total_positivas"] for item in body["distribuicao_por_setor"]}
    assert setores.get("UTI") == 1
    assert setores.get("Enfermaria") == 1


def test_filtro_por_setor(authenticated_client):
    _, setor_uti = _fluxo_positivo_com_antibiograma(
        authenticated_client, "c10", setor_nome="UTI", resultado_sir="RESISTENTE"
    )
    _fluxo_positivo_com_antibiograma(
        authenticated_client, "c11", setor_nome="Enfermaria", resultado_sir="SENSIVEL"
    )

    body = authenticated_client.get(
        "/api/ccih/indicadores", params={"setor_id": setor_uti["id"]}
    ).json()["data"]

    assert body["filtro_setor"] == "UTI"
    assert body["total_solicitacoes"] == 1
    assert body["total_culturas_positivas"] == 1
    assert [item["setor"] for item in body["distribuicao_por_setor"]] == ["UTI"]
    assert len(body["taxa_resistencia"]) == 1
    assert body["taxa_resistencia"][0]["antimicrobiano"] == "Antimicrobiano c10"


def test_taxa_positividade_respeita_filtro_de_setor(authenticated_client):
    # UTI: 1 exame positivo (100%). Enfermaria: 1 exame negativo (0%).
    # Geral: 1 de 2 (50%) - confere que a taxa por setor não é só a geral
    # repetida, ela recalcula sobre o subconjunto filtrado.
    setor_uti = criar_setor(authenticated_client, "UTI")
    setor_enf = criar_setor(authenticated_client, "Enfermaria")

    criar_exame(authenticated_client, prontuario="c12", setor_id=setor_uti["id"], status="POSITIVO")
    criar_exame(authenticated_client, prontuario="c13", setor_id=setor_enf["id"], status="NEGATIVO")

    geral = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    uti = authenticated_client.get(
        "/api/ccih/indicadores", params={"setor_id": setor_uti["id"]}
    ).json()["data"]
    enfermaria = authenticated_client.get(
        "/api/ccih/indicadores", params={"setor_id": setor_enf["id"]}
    ).json()["data"]

    assert geral["taxa_positividade"] == 50.0
    assert uti["taxa_positividade"] == 100.0
    assert enfermaria["taxa_positividade"] == 0.0


def test_perfil_microbiologico_calcula_percentual(authenticated_client):
    _fluxo_positivo_com_antibiograma(authenticated_client, "c5", nome_micro="Klebsiella pneumoniae")
    _fluxo_positivo_com_antibiograma(authenticated_client, "c6", nome_micro="Klebsiella pneumoniae")
    _fluxo_positivo_com_antibiograma(authenticated_client, "c7", nome_micro="Escherichia coli")

    body = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    perfil = {p["microrganismo"]: p for p in body["perfil_microbiologico"]}

    assert perfil["Klebsiella pneumoniae"]["quantidade"] == 2
    assert perfil["Klebsiella pneumoniae"]["percentual"] == 66.7
    assert perfil["Escherichia coli"]["quantidade"] == 1


def test_taxa_resistencia(authenticated_client):
    _fluxo_positivo_com_antibiograma(authenticated_client, "c8", resultado_sir="RESISTENTE")

    body = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    assert len(body["taxa_resistencia"]) == 1
    item = body["taxa_resistencia"][0]
    assert item["total_testado"] == 1
    assert item["total_resistente"] == 1
    assert item["percentual_resistente"] == 100.0
    assert item["total_sensivel"] == 0
    assert item["percentual_sensivel"] == 0.0


def test_taxa_sensibilidade_mesmo_antimicrobiano(authenticated_client):
    # Dois exames testados contra o "mesmo" antimicrobiano (mesmo
    # prontuário usado como sufixo do nome) - um resistente, outro
    # sensível - pra conferir que os dois percentuais são calculados
    # sobre o total testado, não isoladamente.
    setor = criar_setor(authenticated_client, "UTI")
    antimicrobiano = criar_antimicrobiano(authenticated_client, "Antimicrobiano c9")
    microrganismo = criar_microrganismo(authenticated_client, "Klebsiella pneumoniae")

    for resultado_sir in ("RESISTENTE", "SENSIVEL"):
        criar_exame(
            authenticated_client,
            prontuario="c9",
            setor_id=setor["id"],
            status="POSITIVO",
            isolados=[
                {
                    "microrganismo_id": microrganismo["id"],
                    "antibiograma": [
                        {"antimicrobiano_id": antimicrobiano["id"], "resultado": resultado_sir}
                    ],
                }
            ],
        )

    body = authenticated_client.get("/api/ccih/indicadores").json()["data"]
    item = next(
        r for r in body["taxa_resistencia"] if r["antimicrobiano"] == "Antimicrobiano c9"
    )
    assert item["total_testado"] == 2
    assert item["total_resistente"] == 1
    assert item["percentual_resistente"] == 50.0
    assert item["total_sensivel"] == 1
    assert item["percentual_sensivel"] == 50.0


def test_periodo_customizado_exclui_dados_fora_do_intervalo(authenticated_client):
    _fluxo_positivo_com_antibiograma(authenticated_client, "c9")

    ontem = date.today() - timedelta(days=1)
    anteontem = date.today() - timedelta(days=2)

    response = authenticated_client.get(
        "/api/ccih/indicadores",
        params={"data_inicio": anteontem.isoformat(), "data_fim": ontem.isoformat()},
    )

    body = response.json()["data"]
    assert body["total_culturas_positivas"] == 0
