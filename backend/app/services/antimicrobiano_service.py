"""
Service do catálogo de Antimicrobianos (Base de Conhecimento).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.antimicrobiano_repository import AntimicrobianoRepository
from app.schemas.antimicrobiano import AntimicrobianoCreate, AntimicrobianoUpdate


class AntimicrobianoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AntimicrobianoRepository(db)

    def listar(self, termo: str | None, page: int = 1, page_size: int = 20):
        skip = (page - 1) * page_size
        return self.repository.search(termo, skip=skip, limit=page_size)

    def obter(self, antimicrobiano_id: uuid.UUID):
        antimicrobiano = self.repository.get_by_id(antimicrobiano_id)
        if not antimicrobiano or not antimicrobiano.is_active:
            raise NotFoundError("Antimicrobiano não encontrado.")
        return antimicrobiano

    def criar(self, dados: AntimicrobianoCreate):
        existente = self.repository.get_by_nome(dados.nome)
        if existente:
            raise BusinessRuleError(
                "Já existe um antimicrobiano cadastrado com este nome.",
                errors=[f"nome '{dados.nome}' já está em uso."],
            )
        payload = dados.model_dump()
        payload["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(payload)

    def atualizar(self, antimicrobiano_id: uuid.UUID, dados: AntimicrobianoUpdate):
        antimicrobiano = self.obter(antimicrobiano_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(antimicrobiano, dados_dict)

    def remover(self, antimicrobiano_id: uuid.UUID):
        antimicrobiano = self.obter(antimicrobiano_id)
        self.repository.soft_delete(antimicrobiano)
