"""
Middleware de Auditoria (Sprint 13).

Registra, de forma transversal, toda requisição que altera dados
(POST/PUT/PATCH/DELETE) - sem exigir que cada Service chame algo
manualmente. Isso garante que nenhuma rota nova "esqueça" de logar.

Deliberadamente NÃO loga o corpo da requisição (poderia conter senhas
ou dados sensíveis de paciente) - apenas método, caminho, status,
usuário (se autenticado) e IP de origem.
"""
import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.security import decodificar_access_token
from app.db import session as db_session
from app.models.log_auditoria import LogAuditoria

logger = logging.getLogger("hellux.auditoria")

METODOS_AUDITADOS = {"POST", "PUT", "PATCH", "DELETE"}


def _extrair_usuario_do_token(request: Request) -> tuple[str | None, str | None, str | None]:
    """Decodifica o JWT (se presente) sem consultar o banco - só para o log."""
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.lower().startswith("bearer "):
        return None, None, None

    token = auth_header.split(" ", 1)[1]
    payload = decodificar_access_token(token)
    if not payload:
        return None, None, None

    return payload.get("sub"), payload.get("login"), payload.get("tenant_id")


class AuditoriaMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.method in METODOS_AUDITADOS:
            self._registrar_log(request, response)

        return response

    def _registrar_log(self, request: Request, response) -> None:
        usuario_id, usuario_login, tenant_id = _extrair_usuario_do_token(request)
        ip_origem = request.client.host if request.client else None

        db = db_session.SessionLocal()
        try:
            log = LogAuditoria(
                tenant_id=tenant_id,
                usuario_id=usuario_id,
                usuario_login=usuario_login,
                metodo=request.method,
                caminho=request.url.path,
                status_code=response.status_code,
                ip_origem=ip_origem,
            )
            db.add(log)
            db.commit()
        except Exception:  # nunca deixa uma falha de log derrubar a resposta real
            logger.exception("Falha ao registrar log de auditoria")
            db.rollback()
        finally:
            db.close()
