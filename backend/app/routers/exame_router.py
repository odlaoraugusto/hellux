"""
Router do fluxo de Exame unificado (Fase 1).

Cadastra um exame microbiológico completo (paciente resolvido por
prontuário + pedido + resultado + isolados + antibiograma) numa única
chamada - eliminando as telas sequenciais de Solicitação/Microbiologia/
Antibiograma do fluxo antigo (removidas nesta mesma fase, ver
docs/plano).
"""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.models.exame import StatusExameEnum
from app.schemas.exame import ExameCreate, ExameOut, ExameUpdate
from app.services.exame_service import ExameService

router = APIRouter(prefix="/api/exames", tags=["Exames"], dependencies=[Depends(get_current_user)])


@router.get("")
def listar_exames(
    status: StatusExameEnum | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = ExameService(db)
    items, total = service.listar(status, page=page, page_size=page_size)
    data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [ExameOut.model_validate(item).model_dump(mode="json") for item in items],
    }
    return success_response(data, message="Exames listados com sucesso.")


@router.get("/{exame_id}")
def obter_exame(exame_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ExameService(db)
    exame = service.obter(exame_id)
    return success_response(
        ExameOut.model_validate(exame).model_dump(mode="json"),
        message="Exame encontrado.",
    )


@router.post("", status_code=201)
def criar_exame(dados: ExameCreate, db: Session = Depends(get_db)):
    service = ExameService(db)
    exame = service.criar(dados)
    return success_response(
        ExameOut.model_validate(exame).model_dump(mode="json"),
        message="Exame cadastrado com sucesso.",
    )


@router.put("/{exame_id}")
def atualizar_exame(exame_id: uuid.UUID, dados: ExameUpdate, db: Session = Depends(get_db)):
    service = ExameService(db)
    exame = service.atualizar(exame_id, dados)
    return success_response(
        ExameOut.model_validate(exame).model_dump(mode="json"),
        message="Exame atualizado com sucesso.",
    )


@router.delete("/{exame_id}")
def remover_exame(exame_id: uuid.UUID, db: Session = Depends(get_db)):
    service = ExameService(db)
    service.remover(exame_id)
    return success_response(message="Exame removido com sucesso.")
