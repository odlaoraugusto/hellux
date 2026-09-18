"""
Router do módulo CCIH (Sprint 9).
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.services.ccih_service import CCIHService

router = APIRouter(prefix="/api/ccih", tags=["CCIH"], dependencies=[Depends(get_current_user)])


@router.get("/indicadores")
def obter_indicadores_ccih(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    setor_id: uuid.UUID | None = Query(default=None, description="Filtra por setor do exame"),
    db: Session = Depends(get_db),
):
    """Indicadores gerais - todos os exames, exceto os de vigilância."""
    service = CCIHService(db)
    indicadores = service.indicadores(data_inicio, data_fim, setor_id=setor_id)
    return success_response(
        indicadores.model_dump(mode="json"), message="Indicadores da CCIH calculados com sucesso."
    )


@router.get("/indicadores/vigilancia")
def obter_indicadores_ccih_vigilancia(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    setor_id: uuid.UUID | None = Query(default=None, description="Filtra por setor do exame"),
    db: Session = Depends(get_db),
):
    """Indicadores dedicados aos exames de vigilância (rastreio/colonização)."""
    service = CCIHService(db)
    indicadores = service.indicadores_vigilancia(data_inicio, data_fim, setor_id=setor_id)
    return success_response(
        indicadores.model_dump(mode="json"),
        message="Indicadores de vigilância calculados com sucesso.",
    )
