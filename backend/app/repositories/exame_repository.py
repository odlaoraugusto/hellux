"""
Repository do fluxo de Exame unificado (Fase 1).

Lida também com as tabelas filhas `ExameIsolado`/`ExameAntibiograma`, já
que a listagem/edição de um exame sempre acompanha seus isolados e o
antibiograma de cada um (mesmo espírito do antigo `CulturaRepository`).
"""
import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, joinedload

from app.core.tenant_context import get_current_tenant_id
from app.models.exame import (
    STATUS_FINAIS,
    Exame,
    ExameAntibiograma,
    ExameIsolado,
    StatusExameEnum,
)
from app.repositories.base import BaseRepository


class ExameRepository(BaseRepository[Exame]):
    def __init__(self, db: Session):
        super().__init__(db, Exame)

    def _base_query(self):
        return select(Exame).options(
            joinedload(Exame.paciente),
            joinedload(Exame.setor),
            joinedload(Exame.tipo_cultura),
            joinedload(Exame.material),
            joinedload(Exame.isolados).joinedload(ExameIsolado.microrganismo),
            joinedload(Exame.isolados)
            .joinedload(ExameIsolado.antibiograma)
            .joinedload(ExameAntibiograma.antimicrobiano),
        )

    def get_by_id(self, entity_id: uuid.UUID) -> Exame | None:
        stmt = self._base_query().where(Exame.id == entity_id)
        return self.db.scalars(stmt).unique().first()

    def search(
        self,
        status: list[StatusExameEnum] | StatusExameEnum | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Exame], int]:
        stmt = self._base_query().where(Exame.is_active.is_(True))

        if status:
            if isinstance(status, list):
                stmt = stmt.where(Exame.status.in_(status))
            else:
                stmt = stmt.where(Exame.status == status)

        total = len(self.db.scalars(stmt).unique().all())
        items = (
            self.db.scalars(stmt.offset(skip).limit(limit).order_by(Exame.created_at.desc()))
            .unique()
            .all()
        )
        return list(items), total

    def buscar_parciais(self) -> list[Exame]:
        """Exames ainda não finalizados - base do relatório de resultados parciais."""
        stmt = (
            self._base_query()
            .where(Exame.is_active.is_(True), Exame.status.notin_(STATUS_FINAIS))
            .order_by(Exame.previsao_liberacao.asc().nulls_last(), Exame.created_at.asc())
        )
        return list(self.db.scalars(stmt).unique().all())

    def definir_isolados(self, exame_id: uuid.UUID, isolados: list) -> None:
        """Substitui por inteiro a lista de isolados (+ antibiograma) do exame."""
        tenant_id = get_current_tenant_id(self.db)

        isolados_atuais = select(ExameIsolado.id).where(ExameIsolado.exame_id == exame_id)
        self.db.execute(
            delete(ExameAntibiograma).where(ExameAntibiograma.isolado_id.in_(isolados_atuais))
        )
        self.db.execute(delete(ExameIsolado).where(ExameIsolado.exame_id == exame_id))

        for item in isolados:
            isolado = ExameIsolado(
                tenant_id=tenant_id,
                exame_id=exame_id,
                microrganismo_id=item.microrganismo_id,
                mecanismo_resistencia=item.mecanismo_resistencia,
                nao_realizado_tecnico=item.nao_realizado_tecnico,
                motivo_dispensa_tsa=item.motivo_dispensa_tsa,
            )
            self.db.add(isolado)
            self.db.flush()  # precisa do id antes de criar o antibiograma

            for resultado in item.antibiograma:
                self.db.add(
                    ExameAntibiograma(
                        tenant_id=tenant_id,
                        isolado_id=isolado.id,
                        antimicrobiano_id=resultado.antimicrobiano_id,
                        resultado=resultado.resultado,
                    )
                )

        self.db.commit()

    def isolados_sem_antibiograma(self, exame: Exame) -> list[uuid.UUID]:
        """
        Entre os isolados de um exame, devolve os IDs dos que ainda não
        têm nenhum resultado de antibiograma - usado para calcular a
        pendência de exames positivos ainda não finalizados. Isolados
        marcados como `nao_realizado_tecnico` são excluídos dessa lista
        (dispensados individualmente da exigência).
        """
        isolado_ids = [i.id for i in exame.isolados if not i.nao_realizado_tecnico]
        if not isolado_ids:
            return []

        stmt = (
            select(ExameIsolado.id)
            .outerjoin(ExameAntibiograma, ExameAntibiograma.isolado_id == ExameIsolado.id)
            .where(ExameIsolado.id.in_(isolado_ids))
            .group_by(ExameIsolado.id)
            .having(func.count(ExameAntibiograma.id) == 0)
        )
        return list(self.db.scalars(stmt).all())
