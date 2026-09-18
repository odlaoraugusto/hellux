"""
Service do módulo Usuários.

Regra de negócio principal: o primeiro usuário cadastrado no sistema
(quando ainda não existe nenhum) é automaticamente promovido a ADMIN,
resolvendo o problema de "bootstrap" (quem cadastra o primeiro admin?).
A partir do segundo usuário, a criação exige um ADMIN autenticado (essa
checagem é feita no Router, via `require_perfil`).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.security import hash_senha
from app.models.usuario import PerfilUsuarioEnum
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioService:
    def __init__(self, db: Session):
        self.repository = UsuarioRepository(db)

    def sistema_precisa_de_bootstrap(self) -> bool:
        """True quando ainda não existe nenhum usuário cadastrado no sistema."""
        return not self.repository.existe_algum_usuario()

    def listar(self, page: int = 1, page_size: int = 20):
        skip = (page - 1) * page_size
        return self.repository.list(skip=skip, limit=page_size)

    def obter(self, usuario_id: uuid.UUID):
        usuario = self.repository.get_by_id(usuario_id)
        if not usuario or not usuario.is_active:
            raise NotFoundError("Usuário não encontrado.")
        return usuario

    def criar(self, dados: UsuarioCreate):
        login_normalizado = dados.login.lower()
        existente = self.repository.get_by_login(login_normalizado)
        if existente:
            raise BusinessRuleError(
                "Já existe um usuário cadastrado com este login.",
                errors=[f"login '{dados.login}' já está em uso."],
            )

        eh_primeiro_usuario = self.sistema_precisa_de_bootstrap()
        perfil = PerfilUsuarioEnum.ADMIN if eh_primeiro_usuario else dados.perfil

        return self.repository.create(
            {
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
