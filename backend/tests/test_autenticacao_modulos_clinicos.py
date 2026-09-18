"""
Testes que confirmam o travamento de autenticação dos módulos clínicos
(Sprint 14 - Preparação para Produção).

Cada módulo clínico deve responder 401 quando acessado sem um token
válido. O comportamento "com token funciona" já é coberto pelos testes
de cada módulo (que agora usam a fixture `authenticated_client`) - aqui
o foco é garantir que a porta continua fechada por padrão.
"""
import pytest

ENDPOINTS_PROTEGIDOS = [
    ("GET", "/api/pacientes"),
    ("GET", "/api/exames"),
    ("GET", "/api/microrganismos"),
    ("GET", "/api/antimicrobianos"),
    ("GET", "/api/tipos-cultura"),
    ("GET", "/api/dashboard/resumo"),
    ("GET", "/api/ccih/indicadores"),
    ("GET", "/api/relatorios/pacientes.xlsx"),
]


@pytest.mark.parametrize("metodo,caminho", ENDPOINTS_PROTEGIDOS)
def test_endpoint_clinico_exige_autenticacao(client, metodo, caminho):
    response = client.request(metodo, caminho)
    assert response.status_code == 401, f"{metodo} {caminho} deveria exigir login"


def test_endpoint_clinico_rejeita_token_invalido(client):
    response = client.get(
        "/api/pacientes", headers={"Authorization": "Bearer token-forjado-invalido"}
    )
    assert response.status_code == 401


def test_endpoint_clinico_funciona_com_token_valido(authenticated_client):
    response = authenticated_client.get("/api/pacientes")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_health_check_continua_aberto_sem_autenticacao(client):
    """O health check precisa continuar público (usado pelo Docker healthcheck)."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_login_continua_aberto_sem_autenticacao(client):
    """O próprio endpoint de login obviamente não pode exigir login."""
    response = client.post(
        "/api/auth/login", data={"username": "x@x.com", "password": "errada"}
    )
    # 401 por credenciais inválidas é esperado aqui - o importante é que
    # NÃO seja bloqueado antes disso por falta de token (o que voltaria
    # com uma mensagem diferente, de sessão em vez de credenciais).
    assert response.status_code == 401
    assert "senha" in response.json()["message"].lower() or "e-mail" in response.json()["message"].lower()
