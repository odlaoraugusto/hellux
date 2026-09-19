"""
Repository do Dashboard.

Concentra consultas agregadas (contagens, agrupamentos) usadas para
montar o resumo do Dashboard (Sprint 8). Não segue o padrão de
BaseRepository porque não representa uma entidade única, e sim uma
combinação de leituras sobre várias tabelas.

Fase 1 (fluxo de Exame unificado): reescrito sobre `Exame`/`ExameIsolado`
no lugar de `Solicitacao`/`Cultura`/`CulturaMicrorganismo`. Como o exame
não tem mais um flag `liberado_tecnicamente` separado (o status agora
carrega essa informação - ver app/models/exame.py), "liberado hoje" vira
"virou status final hoje" (checado via `updated_at`, já que não existe
mais uma coluna dedicada de data de liberação).
"""
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exame import (
    STATUS_EM_ANDAMENTO,
    STATUS_FINAIS,
    STATUS_POSITIVO,
    Exame,
    ExameIsolado,
    StatusExameEnum,
)
from app.models.material import Material
from app.models.microrganismo import Microrganismo
from app.models.setor import Setor
from app.models.tipo_cultura import TipoCultura
from app.repositories.parametro_sistema_repository import ParametroSistemaRepository

# Valor de fallback caso o parâmetro "prazo_solicitacao_dias" ainda não
# tenha sido semeado no banco (ex.: testes que criam schema sem migração).
PRAZO_PADRAO_DIAS_FALLBACK = 2

# Rótulo usado quando o exame não tem setor (`Exame.setor_id` é
# nullable) - mesmo espírito de `CCIHRepository.SETOR_NAO_INFORMADO`,
# texto diferente porque aqui o campo é "não classificado" no gráfico
# de distribuição mensal (não um filtro do módulo CCIH).
SETOR_NAO_CLASSIFICADO = "Não classificado"


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def _hoje_utc(self) -> date:
        return datetime.now(timezone.utc).date()

    def _inicio_mes_utc(self) -> date:
        return self._hoje_utc().replace(day=1)

    def _filtro_mes_corrente(self, stmt):
        """
        Restringe `stmt` ao mês corrente (dia 1 até hoje), usando
        `Exame.created_at` como referência temporal - mesmo campo já
        usado por `contar_exames_criados_hoje`, pra manter os números
        do card "hoje" e os agregados mensais consistentes entre si.
        """
        inicio_mes = self._inicio_mes_utc()
        hoje = self._hoje_utc()
        return stmt.where(
            func.date(Exame.created_at) >= inicio_mes,
            func.date(Exame.created_at) <= hoje,
        )

    def contar_exames_criados_hoje(self) -> int:
        hoje = self._hoje_utc()
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True), func.date(Exame.created_at) == hoje
        )
        return self.db.scalar(stmt) or 0

    def contar_exames_em_andamento(self) -> int:
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True), Exame.status.in_(STATUS_EM_ANDAMENTO)
        )
        return self.db.scalar(stmt) or 0

    def contar_exames_com_prazo_vencido(self) -> int:
        prazo_dias = ParametroSistemaRepository(self.db).get_valor_int(
            "prazo_solicitacao_dias", PRAZO_PADRAO_DIAS_FALLBACK
        )
        limite = self._hoje_utc() - timedelta(days=prazo_dias)
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True),
            Exame.status.in_(STATUS_EM_ANDAMENTO),
            Exame.previsao_liberacao <= limite,
        )
        return self.db.scalar(stmt) or 0

    def contar_exames_finalizados_hoje(self) -> int:
        hoje = self._hoje_utc()
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True),
            Exame.status.in_(STATUS_FINAIS),
            func.date(Exame.updated_at) == hoje,
        )
        return self.db.scalar(stmt) or 0

    def top_microrganismos(self, dias: int = 30, limite: int = 5) -> list[tuple[str, int]]:
        desde = datetime.now(timezone.utc) - timedelta(days=dias)
        stmt = (
            select(Microrganismo.nome, func.count(ExameIsolado.id).label("qtd"))
            .join(ExameIsolado, ExameIsolado.microrganismo_id == Microrganismo.id)
            .join(Exame, Exame.id == ExameIsolado.exame_id)
            .where(Exame.is_active.is_(True), Exame.created_at >= desde)
            .group_by(Microrganismo.nome)
            .order_by(func.count(ExameIsolado.id).desc())
            .limit(limite)
        )
        return list(self.db.execute(stmt).all())

    def exames_positivos_aguardando_finalizacao(self) -> int:
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True),
            Exame.status == StatusExameEnum.POSITIVO_PARCIAL,
        )
        return self.db.scalar(stmt) or 0

    def contar_exames_mes(self) -> int:
        stmt = self._filtro_mes_corrente(
            select(func.count(Exame.id)).where(Exame.is_active.is_(True))
        )
        return self.db.scalar(stmt) or 0

    def contar_exames_positivos_mes(self) -> int:
        stmt = self._filtro_mes_corrente(
            select(func.count(Exame.id)).where(
                Exame.is_active.is_(True), Exame.status.in_(STATUS_POSITIVO)
            )
        )
        return self.db.scalar(stmt) or 0

    def exames_por_tipo_cultura_mes(self) -> list[tuple[str, int]]:
        stmt = self._filtro_mes_corrente(
            select(TipoCultura.nome, func.count(Exame.id))
            .select_from(Exame)
            .join(TipoCultura, TipoCultura.id == Exame.tipo_cultura_id)
            .where(Exame.is_active.is_(True))
            .group_by(TipoCultura.nome)
            .order_by(func.count(Exame.id).desc())
        )
        return list(self.db.execute(stmt).all())

    def exames_por_material_mes(self) -> list[tuple[str, int]]:
        stmt = self._filtro_mes_corrente(
            select(Material.nome, func.count(Exame.id))
            .select_from(Exame)
            .join(Material, Material.id == Exame.material_id)
            .where(Exame.is_active.is_(True))
            .group_by(Material.nome)
            .order_by(func.count(Exame.id).desc())
        )
        return list(self.db.execute(stmt).all())

    def exames_por_setor_mes(self) -> list[tuple[str, int]]:
        """
        Distribuição por setor do mês corrente, contando TODOS os
        exames (qualquer status) - diferente de
        `CCIHRepository.distribuicao_por_setor`, que só considera
        exames positivos. `Exame.setor_id` é nullable, por isso o
        `outerjoin` + `func.coalesce`, mesmo padrão de
        `CCIHRepository.distribuicao_por_setor`.
        """
        nome_setor = func.coalesce(Setor.nome, SETOR_NAO_CLASSIFICADO)
        stmt = self._filtro_mes_corrente(
            select(nome_setor, func.count(Exame.id))
            .select_from(Exame)
            .outerjoin(Setor, Setor.id == Exame.setor_id)
            .where(Exame.is_active.is_(True))
            .group_by(nome_setor)
            .order_by(func.count(Exame.id).desc())
        )
        return list(self.db.execute(stmt).all())
