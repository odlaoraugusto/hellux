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
    tipo_cultura_id: list[uuid.UUID] | None = Query(
        default=None,
        description="Filtra por um ou mais tipos de cultura do catálogo (?tipo_cultura_id=X&tipo_cultura_id=Y). Omitir traz todos.",
    ),
    db: Session = Depends(get_db),
):
    """Indicadores gerais, opcionalmente filtrados por setor e/ou tipo(s) de cultura."""
    service = CCIHService(db)
    indicadores = service.indicadores(
        data_inicio, data_fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_id
    )
    return success_response(
        indicadores.model_dump(mode="json"), message="Indicadores da CCIH calculados com sucesso."
    )


@router.get("/matriz-sensibilidade")
def obter_matriz_sensibilidade(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    apenas_vigilancia: bool | None = Query(
        default=False,
        description="False (padrão) exclui exames de vigilância, True traz "
        "somente vigilância, omitir o parâmetro como nulo remove o filtro.",
    ),
    db: Session = Depends(get_db),
):
    """
    Matriz de Sensibilidade CCIH: agrupa os resultados de antibiograma por
    macro-grupo de setor x família fenotípica de microrganismo x
    antimicrobiano, com os três percentuais S/I/R. Endpoint aditivo -
    não substitui `/indicadores` nem `/indicadores/vigilancia`.
    """
    service = CCIHService(db)
    matriz = service.matriz_sensibilidade(
        data_inicio, data_fim, apenas_vigilancia=apenas_vigilancia
    )
    return success_response(
        matriz.model_dump(mode="json"),
        message="Matriz de sensibilidade calculada com sucesso.",
    )
