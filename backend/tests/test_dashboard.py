"""
Testes do módulo Dashboard (Sprint 8).

Fase 1 (fluxo de Exame unificado): reescrito sobre `/api/exames`. Os
nomes dos campos de saída (`culturas_hoje`, `liberados_hoje`, etc.)
continuam os mesmos por compatibilidade - só a fonte de dados mudou.
"""
from tests.helpers import criar_exame, criar_microrganismo


def test_resumo_dashboard_estrutura_basica(authenticated_client):
    response = authenticated_client.get("/api/dashboard/resumo")
    assert response.status_code == 200
    body = response.json()["data"]
    for campo in (
        "culturas_hoje",
        "aguardando_atualizacao",
        "prazo_vencido",
        "liberados_hoje",
        "top_microrganismos",
        "alertas",
    ):
        assert campo in body


def test_culturas_hoje_conta_exames_criados(authenticated_client):
    criar_exame(authenticated_client, prontuario="d1", status="NEGATIVO")
    criar_exame(authenticated_client, prontuario="d2", status="NEGATIVO")

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    assert body["culturas_hoje"] == 2


def test_aguardando_atualizacao_conta_exames_em_andamento(authenticated_client):
    criar_exame(authenticated_client, prontuario="d3")  # status padrão: AGUARDANDO_TRIAGEM

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    assert body["aguardando_atualizacao"] >= 1


def test_liberados_hoje_conta_exames_finalizados(authenticated_client):
    criado = criar_exame(authenticated_client, prontuario="d4").json()["data"]
    authenticated_client.put(f"/api/exames/{criado['id']}", json={"status": "NEGATIVO"})

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    assert body["liberados_hoje"] == 1


def test_top_microrganismos_reflete_exames_positivos(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client, nome="Klebsiella pneumoniae")
    for prontuario in ("d5", "d6"):
        criar_exame(
            authenticated_client,
            prontuario=prontuario,
            status="POSITIVO_PARCIAL",
            isolados=[{"microrganismo_id": microrganismo["id"]}],
        )

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    nomes = [m["nome"] for m in body["top_microrganismos"]]
    assert "Klebsiella pneumoniae" in nomes


def test_alerta_de_exame_positivo_aguardando_finalizacao(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client, nome="Acinetobacter baumannii")
    criar_exame(
        authenticated_client,
        prontuario="d7",
        status="POSITIVO_PARCIAL",
        isolados=[{"microrganismo_id": microrganismo["id"]}],
    )

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    tipos = [a["tipo"] for a in body["alertas"]]
    assert "info" in tipos
