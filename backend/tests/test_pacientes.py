"""
Testes do módulo Pacientes.

Cobrem o fluxo principal do CRUD e a regra de negócio de prontuário
único, conforme Sprint 2 e Sprint 3 (Robustez da API) do roadmap.
"""


def test_criar_paciente_com_sucesso(authenticated_client):
    payload = {
        "nome": "João da Silva",
        "prontuario": "54321",
        "sexo": "MASCULINO",
        "setor": "UTI",
    }
    response = authenticated_client.post("/api/pacientes", json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["nome"] == "João da Silva"
    assert body["data"]["prontuario"] == "54321"


def test_nao_permite_prontuario_duplicado(authenticated_client):
    payload = {"nome": "Paciente A", "prontuario": "111"}
    authenticated_client.post("/api/pacientes", json=payload)

    response = authenticated_client.post(
        "/api/pacientes", json={"nome": "Paciente B", "prontuario": "111"}
    )

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "prontuário" in body["message"].lower()


def test_listar_pacientes(authenticated_client):
    authenticated_client.post("/api/pacientes", json={"nome": "Ana Souza", "prontuario": "222"})
    authenticated_client.post("/api/pacientes", json={"nome": "Carlos Lima", "prontuario": "333"})

    response = authenticated_client.get("/api/pacientes")

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["total"] == 2
    assert len(body["data"]["items"]) == 2


def test_buscar_paciente_por_termo(authenticated_client):
    authenticated_client.post("/api/pacientes", json={"nome": "Fernanda Costa", "prontuario": "444"})
    authenticated_client.post("/api/pacientes", json={"nome": "Ana Souza", "prontuario": "555"})

    response = authenticated_client.get("/api/pacientes", params={"termo": "Fernanda"})

    body = response.json()
    assert body["data"]["total"] == 1
    assert body["data"]["items"][0]["nome"] == "Fernanda Costa"


def test_obter_paciente_inexistente_retorna_404(authenticated_client):
    response = authenticated_client.get("/api/pacientes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
    assert response.json()["success"] is False


def test_atualizar_paciente(authenticated_client):
    criado = authenticated_client.post(
        "/api/pacientes", json={"nome": "Marcos Reis", "prontuario": "666"}
    ).json()["data"]

    response = authenticated_client.put(
        f"/api/pacientes/{criado['id']}",
        json={"leito": "302-B"},
    )

    assert response.status_code == 200
    assert response.json()["data"]["leito"] == "302-B"


def test_remover_paciente_soft_delete(authenticated_client):
    criado = authenticated_client.post(
        "/api/pacientes", json={"nome": "Paula Nunes", "prontuario": "777"}
    ).json()["data"]

    response = authenticated_client.delete(f"/api/pacientes/{criado['id']}")
    assert response.status_code == 200

    consulta = authenticated_client.get(f"/api/pacientes/{criado['id']}")
    assert consulta.status_code == 404
