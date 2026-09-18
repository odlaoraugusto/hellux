"""
Contrato único de respostas da API Hellux.

Toda resposta da API segue este formato, conforme definido no
Documento Mestre (seção 8 - Padrão da API):

Sucesso:
{
  "success": true,
  "message": "...",
  "data": {}
}

Erro:
{
  "success": false,
  "message": "...",
  "errors": []
}
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "OK"
    data: T | None = None


class ApiErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: list[str] = []


def success_response(data: Any = None, message: str = "OK") -> dict:
    """Monta uma resposta de sucesso seguindo o contrato padrão."""
    return {"success": True, "message": message, "data": data}


def error_response(message: str, errors: list[str] | None = None) -> dict:
    """Monta uma resposta de erro seguindo o contrato padrão."""
    return {"success": False, "message": message, "errors": errors or []}
