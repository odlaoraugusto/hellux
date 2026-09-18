"""
Testes do módulo de Autenticação e Usuários (Sprint 12).
"""


def _criar_primeiro_usuario(client, login="admin", senha="senha12345"):
    """O primeiro usuário do sistema é sempre promovido a ADMIN."""
    return client.post(
        "/api/usuarios",
        json={"nome": "Admin", "login": login, "senha": senha, "perfil": "VISUALIZADOR"},
    ).json()["data"]


def _login(client, login="admin", senha="senha12345"):
    response = client.post(
        "/api/auth/login", data={"username": login, "password": senha}
    )
    return response.json()["data"]["access_token"]


def test_primeiro_usuario_criado_sem_auth_vira_admin(client):
    usuario = _criar_primeiro_usuario(client)
    assert usuario["perfil"] == "ADMIN"


def test_criar_segundo_usuario_sem_token_falha(client):
    _criar_primeiro_usuario(client)

    response = client.post(
        "/api/usuarios",
        json={
            "nome": "Técnico",
            "login": "tecnico",
            "senha": "outrasenha123",
            "perfil": "TECNICO",
        },
    )
    assert response.status_code == 401


def test_criar_segundo_usuario_com_admin_funciona(client):
    _criar_primeiro_usuario(client)
    token = _login(client)

    response = client.post(
        "/api/usuarios",
        json={
            "nome": "Técnico",
            "login": "tecnico",
            "senha": "outrasenha123",
            "perfil": "TECNICO",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 201
    assert response.json()["data"]["perfil"] == "TECNICO"


def test_login_com_senha_errada_falha(client):
    _criar_primeiro_usuario(client)

    response = client.post(
        "/api/auth/login", data={"username": "admin", "password": "senha_errada"}
    )
    assert response.status_code == 401


def test_login_com_sucesso_retorna_token(client):
    _criar_primeiro_usuario(client)
    token = _login(client)
    assert isinstance(token, str) and len(token) > 10


def test_me_retorna_usuario_autenticado(client):
    _criar_primeiro_usuario(client)
    token = _login(client)

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["data"]["login"] == "admin"


def test_me_sem_token_falha(client):
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_listar_usuarios_exige_admin(client):
    _criar_primeiro_usuario(client)
    token_admin = _login(client)
    client.post(
        "/api/usuarios",
        json={
            "nome": "Visualizador",
            "login": "visu",
            "senha": "senhavisu123",
            "perfil": "VISUALIZADOR",
        },
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    token_visualizador = _login(client, login="visu", senha="senhavisu123")

    response_admin = client.get(
        "/api/usuarios", headers={"Authorization": f"Bearer {token_admin}"}
    )
    response_visualizador = client.get(
        "/api/usuarios", headers={"Authorization": f"Bearer {token_visualizador}"}
    )

    assert response_admin.status_code == 200
    assert response_admin.json()["data"]["total"] == 2
    assert response_visualizador.status_code == 403


def test_nao_permite_login_duplicado(client):
    _criar_primeiro_usuario(client)
    token = _login(client)

    response = client.post(
        "/api/usuarios",
        json={
            "nome": "Duplicado",
            "login": "admin",
            "senha": "outrasenha123",
            "perfil": "TECNICO",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_login_nao_interpreta_wildcard_de_like(client):
    """
    O login vem via OAuth2PasswordRequestForm (sem validação de formato),
    então "%" e "_" digitados no username não podem virar wildcard de SQL
    LIKE - senão um username como "admin_teste" casaria com "admin.teste"
    E com "adminXteste" ao mesmo tempo (o "_" do LIKE bate com qualquer
    caractere único), autenticando numa conta que a pessoa nem sequer
    digitou corretamente.
    """
    admin = _criar_primeiro_usuario(client, login="admin.teste", senha="senha12345")
    token_admin = _login(client, login="admin.teste", senha="senha12345")

    client.post(
        "/api/usuarios",
        json={
            "nome": "Outro Usuário",
            "login": "adminXteste",
            "senha": "outrasenha123",
            "perfil": "TECNICO",
        },
        headers={"Authorization": f"Bearer {token_admin}"},
    )

    # "_" no lugar do "."/"X" - sob .ilike() isso seria wildcard e casaria
    # com as duas contas criadas acima. Com comparação exata, não deve
    # autenticar em nenhuma delas.
    resposta_com_senha_do_admin = client.post(
        "/api/auth/login",
        data={"username": "admin_teste", "password": "senha12345"},
    )
    resposta_com_senha_do_outro = client.post(
        "/api/auth/login",
        data={"username": "admin_teste", "password": "outrasenha123"},
    )

    assert admin["login"] == "admin.teste"
    assert resposta_com_senha_do_admin.status_code == 401
    assert resposta_com_senha_do_outro.status_code == 401


def test_login_com_muitas_tentativas_seguidas_retorna_429(client):
    """
    Rate limit de força bruta no login: 5 tentativas por minuto por IP
    (ver app/core/rate_limit.py e o decorator @limiter.limit em
    auth_router.py). A 6ª tentativa dentro da mesma janela deve ser
    barrada com 429, sem sequer chegar a validar a senha.
    """
    _criar_primeiro_usuario(client)

    respostas = [
        client.post(
            "/api/auth/login",
            data={"username": "admin", "password": "senha_errada"},
        )
        for _ in range(6)
    ]

    assert [r.status_code for r in respostas[:5]] == [401, 401, 401, 401, 401]

    ultima = respostas[5]
    assert ultima.status_code == 429
    corpo = ultima.json()
    assert corpo["success"] is False
    assert "Muitas tentativas de login" in corpo["message"]
