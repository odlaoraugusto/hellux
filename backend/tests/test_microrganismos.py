"""
Testes do catálogo de Microrganismos (Base de Conhecimento).

Extraído de test_microbiologia.py na Fase 1 (fluxo de Exame unificado):
o catálogo de Microrganismos em si não foi removido, só o módulo antigo
de Cultura/CulturaMicrorganismo que vivia no mesmo arquivo de teste (ver
tests/test_exames.py para a cobertura do fluxo de Exame com isolados).
"""


def test_criar_microrganismo_com_sucesso(authenticated_client):
    response = authenticated_client.post(
        "/api/microrganismos",
        json={"nome": "Escherichia coli", "gram": "NEGATIVO", "tipo": "BACTERIA"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["nome"] == "Escherichia coli"


def test_nao_permite_microrganismo_duplicado(authenticated_client):
    authenticated_client.post("/api/microrganismos", json={"nome": "Candida albicans"})
    response = authenticated_client.post("/api/microrganismos", json={"nome": "Candida albicans"})
    assert response.status_code == 422


def test_microrganismo_seedado_com_taxonomia_correta(authenticated_client):
    """
    Confere que os campos de taxonomia (gram/tipo/morfologia/fermentador/
    familia) trafegam corretamente do cadastro até o GET.

    O banco de testes é montado a partir do metadata do SQLAlchemy (ver
    conftest.py), não roda as migrações - aqui reproduzimos os mesmos
    valores que a migração grava em produção pra "Klebsiella pneumoniae"
    e conferimos o roundtrip.
    """
    criado = authenticated_client.post(
        "/api/microrganismos",
        json={
            "nome": "Klebsiella pneumoniae",
            "gram": "NEGATIVO",
            "tipo": "BACTERIA",
            "morfologia": "BACILO",
            "fermentador": True,
            "familia": "Enterobacteriaceae",
        },
    ).json()["data"]

    response = authenticated_client.get("/api/microrganismos", params={"termo": "Klebsiella"})

    assert response.status_code == 200
    item = next(i for i in response.json()["data"]["items"] if i["id"] == criado["id"])
    assert item["gram"] == "NEGATIVO"
    assert item["morfologia"] == "BACILO"
    assert item["fermentador"] is True
    assert item["familia"] == "Enterobacteriaceae"


def test_novo_microrganismo_herda_taxonomia_do_mesmo_genero(authenticated_client):
    """
    "Aprendizado" incremental da base de conhecimento: cadastrar uma nova
    espécie de um gênero já conhecido (sem informar taxonomia) herda
    gram/tipo/morfologia/fermentador/familia do primeiro microrganismo
    ativo desse gênero, em vez de cair nos defaults genéricos.
    """
    authenticated_client.post(
        "/api/microrganismos",
        json={
            "nome": "Klebsiella pneumoniae",
            "gram": "NEGATIVO",
            "tipo": "BACTERIA",
            "morfologia": "BACILO",
            "fermentador": True,
            "familia": "Enterobacteriaceae",
        },
    )

    response = authenticated_client.post(
        "/api/microrganismos", json={"nome": "Klebsiella aerogenes"}
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["gram"] == "NEGATIVO"
    assert body["tipo"] == "BACTERIA"
    assert body["morfologia"] == "BACILO"
    assert body["fermentador"] is True
    assert body["familia"] == "Enterobacteriaceae"


def test_criar_microrganismo_com_campos_explicitos_nao_e_sobrescrito_pela_heranca(
    authenticated_client,
):
    """
    Se o cliente informar a taxonomia explicitamente na criação, a
    herança automática por gênero é pulada - o que foi enviado prevalece,
    mesmo já existindo outro microrganismo do mesmo gênero cadastrado.
    """
    authenticated_client.post(
        "/api/microrganismos",
        json={
            "nome": "Klebsiella pneumoniae",
            "gram": "NEGATIVO",
            "tipo": "BACTERIA",
            "morfologia": "BACILO",
            "fermentador": True,
            "familia": "Enterobacteriaceae",
        },
    )

    response = authenticated_client.post(
        "/api/microrganismos",
        json={
            "nome": "Klebsiella oxytoca",
            "gram": "POSITIVO",
            "morfologia": "COCO",
            "fermentador": False,
            "familia": "Familia Diferente",
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["gram"] == "POSITIVO"
    assert body["morfologia"] == "COCO"
    assert body["fermentador"] is False
    assert body["familia"] == "Familia Diferente"
