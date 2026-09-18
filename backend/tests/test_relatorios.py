"""
Testes do módulo Relatórios (Sprint 10).

Como os endpoints retornam arquivos binários (não o contrato JSON
padrão), os testes verificam: status HTTP, content-type, headers de
download e a assinatura binária do arquivo gerado (magic bytes).

Fase 1 (fluxo de Exame unificado): `/api/relatorios/solicitacoes.xlsx`
vira `/api/relatorios/exames.xlsx` e `/api/relatorios/culturas-
parciais.xlsx` vira `/api/relatorios/exames-parciais.xlsx`.
"""
from tests.helpers import criar_exame, criar_microrganismo


def test_exportar_pacientes_excel(authenticated_client):
    authenticated_client.post("/api/pacientes", json={"nome": "Paciente Relatório", "prontuario": "r1"})

    response = authenticated_client.get("/api/relatorios/pacientes.xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert "attachment" in response.headers["content-disposition"]
    # arquivos .xlsx são arquivos ZIP - começam com a assinatura "PK"
    assert response.content[:2] == b"PK"


def test_exportar_exames_excel(authenticated_client):
    criar_exame(authenticated_client, prontuario="r2")

    response = authenticated_client.get("/api/relatorios/exames.xlsx")

    assert response.status_code == 200
    assert response.content[:2] == b"PK"


def test_exportar_exames_parciais_excel(authenticated_client):
    criar_exame(authenticated_client, prontuario="rp1")  # status padrão: AGUARDANDO_TRIAGEM

    response = authenticated_client.get("/api/relatorios/exames-parciais.xlsx")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert response.content[:2] == b"PK"


def test_exportar_ccih_pdf(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client, nome="Micro Relatório")
    criar_exame(
        authenticated_client,
        prontuario="r3",
        status="POSITIVO",
        isolados=[{"microrganismo_id": microrganismo["id"]}],
    )

    response = authenticated_client.get("/api/relatorios/ccih.pdf")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers["content-disposition"]
    # arquivos PDF começam com a assinatura "%PDF"
    assert response.content[:4] == b"%PDF"


def test_exportar_ccih_pdf_com_periodo_customizado(authenticated_client):
    response = authenticated_client.get(
        "/api/relatorios/ccih.pdf",
        params={"data_inicio": "2026-01-01", "data_fim": "2026-01-31"},
    )
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
