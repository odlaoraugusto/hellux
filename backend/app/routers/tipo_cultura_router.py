"""
Router do catálogo de Tipos de Cultura (Fase 1 - fluxo de Exame unificado).

Substitui o enum fixo `GrupoCulturaEnum` por um catálogo tenant-scoped -
mesmo padrão dos catálogos de Setores/Materiais.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.response import success_response
from app.db.session import get_db
from app.schemas.tipo_cultura import TipoCulturaCreate, TipoCulturaOut, TipoCulturaUpdate
from app.services.tipo_cultura_service import TipoCulturaService

router = APIRouter(
    prefix="/api/tipos-cultura", tags=["Tipos de Cultura"], dependencies=[Depends(get_current_user)]
)


@router.get("")
def listar_tipos_cultura(db: Session = Depends(get_db)):
    service = TipoCulturaService(db)
    itens = service.listar()
    data = {
        "total": len(itens),
        "items": [TipoCulturaOut.model_validate(i).model_dump(mode="json") for i in itens],
    }
    return success_response(data, message="Tipos de cultura listados com sucesso.")


@router.post("", status_code=201)
def criar_tipo_cultura(dados: TipoCulturaCreate, db: Session = Depends(get_db)):
    service = TipoCulturaService(db)
    tipo_cultura = service.criar(dados)
    return success_response(
        TipoCulturaOut.model_validate(tipo_cultura).model_dump(mode="json"),
        message="Tipo de cultura cadastrado com sucesso.",
    )


@router.put("/{tipo_cultura_id}")
def atualizar_tipo_cultura(
    tipo_cultura_id: uuid.UUID, dados: TipoCulturaUpdate, db: Session = Depends(get_db)
):
    service = TipoCulturaService(db)
    tipo_cultura = service.atualizar(tipo_cultura_id, dados)
    return success_response(
        TipoCulturaOut.model_validate(tipo_cultura).model_dump(mode="json"),
        message="Tipo de cultura atualizado com sucesso.",
    )


@router.delete("/{tipo_cultura_id}")
def remover_tipo_cultura(tipo_cultura_id: uuid.UUID, db: Session = Depends(get_db)):
    service = TipoCulturaService(db)
    service.remover(tipo_cultura_id)
    return success_response(message="Tipo de cultura removido com sucesso.")
