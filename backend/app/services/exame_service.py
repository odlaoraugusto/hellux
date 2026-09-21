"""
Service do fluxo de Exame unificado (Fase 1).

Reescrito para gravar direto na entidade `Exame` (em vez de compor
Solicitação + Cultura como antes) - mas herda o espírito do
`ExameService` anterior: resolve o paciente por prontuário (cria se não
existir) e reaproveita a regra de "só aceita isolados quando o status é
positivo/positivo parcial", que antes vivia em `CulturaService`.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.models.exame import STATUS_POSITIVO, Exame, StatusExameEnum
from app.repositories.exame_repository import ExameRepository
from app.repositories.parametro_sistema_repository import ParametroSistemaRepository
from app.schemas.exame import ExameCreate, ExameUpdate
from app.schemas.paciente import PacienteCreate
from app.services.paciente_service import PacienteService

PRAZO_PADRAO_DIAS_FALLBACK = 2


class ExameService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ExameRepository(db)
        self.paciente_service = PacienteService(db)
        self.parametro_repository = ParametroSistemaRepository(db)

    def listar(
        self,
        status: list[StatusExameEnum] | None,
        paciente_id: uuid.UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ):
        skip = (page - 1) * page_size
        return self.repository.search(
            status=status, paciente_id=paciente_id, skip=skip, limit=page_size
        )

    def obter(self, exame_id: uuid.UUID) -> Exame:
        exame = self.repository.get_by_id(exame_id)
        if not exame or not exame.is_active:
            raise NotFoundError("Exame não encontrado.")
        return exame

    def _resolver_paciente(self, prontuario: str, nome: str):
        """
        Reaproveita o paciente já cadastrado com este prontuário (sem
        sobrescrever o nome original) ou cria um novo na hora - elimina o
        recadastro manual antes de cada exame, já que o paciente já existe
        no sistema do hospital/planilha do usuário.
        """
        try:
            return self.paciente_service.obter_por_prontuario(prontuario)
        except NotFoundError:
            return self.paciente_service.criar(
                PacienteCreate(nome=nome, prontuario=prontuario)
            )

    def _validar_isolados(self, status: StatusExameEnum, isolados: list) -> None:
        if isolados and status not in STATUS_POSITIVO:
            raise BusinessRuleError(
                "Só é possível informar isolados quando o status é "
                "POSITIVO_PARCIAL ou POSITIVO.",
                errors=[f"status '{status.value}' não permite isolados."],
            )

    def _calcular_previsao_padrao(self) -> date:
        prazo_dias = self.parametro_repository.get_valor_int(
            "prazo_solicitacao_dias", PRAZO_PADRAO_DIAS_FALLBACK
        )
        return date.today() + timedelta(days=prazo_dias)

    def criar(self, dados: ExameCreate) -> Exame:
        paciente = self._resolver_paciente(dados.paciente_prontuario, dados.paciente_nome)
        self._validar_isolados(dados.status, dados.isolados)

        exame = self.repository.create(
            {
                "tenant_id": get_current_tenant_id(self.db),
                "paciente_id": paciente.id,
                "setor_id": dados.setor_id,
                "tipo_cultura_id": dados.tipo_cultura_id,
                "material_id": dados.material_id,
                "data_coleta": dados.data_coleta or datetime.now(timezone.utc),
                "previsao_liberacao": dados.previsao_liberacao
                or self._calcular_previsao_padrao(),
                "status": dados.status,
                "identificacao_preliminar": dados.identificacao_preliminar,
                "observacoes": dados.observacoes,
            }
        )

        if dados.isolados:
            self.repository.definir_isolados(exame.id, dados.isolados)

        return self.repository.get_by_id(exame.id)

    def atualizar(self, exame_id: uuid.UUID, dados: ExameUpdate) -> Exame:
        exame = self.obter(exame_id)

        status_final = dados.status or exame.status
        if dados.isolados is not None:
            self._validar_isolados(status_final, dados.isolados)

        dados_dict = dados.model_dump(exclude_unset=True, exclude={"isolados"})
        self.repository.update(exame, dados_dict)

        if dados.isolados is not None:
            self.repository.definir_isolados(exame_id, dados.isolados)

        return self.repository.get_by_id(exame_id)

    def remover(self, exame_id: uuid.UUID) -> None:
        exame = self.obter(exame_id)
        self.repository.soft_delete(exame)

    def calcular_pendencia(self, exame: Exame) -> str:
        """
        Explica, em uma frase curta, por que o exame ainda não foi
        finalizado - usado no relatório de resultados parciais.
        """
        if exame.status == StatusExameEnum.AGUARDANDO_TRIAGEM:
            return "Aguardando triagem inicial"

        if exame.status in STATUS_POSITIVO:
            if not exame.isolados:
                return "Aguardando identificação do microrganismo"
            if self.repository.isolados_sem_antibiograma(exame):
                return "Aguardando antibiograma"
            return "Pronto para finalização"

        # NEGATIVO_PARCIAL não depende de isolado/antibiograma.
        return "Pronto para finalização"

    def resultados_parciais(self) -> list[tuple[Exame, str]]:
        """Exames ainda não finalizados, cada um com sua pendência explicada."""
        exames = self.repository.buscar_parciais()
        return [(exame, self.calcular_pendencia(exame)) for exame in exames]
