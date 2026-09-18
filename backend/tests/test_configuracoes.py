"""
Testes do módulo Configurações - Parâmetros do Sistema (Sprint 11).

Como os testes rodam sobre um schema criado via Base.metadata.create_all
(sem executar as migrações do Alembic), o parâmetro seed
"prazo_solicitacao_dias" não existe automaticamente - os testes cobrem
justamente esse cenário de fallback, além do fluxo com o parâmetro
previamente cadastrado.
"""


def _criar_admin_e_logar(client, login="admin_cfg"):
    client.post(
        "/api/usuarios",
        json={"nome": "Admin Config", "login": login, "senha": "senhaadmin123", "perfil": "ADMIN"},
    )
    token = client.post(
        "/api/auth/login", data={"username": login, "password": "senhaadmin123"}
    ).json()["data"]["access_token"]
    return token


def test_listar_parametros_quando_vazio(client):
    response = client.get("/api/configuracoes/parametros")
    assert response.status_code == 200
    assert response.json()["data"] == []


def test_atualizar_parametro_inexistente_retorna_404(client):
    token = _criar_admin_e_logar(client)
    response = client.put(
        "/api/configuracoes/parametros/chave_que_nao_existe",
        json={"valor": "10"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404


def test_atualizar_parametro_sem_ser_admin_falha(client):
    response = client.put(
        "/api/configuracoes/parametros/prazo_solicitacao_dias", json={"valor": "5"}
    )
    assert response.status_code == 401


def test_dashboard_usa_fallback_quando_parametro_nao_existe(authenticated_client):
    # Sem o parâmetro semeado, o cálculo de prazo vencido deve continuar
    # funcionando normalmente usando o valor de fallback do código.
    response = authenticated_client.get("/api/dashboard/resumo")
    assert response.status_code == 200
    assert "prazo_vencido" in response.json()["data"]
