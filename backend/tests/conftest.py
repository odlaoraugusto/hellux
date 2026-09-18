"""
Fixtures compartilhadas dos testes.

Usa SQLite em memória para os testes rodarem rápido e sem depender de
um PostgreSQL real. Como o SQLite não suporta os tipos Enum/UUID do
Postgres da mesma forma, isso é suficiente para testar as camadas de
Service/Router; testes de integração completos devem rodar contra
Postgres (ver docs/testes.md).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.db.session as db_session_module
from app.core.rate_limit import limiter
from app.db.session import Base, get_db
from app.main import app

SQLALCHEMY_TEST_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    """
    Zera o storage (em memória) do rate limiter de login antes de cada
    teste.

    Sem isso, o limite de "5/minute" configurado no endpoint de login
    (ver app/core/rate_limit.py) é global por IP dentro do processo -
    como a suíte inteira faz dezenas de logins (fixture
    `authenticated_client` é usada em quase todo teste de módulo
    clínico), sem reset ela estouraria o limite em algum teste no meio
    do caminho e derrubaria a suíte inteira com 429s inesperados. O
    teste que valida o rate limit em si (`test_login_com_muitas_tentativas_retorna_429`
    em test_auth.py) também depende desse reset para começar cada
    execução com a cota zerada.
    """
    limiter.reset()
    yield


@pytest.fixture()
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # O middleware de auditoria abre sua própria sessão (fora do sistema
    # de Depends do FastAPI), então precisa apontar para o mesmo banco
    # de testes - não para o Postgres real configurado em produção.
    session_local_original = db_session_module.SessionLocal
    db_session_module.SessionLocal = TestingSessionLocal

    with TestClient(app) as test_client:
        yield test_client

    db_session_module.SessionLocal = session_local_original
    app.dependency_overrides.clear()


@pytest.fixture()
def tenant(db_session):
    """
    Cria um tenant direto no banco de testes (não existe endpoint de
    self-service de tenant - ver app/routers/tenant_router.py, restrito a
    SUPER_ADMIN). Fase 1 (fundação multi-tenant): toda fixture que cria
    usuário/dado de negócio precisa de um tenant já existente ANTES.
    """
    from app.models.tenant import Tenant

    tenant_obj = Tenant(nome_fantasia="Hospital de Teste")
    db_session.add(tenant_obj)
    db_session.commit()
    db_session.refresh(tenant_obj)
    return tenant_obj


@pytest.fixture()
def authenticated_client(client, tenant):
    """
    Mesmo TestClient da fixture `client`, mas já autenticado.

    Cria o primeiro usuário do tenant de teste (que vira ADMIN
    automaticamente, ver UsuarioService) e anexa o token JWT como header
    padrão em todas as próximas requisições feitas com esse client -
    usado pelos testes dos módulos clínicos, que agora exigem login (ver
    core/deps.py). Como já existe um tenant (fixture `tenant`, criado
    ANTES do usuário), o cadastro aberto de usuário o resolve
    automaticamente (ver UsuarioService.resolver_tenant_bootstrap).
    """
    client.post(
        "/api/usuarios",
        json={
            "nome": "Usuário de Teste",
            "login": "teste",
            "senha": "senha-de-teste-123",
            "perfil": "ADMIN",
        },
    )
    resposta_login = client.post(
        "/api/auth/login",
        data={"username": "teste", "password": "senha-de-teste-123"},
    )
    token = resposta_login.json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture()
def super_admin_client(client, db_session):
    """
    Mesmo TestClient da fixture `client`, mas autenticado como SUPER_ADMIN.

    Não existe endpoint HTTP pra criar o primeiro SUPER_ADMIN do sistema
    (só o script `scripts/bootstrap_tenant.py --super-admin` ou outro
    SUPER_ADMIN já autenticado podem cadastrar um - ver
    app/routers/usuario_router.py) - o teste replica o mesmo efeito
    chamando o Service diretamente, e loga normalmente pela API depois.
    """
    from app.core.tenant_context import set_tenant_context
    from app.schemas.usuario import UsuarioCreate
    from app.services.usuario_service import UsuarioService

    set_tenant_context(db_session, None, is_super_admin=True)
    UsuarioService(db_session).criar_super_admin(
        UsuarioCreate(
            nome="Root", login="root", senha="senha-super-admin-123", perfil="SUPER_ADMIN"
        )
    )

    resposta_login = client.post(
        "/api/auth/login", data={"username": "root", "password": "senha-super-admin-123"}
    )
    token = resposta_login.json()["data"]["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client
