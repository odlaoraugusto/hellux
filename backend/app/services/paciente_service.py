"""
Service do módulo Pacientes.

Concentra as regras de negócio: validação de prontuário duplicado,
orquestração entre repository e schemas, etc. O Router nunca acessa o
banco diretamente - sempre passa pelo Service.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.paciente_repository import PacienteRepository
from app.schemas.paciente import PacienteCreate, PacienteUpdate


class PacienteService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PacienteRepository(db)

    def listar(self, termo: str | None, page: int = 1, page_size: int = 20):
        skip = (page - 1) * page_size
        items, total = self.repository.search(termo, skip=skip, limit=page_size)
        return items, total

    def obter(self, paciente_id: uuid.UUID):
        paciente = self.repository.get_by_id(paciente_id)
        if not paciente or not paciente.is_active:
            raise NotFoundError("Paciente não encontrado.")
        return paciente

    def obter_por_prontuario(self, prontuario: str):
        paciente = self.repository.get_by_prontuario(prontuario)
        if not paciente:
            raise NotFoundError("Paciente não encontrado para este prontuário.")
        return paciente

    def criar(self, dados: PacienteCreate):
        existente = self.repository.get_by_prontuario(dados.prontuario)
        if existente:
            raise BusinessRuleError(
                "Já existe um paciente cadastrado com este número de prontuário.",
                errors=[f"prontuario '{dados.prontuario}' já está em uso."],
            )
        payload = dados.model_dump()
        payload["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(payload)

    def atualizar(self, paciente_id: uuid.UUID, dados: PacienteUpdate):
        paciente = self.obter(paciente_id)

        novo_prontuario = dados.prontuario
        if novo_prontuario and novo_prontuario != paciente.prontuario:
            existente = self.repository.get_by_prontuario(novo_prontuario)
            if existente:
                raise BusinessRuleError(
                    "Já existe um paciente cadastrado com este número de prontuário.",
                    errors=[f"prontuario '{novo_prontuario}' já está em uso."],
                )

        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(paciente, dados_dict)

    def remover(self, paciente_id: uuid.UUID):
        paciente = self.obter(paciente_id)
        self.repository.soft_delete(paciente)
