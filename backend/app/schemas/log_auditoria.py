"""
Schemas de saída dos Logs de Auditoria (Sprint 13).
"""
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LogAuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    usuario_id: uuid.UUID | None
    usuario_login: str | None
    metodo: str
    caminho: str
    status_code: int
    ip_origem: str | None
    criado_em: datetime


class LogAuditoriaListOut(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[LogAuditoriaOut]
