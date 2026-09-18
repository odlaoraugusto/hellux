"""
Repository do catálogo de Tipos de Cultura.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tipo_cultura import TipoCultura
from app.repositories.base import BaseRepository


class TipoCulturaRepository(BaseRepository[TipoCultura]):
    def __init__(self, db: Session):
        super().__init__(db, TipoCultura)

    def get_by_nome(self, nome: str) -> TipoCultura | None:
        stmt = select(TipoCultura).where(
            TipoCultura.nome.ilike(nome), TipoCultura.is_active.is_(True)
        )
        return self.db.scalars(stmt).first()

    def listar_todos(self) -> list[TipoCultura]:
        stmt = select(TipoCultura).where(TipoCultura.is_active.is_(True)).order_by(TipoCultura.nome)
        return list(self.db.scalars(stmt).all())
