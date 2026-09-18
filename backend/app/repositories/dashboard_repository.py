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
    Exame,
    ExameIsolado,
    StatusExameEnum,
)
from app.models.microrganismo import Microrganismo
from app.repositories.parametro_sistema_repository import ParametroSistemaRepository

# Valor de fallback caso o parâmetro "prazo_solicitacao_dias" ainda não
# tenha sido semeado no banco (ex.: testes que criam schema sem migração).
PRAZO_PADRAO_DIAS_FALLBACK = 2


class DashboardRepository:
    def __init__(self, db: Session):
        self.db = db

    def _hoje_utc(self) -> date:
        return datetime.now(timezone.utc).date()

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
