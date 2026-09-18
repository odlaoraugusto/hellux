"""
Service do catálogo de Materiais (Sprint 11).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.material_repository import MaterialRepository
from app.schemas.material import MaterialCreate, MaterialUpdate


class MaterialService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MaterialRepository(db)

    def listar(self):
        return self.repository.listar_todos()

    def obter(self, material_id: uuid.UUID):
        material = self.repository.get_by_id(material_id)
        if not material or not material.is_active:
            raise NotFoundError("Material não encontrado.")
        return material

    def criar(self, dados: MaterialCreate):
        existente = self.repository.get_by_nome(dados.nome)
        if existente:
            raise BusinessRuleError(
                "Já existe um material cadastrado com este nome.",
                errors=[f"nome '{dados.nome}' já está em uso."],
            )
        payload = dados.model_dump()
        payload["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(payload)

    def atualizar(self, material_id: uuid.UUID, dados: MaterialUpdate):
        material = self.obter(material_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(material, dados_dict)

    def remover(self, material_id: uuid.UUID):
        material = self.obter(material_id)
        self.repository.soft_delete(material)
