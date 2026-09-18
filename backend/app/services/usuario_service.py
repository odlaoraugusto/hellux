"""
Service do módulo Usuários.

Regra de negócio principal: o primeiro usuário cadastrado de um tenant
(quando ele ainda não tem nenhum) é automaticamente promovido a ADMIN,
resolvendo o problema de "bootstrap" (quem cadastra o primeiro admin?).
A partir do segundo usuário DAQUELE tenant, a criação exige um ADMIN
autenticado (checagem feita no Router, via `require_perfil`/token).

Fase 1 (fundação multi-tenant): esse bootstrap agora é por tenant, não
mais global. Como ainda não existe endpoint de self-service de tenant
(ver docs/plano da Fase 1 - só o script `scripts/bootstrap_tenant.py`),
o cadastro aberto (sem token) só funciona quando existe exatamente um
tenant no sistema - se não existir nenhum ainda (primeiro uso local/dev,
ou suíte de testes que não criou um tenant explicitamente), um tenant
padrão é criado automaticamente na hora.
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.security import hash_senha
from app.core.tenant_context import set_tenant_context
from app.models.tenant import Tenant
from app.models.usuario import PerfilUsuarioEnum
from app.repositories.tenant_repository import TenantRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate

NOME_TENANT_PADRAO_BOOTSTRAP = "Tenant Padrão"


class UsuarioService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = UsuarioRepository(db)
        self.tenant_repository = TenantRepository(db)

    def resolver_tenant_bootstrap(self) -> Tenant:
        """
        Resolve para qual tenant um cadastro ABERTO (sem token) de usuário
        deve ir. Só funciona sem ambiguidade quando existe exatamente um
        tenant ativo; se nenhum existir ainda, cria um tenant padrão na
        hora (bootstrap local/dev/teste - em produção o caminho oficial é
        `scripts/bootstrap_tenant.py`).
        """
        tenants = self.tenant_repository.listar_ativos()
        if len(tenants) == 1:
            return tenants[0]
        if len(tenants) == 0:
            return self.tenant_repository.create({"nome_fantasia": NOME_TENANT_PADRAO_BOOTSTRAP})
        raise BusinessRuleError(
            "Existe mais de um tenant cadastrado - não é possível determinar "
            "automaticamente para qual tenant o cadastro aberto deveria ir. "
            "Autentique-se com um usuário ADMIN do tenant desejado.",
        )

    def aplicar_contexto_tenant(self, tenant_id: uuid.UUID) -> None:
        set_tenant_context(self.db, tenant_id)

    def tenant_ja_possui_usuario(self, tenant_id: uuid.UUID) -> bool:
        return self.repository.existe_usuario_do_tenant(tenant_id)

    def criar_super_admin(self, dados: UsuarioCreate):
        """
        Cadastra um usuário SUPER_ADMIN (sem tenant) - só deve ser chamado
        depois de confirmado que quem está pedindo já é, ele mesmo, um
        SUPER_ADMIN autenticado (checagem no Router) OU pelo script
        `scripts/bootstrap_tenant.py --super-admin` (bootstrap do
        primeiro SUPER_ADMIN do sistema, que não pode se auto-cadastrar
        por API - problema do ovo e da galinha).
        """
        login_normalizado = dados.login.lower()
        existente = self.repository.get_super_admin_by_login(login_normalizado)
        if existente:
            raise BusinessRuleError(
                "Já existe um SUPER_ADMIN cadastrado com este login.",
                errors=[f"login '{dados.login}' já está em uso."],
            )
        return self.repository.create(
            {
                "tenant_id": None,
                "nome": dados.nome,
                "login": login_normalizado,
                "senha_hash": hash_senha(dados.senha),
                "perfil": PerfilUsuarioEnum.SUPER_ADMIN,
            }
        )

    def listar(self, tenant_id: uuid.UUID | None = None, page: int = 1, page_size: int = 20):
        skip = (page - 1) * page_size
        return self.repository.search(tenant_id=tenant_id, skip=skip, limit=page_size)

    def obter(self, usuario_id: uuid.UUID):
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario or not usuario.is_active:
            raise NotFoundError("Usuário não encontrado.")
        return usuario

    def criar(self, dados: UsuarioCreate, tenant_id: uuid.UUID):
        login_normalizado = dados.login.lower()
        existente = self.repository.get_by_login(login_normalizado)
        if existente and existente.tenant_id == tenant_id:
            raise BusinessRuleError(
                "Já existe um usuário cadastrado com este login.",
                errors=[f"login '{dados.login}' já está em uso."],
            )

        eh_primeiro_usuario_do_tenant = not self.tenant_ja_possui_usuario(tenant_id)
        perfil = PerfilUsuarioEnum.ADMIN if eh_primeiro_usuario_do_tenant else dados.perfil

        return self.repository.create(
            {
                "tenant_id": tenant_id,
                "nome": dados.nome,
                "login": login_normalizado,
                "senha_hash": hash_senha(dados.senha),
                "perfil": perfil,
            }
        )

    def atualizar(self, usuario_id: uuid.UUID, dados: UsuarioUpdate):
        usuario = self.obter(usuario_id)
        dados_dict = dados.model_dump(exclude_unset=True, exclude={"senha"})

        if dados.senha:
            dados_dict["senha_hash"] = hash_senha(dados.senha)

        return self.repository.update(usuario, dados_dict)

    def remover(self, usuario_id: uuid.UUID):
        usuario = self.obter(usuario_id)
        self.repository.soft_delete(usuario)
