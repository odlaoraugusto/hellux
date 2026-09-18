"""
Ponto de entrada da API Hellux.

Fluxo de arquitetura (Documento Mestre, seção 4):
Frontend -> Router -> Service -> Repository -> PostgreSQL
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.audit_middleware import AuditoriaMiddleware
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import limiter
from app.core.security_headers import SecurityHeadersMiddleware
from app.routers import (
    antimicrobiano_router,
    auth_router,
    ccih_router,
    configuracao_router,
    dashboard_router,
    exame_router,
    health_router,
    log_auditoria_router,
    material_router,
    microrganismo_router,
    paciente_router,
    relatorio_router,
    setor_router,
    tenant_router,
    tipo_cultura_router,
    usuario_router,
)

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "API do Hellux - Sistema Inteligente de Gestão Microbiológica. "
        "Plataforma para gestão da microbiologia hospitalar, do cadastro de "
        "pacientes à geração de indicadores epidemiológicos e apoio à CCIH."
    ),
)

# CORS - permite que o frontend (React/Vite) consuma a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auditoria - registra automaticamente toda ação de escrita (Sprint 13)
app.add_middleware(AuditoriaMiddleware)

# Headers de segurança defensivos (Sprint 14)
app.add_middleware(SecurityHeadersMiddleware)

# Rate limiting (Sprint 15) - o Limiter fica em app.state para o decorator
# @limiter.limit(...) usado nas rotas conseguir localizá-lo em tempo de
# requisição; o handler de RateLimitExceeded é registrado junto com os
# demais em register_exception_handlers.
app.state.limiter = limiter

register_exception_handlers(app)


@app.on_event("startup")
def verificar_configuracao_de_producao() -> None:
    """
    Rede de segurança (Sprint 14): impede que a aplicação suba em modo
    "production" usando o SECRET_KEY padrão do repositório, o que
    invalidaria toda a segurança dos tokens JWT emitidos.
    """
    if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "change-me-in-production":
        raise RuntimeError(
            "SECRET_KEY ainda está com o valor padrão em um ambiente de produção. "
            "Defina uma SECRET_KEY forte e única na variável de ambiente antes de "
            "iniciar o servidor (ex.: `openssl rand -hex 32`)."
        )

# Módulos ativos
app.include_router(health_router.router)
app.include_router(paciente_router.router)
app.include_router(microrganismo_router.router)
app.include_router(exame_router.router)
app.include_router(antimicrobiano_router.router)
app.include_router(setor_router.router)
app.include_router(material_router.router)
app.include_router(tipo_cultura_router.router)
app.include_router(dashboard_router.router)
app.include_router(ccih_router.router)
app.include_router(relatorio_router.router)
app.include_router(auth_router.router)
app.include_router(usuario_router.router)
app.include_router(tenant_router.router)
app.include_router(configuracao_router.router)
app.include_router(log_auditoria_router.router)


@app.get("/")
def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
