"""
Service do catálogo de Microrganismos (Base de Conhecimento).
"""
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.tenant_context import get_current_tenant_id
from app.repositories.microrganismo_repository import MicrorganismoRepository
from app.schemas.microrganismo import MicrorganismoCreate, MicrorganismoUpdate


class MicrorganismoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = MicrorganismoRepository(db)

    def listar(self, termo: str | None, page: int = 1, page_size: int = 20):
        skip = (page - 1) * page_size
        return self.repository.search(termo, skip=skip, limit=page_size)

    def obter(self, microrganismo_id: uuid.UUID):
        microrganismo = self.repository.get_by_id(microrganismo_id)
        if not microrganismo or not microrganismo.is_active:
            raise NotFoundError("Microrganismo não encontrado.")
        return microrganismo

    # Campos de taxonomia/morfologia que participam da herança automática por
    # gênero (ver docstring de `criar`).
    _CAMPOS_HERDAVEIS = ("gram", "tipo", "morfologia", "fermentador", "familia")

    def criar(self, dados: MicrorganismoCreate):
        existente = self.repository.get_by_nome(dados.nome)
        if existente:
            raise BusinessRuleError(
                "Já existe um microrganismo cadastrado com este nome.",
                errors=[f"nome '{dados.nome}' já está em uso."],
            )

        dados_dict = dados.model_dump()
        self._herdar_taxonomia_do_genero(dados, dados_dict)
        dados_dict["tenant_id"] = get_current_tenant_id(self.db)
        return self.repository.create(dados_dict)

    def _herdar_taxonomia_do_genero(
        self, dados: MicrorganismoCreate, dados_dict: dict
    ) -> None:
        """"Aprendizado" incremental da base de conhecimento: se o cliente não
        informou explicitamente NENHUM dos campos de taxonomia/morfologia
        (gram/tipo/morfologia/fermentador/familia) e já existe algum
        microrganismo ativo do mesmo gênero (primeira palavra do nome, ex.:
        "Klebsiella" em "Klebsiella aerogenes") cadastrado, copiamos esses
        campos dele em vez de usar os defaults genéricos do schema. Assim,
        cadastrar uma nova espécie de um gênero já conhecido já nasce com
        Gram/família corretos sem digitar nada. Se o usuário informar
        qualquer um desses campos na requisição (mesmo que igual ao default),
        a herança é pulada e o que foi enviado prevalece.
        """
        campos_informados = set(dados.model_fields_set) & set(self._CAMPOS_HERDAVEIS)
        if campos_informados:
            return

        genero = dados.nome.strip().split(" ")[0]
        if not genero:
            return

        referencia = self.repository.get_by_genero(genero)
        if not referencia:
            return

        for campo in self._CAMPOS_HERDAVEIS:
            dados_dict[campo] = getattr(referencia, campo)

    def atualizar(self, microrganismo_id: uuid.UUID, dados: MicrorganismoUpdate):
        microrganismo = self.obter(microrganismo_id)
        dados_dict = dados.model_dump(exclude_unset=True)
        return self.repository.update(microrganismo, dados_dict)

    def remover(self, microrganismo_id: uuid.UUID):
        microrganismo = self.obter(microrganismo_id)
        self.repository.soft_delete(microrganismo)
