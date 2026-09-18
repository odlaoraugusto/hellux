"""
Testes do catálogo de Antimicrobianos (Base de Conhecimento).

Extraído de test_antibiogramas.py na Fase 1 (fluxo de Exame unificado):
o catálogo de Antimicrobianos em si não foi removido, só o módulo antigo
de Antibiograma/AntibiogramaResultado que vivia no mesmo arquivo de
teste (ver tests/test_exames.py para a cobertura do fluxo de Exame com
antibiograma por isolado).
"""


def test_criar_antimicrobiano_com_sucesso(authenticated_client):
    response = authenticated_client.post(
        "/api/antimicrobianos", json={"nome": "Vancomicina", "classe": "Glicopeptídeo"}
    )
    assert response.status_code == 201
    assert response.json()["data"]["nome"] == "Vancomicina"


def test_nao_permite_antimicrobiano_duplicado(authenticated_client):
    authenticated_client.post("/api/antimicrobianos", json={"nome": "Ceftriaxona"})
    response = authenticated_client.post("/api/antimicrobianos", json={"nome": "Ceftriaxona"})
    assert response.status_code == 422
