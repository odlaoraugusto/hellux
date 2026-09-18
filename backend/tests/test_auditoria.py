"""
Testes do módulo de Auditoria (Sprint 13).
"""


def _criar_admin_e_logar(client, login="admin_audit"):
    client.post(
        "/api/usuarios",
        json={"nome": "Admin Audit", "login": login, "senha": "senhaadmin123", "perfil": "ADMIN"},
    )
    token = client.post(
        "/api/auth/login", data={"username": login, "password": "senhaadmin123"}
    ).json()["data"]["access_token"]
    return token


def test_acoes_de_escrita_geram_log_de_auditoria(client):
    token = _criar_admin_e_logar(client)

    # Essa própria criação de usuário (POST) já deveria ter gerado um log.
    client.post(
        "/api/pacientes",
        json={"nome": "Paciente Auditado", "prontuario": "aud1"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/auditoria/logs", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] >= 2  # criação do admin + criação do paciente
    caminhos = [item["caminho"] for item in body["items"]]
    assert "/api/pacientes" in caminhos


def test_log_registra_metodo_e_status_code(client):
    token = _criar_admin_e_logar(client)
    client.post(
        "/api/pacientes",
        json={"nome": "Paciente Log", "prontuario": "aud2"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/auditoria/logs",
        params={"metodo": "POST"},
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()["data"]
    assert body["total"] >= 1
    for item in body["items"]:
        assert item["metodo"] == "POST"
        assert item["status_code"] in (200, 201, 422)


def test_log_registra_usuario_autenticado(client):
    token = _criar_admin_e_logar(client)
    client.post(
        "/api/pacientes",
        json={"nome": "Paciente Rastreado", "prontuario": "aud3"},
        headers={"Authorization": f"Bearer {token}"},
    )

    response = client.get(
        "/api/auditoria/logs", headers={"Authorization": f"Bearer {token}"}
    )

    body = response.json()["data"]
    logins = [item["usuario_login"] for item in body["items"]]
    assert "admin_audit" in logins


def test_get_nao_gera_log(client):
    token = _criar_admin_e_logar(client)
    client.get("/api/pacientes")

    response = client.get(
        "/api/auditoria/logs", headers={"Authorization": f"Bearer {token}"}
    )
    caminhos_get = [
        item["caminho"]
        for item in response.json()["data"]["items"]
        if item["metodo"] == "GET"
    ]
    assert caminhos_get == []


def test_listar_logs_exige_admin(client):
    response = client.get("/api/auditoria/logs")
    assert response.status_code == 401
