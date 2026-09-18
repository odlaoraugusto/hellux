"""
Service do catálogo de Setores (Sprint 11).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.setor_repository import SetorRepository
from app.schemas.setor import SetorCreate, SetorUpdate


class SetorService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SetorRepository(db)

    def listar(self):
        return self.repository.listar_todos()

    def obter(self, setor_id: uuid.UUID):
        setor = self.repository.get_by_id(setor_id)
        if not setor or not setor.is_active:
            raise NotFoundError("Setor não encontrado.")
        return setor

    def criar(self, dados: SetorCreate):
        existente = self.repository.get_by_nome(dados.nome)
        if existente:
            raise BusinessRuleError(
                "Já existe um setor cadastrado com este nome.",
                errors=[f"nome '{dados.nome}' já está em uso."],
            )
        payload = dados.model_dump()
        payload["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(payload)

    def atualizar(self, setor_id: uuid.UUID, dados: SetorUpdate):
        setor = self.obter(setor_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(setor, dados_dict)

    def remover(self, setor_id: uuid.UUID):
        setor = self.obter(setor_id)
        self.repository.soft_delete(setor)
