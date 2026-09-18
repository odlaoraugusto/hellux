"""
Testes do módulo Tenants (Fase 1 - fundação multi-tenant, papel SUPER_ADMIN).

O SUPER_ADMIN não pertence a nenhum tenant - gerencia a lista de
tenants (cria/edita/ativa/desativa) e, dentro de cada um, pode cadastrar
usuários informando `tenant_id` explicitamente (os demais perfis nunca
escolhem o tenant, ele é sempre implícito).
"""


def test_super_admin_cria_tenant_com_admin_inicial(super_admin_client):
    response = super_admin_client.post(
        "/api/tenants",
        json={
            "nome_fantasia": "Hospital Novo",
            "admin_nome": "Admin do Hospital",
            "admin_login": "admin.hospital",
            "admin_senha": "senha-admin-123",
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["tenant"]["nome_fantasia"] == "Hospital Novo"
    assert body["tenant"]["ativo"] is True
    assert body["admin"]["perfil"] == "ADMIN"
    assert body["admin"]["login"] == "admin.hospital"

    # o admin recém-criado já consegue logar de verdade.
    login = super_admin_client.post(
        "/api/auth/login", data={"username": "admin.hospital", "password": "senha-admin-123"}
    )
    assert login.status_code == 200


def test_super_admin_lista_e_atualiza_tenants(super_admin_client):
    criado = super_admin_client.post(
        "/api/tenants",
        json={
            "nome_fantasia": "Hospital X",
            "admin_nome": "Admin X",
            "admin_login": "admin.x",
            "admin_senha": "senha-admin-123",
        },
    ).json()["data"]["tenant"]

    listagem = super_admin_client.get("/api/tenants").json()["data"]
    assert listagem["total"] >= 1
    assert any(t["id"] == criado["id"] for t in listagem["items"])

    resposta = super_admin_client.put(f"/api/tenants/{criado['id']}", json={"ativo": False})
    assert resposta.status_code == 200
    assert resposta.json()["data"]["ativo"] is False


def test_super_admin_cadastra_usuario_em_tenant_especifico(super_admin_client):
    tenant = super_admin_client.post(
        "/api/tenants",
        json={
            "nome_fantasia": "Hospital Y",
            "admin_nome": "Admin Y",
            "admin_login": "admin.y",
            "admin_senha": "senha-admin-123",
        },
    ).json()["data"]["tenant"]

    response = super_admin_client.post(
        "/api/usuarios",
        json={
            "nome": "Técnico Y",
            "login": "tecnico.y",
            "senha": "senha-tecnico-123",
            "perfil": "TECNICO",
            "tenant_id": tenant["id"],
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["tenant_id"] == tenant["id"]


def test_super_admin_sem_tenant_id_falha_ao_cadastrar_usuario(super_admin_client):
    response = super_admin_client.post(
        "/api/usuarios",
        json={
            "nome": "Sem Tenant",
            "login": "sem.tenant",
            "senha": "senha-qualquer-123",
            "perfil": "TECNICO",
        },
    )
    assert response.status_code == 422


def test_super_admin_login_sem_tenant_id_no_token(super_admin_client):
    response = super_admin_client.get("/api/auth/me")
    assert response.status_code == 200
    assert response.json()["data"]["perfil"] == "SUPER_ADMIN"


def test_usuario_comum_nao_acessa_listagem_de_tenants(authenticated_client):
    response = authenticated_client.get("/api/tenants")
    assert response.status_code == 403


def test_usuario_comum_nao_cria_tenant(authenticated_client):
    response = authenticated_client.post(
        "/api/tenants",
        json={
            "nome_fantasia": "Não deveria existir",
            "admin_nome": "A",
            "admin_login": "a.b",
            "admin_senha": "senha-qualquer-123",
        },
    )
    assert response.status_code == 403


def test_anonimo_nao_acessa_endpoints_de_tenant(client):
    response = client.get("/api/tenants")
    assert response.status_code == 401


def test_usuario_comum_nao_cria_super_admin(authenticated_client):
    response = authenticated_client.post(
        "/api/usuarios",
        json={
            "nome": "Outro Root",
            "login": "outro.root",
            "senha": "senha-qualquer-123",
            "perfil": "SUPER_ADMIN",
        },
    )
    assert response.status_code == 403
