"""
Repository do módulo Tenants.

A tabela `tenants` é a raiz da hierarquia multi-tenant e não tem
`tenant_id`/Row Level Security nela mesma (ver app/models/tenant.py) -
por isso os métodos aqui não filtram por tenant nenhum, de propósito.
"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    def __init__(self, db: Session):
        super().__init__(db, Tenant)

    def listar_todos(self) -> list[Tenant]:
        stmt = select(Tenant).order_by(Tenant.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def listar_ativos(self) -> list[Tenant]:
        stmt = select(Tenant).where(Tenant.ativo.is_(True)).order_by(Tenant.created_at)
        return list(self.db.scalars(stmt).all())
