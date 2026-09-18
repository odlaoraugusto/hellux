"""
Service do módulo Tenants - gestão de unidades/hospitais-cliente.

Só acessível por um usuário SUPER_ADMIN (ver app/routers/tenant_router.py
e app/models/usuario.py). Cadastrar um tenant já cria, na mesma chamada,
o primeiro usuário ADMIN dele - mesma ordem do script
`scripts/bootstrap_tenant.py` (tenant existe -> contexto de RLS setado
para o tenant recém-criado -> usuário inserido), só que via duas
transações em vez de uma só (o tenant precisa estar COMMITADO antes de
`set_tenant_context` poder ser chamado com segurança - ver docstring de
`set_tenant_context`).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.tenant_context import set_tenant_context
from app.models.tenant import Tenant
from app.models.usuario import PerfilUsuarioEnum, Usuario
from app.repositories.tenant_repository import TenantRepository
from app.schemas.tenant import TenantCreate, TenantUpdate
from app.schemas.usuario import UsuarioCreate
from app.services.usuario_service import UsuarioService


class TenantService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = TenantRepository(db)
        self.usuario_service = UsuarioService(db)

    def listar(self) -> list[Tenant]:
        return self.repository.listar_todos()

    def obter(self, tenant_id: uuid.UUID) -> Tenant:
        tenant = self.repository.get_by_id(tenant_id)
        if not tenant:
            raise NotFoundError("Tenant não encontrado.")
        return tenant

    def criar(self, dados: TenantCreate) -> tuple[Tenant, Usuario]:
        tenant = self.repository.create(
            {
                "nome_fantasia": dados.nome_fantasia,
                "razao_social": dados.razao_social,
                "cnpj": dados.cnpj,
                "logo_url": dados.logo_url,
                "subtitulo_cabecalho": dados.subtitulo_cabecalho,
            }
        )

        # Só agora (tenant já commitado acima) é seguro trocar o contexto
        # de RLS da sessão - set_tenant_context() faz um rollback() pra
        # forçar a próxima transação a reaplicar o SET LOCAL, o que
        # descartaria o tenant se ele ainda não tivesse sido commitado.
        set_tenant_context(self.db, tenant.id)

        admin = self.usuario_service.criar(
            UsuarioCreate(
                nome=dados.admin_nome,
                login=dados.admin_login,
                senha=dados.admin_senha,
                perfil=PerfilUsuarioEnum.ADMIN,
            ),
            tenant.id,
        )

        return tenant, admin

    def atualizar(self, tenant_id: uuid.UUID, dados: TenantUpdate) -> Tenant:
        tenant = self.obter(tenant_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(tenant, dados_dict)
