"""
Testes do módulo Dashboard (Sprint 8).

Fase 1 (fluxo de Exame unificado): reescrito sobre `/api/exames`. Os
nomes dos campos de saída (`culturas_hoje`, `liberados_hoje`, etc.)
continuam os mesmos por compatibilidade - só a fonte de dados mudou.
Sprint do dashboard redesenhado: acrescenta `total_exames_mes`,
`taxa_positividade_mes`, `por_tipo_cultura`, `por_material` e
`por_setor`, todos calculados sobre o mês corrente.
Sparkline de tendência: acrescenta `tendencia_7_dias`, contagem de
exames criados por dia nos últimos 7 dias corridos (incluindo hoje).
"""
from datetime import date, datetime, timedelta, timezone

from tests.helpers import (
    criar_exame,
    criar_material,
    criar_microrganismo,
    criar_setor,
    criar_tipo_cultura,
)


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
        "total_exames_mes",
        "taxa_positividade_mes",
        "por_tipo_cultura",
        "por_material",
        "por_setor",
        "tendencia_7_dias",
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


def test_estatisticas_mensais_agregam_por_catalogo_e_status(authenticated_client):
    """
    Cenário com 2 tipos de cultura, 2 materiais e 2 setores (+ 1 exame
    sem setor, pro balde "Não classificado"), misturando status
    positivos e não positivos - tudo dentro do mês corrente (a fixture
    `criar_exame` não permite escolher `data_coleta`/`created_at`, então
    todo exame criado no teste já cai automaticamente no mês corrente).
    """
    material_hemo = criar_material(authenticated_client, nome="Hemocultura")
    material_urina = criar_material(authenticated_client, nome="Urina")
    tipo_geral = criar_tipo_cultura(authenticated_client, nome="Cultura Geral")
    tipo_bk = criar_tipo_cultura(authenticated_client, nome="BK")
    setor_uti = criar_setor(authenticated_client, "UTI")
    setor_enfermaria = criar_setor(authenticated_client, "Enfermaria")

    # 1) Cultura Geral + Hemocultura + UTI + POSITIVO
    criar_exame(
        authenticated_client,
        prontuario="m1",
        material_id=material_hemo["id"],
        tipo_cultura_id=tipo_geral["id"],
        setor_id=setor_uti["id"],
        status="POSITIVO",
    )
    # 2) Cultura Geral + Urina + Enfermaria + NEGATIVO
    criar_exame(
        authenticated_client,
        prontuario="m2",
        material_id=material_urina["id"],
        tipo_cultura_id=tipo_geral["id"],
        setor_id=setor_enfermaria["id"],
        status="NEGATIVO",
    )
    # 3) BK + Hemocultura + UTI + POSITIVO_PARCIAL
    criar_exame(
        authenticated_client,
        prontuario="m3",
        material_id=material_hemo["id"],
        tipo_cultura_id=tipo_bk["id"],
        setor_id=setor_uti["id"],
        status="POSITIVO_PARCIAL",
    )
    # 4) BK + Urina + sem setor + NEGATIVO
    criar_exame(
        authenticated_client,
        prontuario="m4",
        material_id=material_urina["id"],
        tipo_cultura_id=tipo_bk["id"],
        status="NEGATIVO",
    )
    # 5) Cultura Geral + Hemocultura + Enfermaria + status padrão (AGUARDANDO_TRIAGEM)
    criar_exame(
        authenticated_client,
        prontuario="m5",
        material_id=material_hemo["id"],
        tipo_cultura_id=tipo_geral["id"],
        setor_id=setor_enfermaria["id"],
    )

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]

    assert body["total_exames_mes"] == 5
    # 2 positivos (POSITIVO + POSITIVO_PARCIAL) em 5 exames = 40%.
    assert body["taxa_positividade_mes"] == 40.0

    por_tipo = {item["nome"]: item["quantidade"] for item in body["por_tipo_cultura"]}
    assert por_tipo["Cultura Geral"] == 3
    assert por_tipo["BK"] == 2

    por_material = {item["nome"]: item["quantidade"] for item in body["por_material"]}
    assert por_material["Hemocultura"] == 3
    assert por_material["Urina"] == 2

    por_setor = {item["nome"]: item["quantidade"] for item in body["por_setor"]}
    assert por_setor["UTI"] == 2
    assert por_setor["Enfermaria"] == 2
    assert por_setor["Não classificado"] == 1


def test_taxa_positividade_mes_zero_sem_exames(authenticated_client):
    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    if body["total_exames_mes"] == 0:
        assert body["taxa_positividade_mes"] == 0.0


def test_tendencia_7_dias_sempre_tem_sete_pontos_mesmo_sem_exames(authenticated_client):
    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    tendencia = body["tendencia_7_dias"]

    assert len(tendencia) == 7
    assert all(item["quantidade"] == 0 for item in tendencia)


def test_tendencia_7_dias_conta_exames_de_hoje_e_vem_ordenada(authenticated_client):
    """
    A fixture `criar_exame` não permite escolher `created_at`, então só
    dá pra controlar com certeza a contagem do dia de hoje - os exames
    de outros testes não vazam pra cá porque a fixture `db_session`
    recria o schema do zero a cada teste (ver `tests/conftest.py`).
    """
    criar_exame(authenticated_client, prontuario="t1", status="NEGATIVO")
    criar_exame(authenticated_client, prontuario="t2", status="NEGATIVO")

    body = authenticated_client.get("/api/dashboard/resumo").json()["data"]
    tendencia = body["tendencia_7_dias"]

    assert len(tendencia) == 7

    datas = [date.fromisoformat(item["data"]) for item in tendencia]
    assert datas == sorted(datas)
    # UTC, não `date.today()` (local) - a API calcula "hoje" em UTC (ver
    # DashboardRepository._hoje_utc()), já que `Exame.created_at` é
    # gravado em UTC. Perto da virada de dia em fusos a oeste de UTC, o
    # dia de calendário local e o UTC divergem - comparar contra o local
    # fazia esse teste falhar sem nenhum bug real na API.
    hoje_utc = datetime.now(timezone.utc).date()
    assert datas[-1] == hoje_utc
    assert datas[0] == hoje_utc - timedelta(days=6)

    hoje = tendencia[-1]
    assert hoje["quantidade"] == 2
