"""
Exceções de domínio e handlers globais.

Garantem que qualquer erro da aplicação (esperado ou inesperado) seja
devolvido ao frontend no mesmo contrato padrão de resposta da API.
"""
import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.response import error_response

logger = logging.getLogger("hellux.erros")


class NotFoundError(Exception):
    """Levantada quando um recurso não é encontrado (ex.: paciente inexistente)."""

    def __init__(self, message: str = "Recurso não encontrado"):
        self.message = message
        super().__init__(message)


class BusinessRuleError(Exception):
    """Levantada quando uma regra de negócio é violada."""

    def __init__(self, message: str, errors: list[str] | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(message)


class AuthenticationError(Exception):
    """Levantada quando credenciais de login são inválidas (HTTP 401)."""

    def __init__(self, message: str = "E-mail ou senha inválidos."):
        self.message = message
        super().__init__(message)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=error_response(exc.message),
        )

    @app.exception_handler(AuthenticationError)
    async def authentication_error_handler(request: Request, exc: AuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=error_response(exc.message),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(BusinessRuleError)
    async def business_rule_handler(request: Request, exc: BusinessRuleError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response(exc.message, exc.errors),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        errors = [
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response("Erro de validação nos dados enviados.", errors),
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=error_response(
                "Muitas tentativas de login. Tente novamente em instantes."
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Loga o stack trace completo no servidor para investigação futura -
        # o cliente continua recebendo só a mensagem genérica abaixo, sem
        # vazar detalhe nenhum da exceção (stack trace, query, etc.).
        logger.exception(
            "Erro não tratado em %s %s", request.method, request.url.path
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response("Erro interno no servidor."),
        )
