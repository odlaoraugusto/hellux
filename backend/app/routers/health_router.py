"""Router simples de verificação de saúde da API (usado por monitoramento/Docker)."""
from fastapi import APIRouter

from app.core.config import get_settings
from app.core.response import success_response

router = APIRouter(tags=["Health"])
settings = get_settings()


@router.get("/api/health")
def health_check():
    return success_response(
        {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION},
        message="Hellux API operacional.",
    )
