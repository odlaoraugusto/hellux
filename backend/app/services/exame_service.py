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
from app.models.exame import (
    STATUS_PAINEL,
    STATUS_POSITIVO,
    Exame,
    MecanismoResistenciaEnum,
    ResultadoSIREnum,
    StatusExameEnum,
)
from app.repositories.exame_repository import ExameRepository
from app.repositories.parametro_sistema_repository import ParametroSistemaRepository
from app.schemas.exame import ExameCreate, ExameUpdate
from app.schemas.paciente import PacienteCreate
from app.services.paciente_service import PacienteService

PRAZO_PADRAO_DIAS_FALLBACK = 2

MECANISMO_LABELS = {
    MecanismoResistenciaEnum.MRSA: "MRSA",
    MecanismoResistenciaEnum.ESBL: "ESBL",
    MecanismoResistenciaEnum.CARBAPENEMASE_KPC: "Carbapenemase (KPC)",
    MecanismoResistenciaEnum.VRE: "VRE",
    MecanismoResistenciaEnum.D_TESTE_POSITIVO: "D-teste positivo",
    MecanismoResistenciaEnum.OUTRO: "Outro",
}


def _unicos(valores: list[str]) -> list[str]:
    """Remove repetidos preservando a ordem de aparição."""
    return list(dict.fromkeys(valores))


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
        # UTC, não `date.today()` (local) - `previsao_liberacao` é depois
        # comparada contra `DashboardRepository._hoje_utc()` pra calcular
        # "prazo vencido"; misturar as duas referências fazia o prazo
        # ficar um dia adiantado/atrasado sempre que o horário local e o
        # UTC caem em dias de calendário diferentes (a maior parte do dia,
        # em qualquer fuso a oeste de UTC).
        return datetime.now(timezone.utc).date() + timedelta(days=prazo_dias)

    def criar(self, dados: ExameCreate) -> Exame:
        paciente = self._resolver_paciente(dados.paciente_prontuario, dados.paciente_nome)
        self._validar_isolados(dados.status, dados.isolados)

        exame = self.repository.create(
            {
                "tenant_id": get_current_tenant_id(self.db),
                "paciente_id": paciente.id,
                "setor_id": dados.setor_id,
                "numero_solicitacao": dados.numero_solicitacao,
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

    def painel_acompanhamento(self, mes: int | None, ano: int | None) -> list[dict]:
        """
        Uma linha "achatada" por exame para o Painel de Acompanhamento:
        microrganismos, antimicrobianos agrupados por resultado (R / S /
        I = sensível com exposição aumentada, BrCAST) e mecanismos de
        resistência de todos os isolados do exame.
        """
        linhas = []
        for exame in self.repository.buscar_por_mes_ano_coleta(mes, ano):
            por_resultado: dict[ResultadoSIREnum, list[str]] = {r: [] for r in ResultadoSIREnum}
            microrganismos, mecanismos = [], []
            for isolado in exame.isolados:
                microrganismos.append(isolado.microrganismo.nome)
                if isolado.mecanismo_resistencia in MECANISMO_LABELS:
                    mecanismos.append(MECANISMO_LABELS[isolado.mecanismo_resistencia])
                for item in isolado.antibiograma:
                    por_resultado[item.resultado].append(item.antimicrobiano.nome)

            linhas.append(
                {
                    "id": exame.id,
                    "prontuario": exame.paciente.prontuario if exame.paciente else None,
                    "paciente_nome": exame.paciente.nome if exame.paciente else None,
                    "numero_solicitacao": exame.numero_solicitacao,
                    "data_coleta": exame.data_coleta,
                    "tipo_cultura": exame.tipo_cultura.nome if exame.tipo_cultura else None,
                    "material": exame.material.nome if exame.material else None,
                    "setor": exame.setor.nome if exame.setor else None,
                    "status": exame.status,
                    "status_painel": STATUS_PAINEL[exame.status],
                    "microrganismos": _unicos(microrganismos),
                    "resistencia": _unicos(por_resultado[ResultadoSIREnum.RESISTENTE]),
                    "sensibilidade": _unicos(por_resultado[ResultadoSIREnum.SENSIVEL]),
                    "sensivel_exposicao_aumentada": _unicos(
                        por_resultado[ResultadoSIREnum.INTERMEDIARIO]
                    ),
                    "mecanismos_resistencia": _unicos(mecanismos),
                }
            )
        return linhas
