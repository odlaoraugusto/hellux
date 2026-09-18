"""
Service do catálogo de Tipos de Cultura (Fase 1 - fluxo de Exame unificado).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.tipo_cultura_repository import TipoCulturaRepository
from app.schemas.tipo_cultura import TipoCulturaCreate, TipoCulturaUpdate


class TipoCulturaService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TipoCulturaRepository(db)

    def listar(self):
        return self.repository.listar_todos()

    def obter(self, tipo_cultura_id: uuid.UUID):
        tipo_cultura = self.repository.get_by_id(tipo_cultura_id)
        if not tipo_cultura or not tipo_cultura.is_active:
            raise NotFoundError("Tipo de cultura não encontrado.")
        return tipo_cultura

    def criar(self, dados: TipoCulturaCreate):
        existente = self.repository.get_by_nome(dados.nome)
        if existente:
            raise BusinessRuleError(
                "Já existe um tipo de cultura cadastrado com este nome.",
                errors=[f"nome '{dados.nome}' já está em uso."],
            )
        payload = dados.model_dump()
        payload["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(payload)

    def atualizar(self, tipo_cultura_id: uuid.UUID, dados: TipoCulturaUpdate):
        tipo_cultura = self.obter(tipo_cultura_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(tipo_cultura, dados_dict)

    def remover(self, tipo_cultura_id: uuid.UUID):
        tipo_cultura = self.obter(tipo_cultura_id)
        self.repository.soft_delete(tipo_cultura)
