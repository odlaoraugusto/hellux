"""
Router do módulo Usuários.

Regra especial de bootstrap: a criação do usuário está aberta (sem
autenticação) apenas enquanto o tenant-alvo ainda não tiver nenhum
usuário - esse primeiro cadastro vira automaticamente ADMIN (ver
UsuarioService). A partir daí, criar/listar/editar/remover usuários
daquele tenant exige um ADMIN (ou um SUPER_ADMIN) autenticado.

Fase 1 (fundação multi-tenant): quando a requisição vem com um token
válido, o tenant é o do usuário autenticado; sem token, só é possível
resolver o tenant automaticamente quando existe exatamente um tenant no
sistema (ver `UsuarioService.resolver_tenant_bootstrap`).

Um SUPER_ADMIN não tem tenant próprio - por isso ele precisa informar
`tenant_id` explicitamente no corpo (POST) ou na query (GET) para dizer
de qual tenant ele está falando; os demais perfis nunca escolhem o
tenant, ele é sempre implícito (o deles mesmo).
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import CREDENCIAIS_INVALIDAS, get_current_user, oauth2_scheme, require_perfil
from app.core.response import success_response
from app.db.session import get_db
from app.models.usuario import PerfilUsuarioEnum
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/api/usuarios", tags=["Usuários"])

PERFIS_QUE_GERENCIAM_USUARIOS = (PerfilUsuarioEnum.ADMIN, PerfilUsuarioEnum.SUPER_ADMIN)


@router.post("", status_code=201)
def criar_usuario(
    dados: UsuarioCreate,
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme),
):
    service = UsuarioService(db)
    usuario_atual = get_current_user(token=token, db=db) if token else None

    # Cadastro de um SUPER_ADMIN: só outro SUPER_ADMIN pode fazer isso, e
    # nunca tem tenant_id (validado também no schema).
    if dados.perfil == PerfilUsuarioEnum.SUPER_ADMIN:
        if usuario_atual is None or usuario_atual.perfil != PerfilUsuarioEnum.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas um SUPER_ADMIN pode cadastrar outro SUPER_ADMIN.",
            )
        usuario = service.criar_super_admin(dados)
        return success_response(
            UsuarioOut.model_validate(usuario).model_dump(mode="json"),
            message="Usuário SUPER_ADMIN cadastrado com sucesso.",
        )

    if usuario_atual is not None and usuario_atual.perfil == PerfilUsuarioEnum.SUPER_ADMIN:
        # SUPER_ADMIN não tem tenant implícito - precisa dizer qual.
        if not dados.tenant_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="tenant_id é obrigatório ao cadastrar usuário como SUPER_ADMIN.",
            )
        tenant_id = dados.tenant_id
    elif usuario_atual is not None:
        tenant_id = usuario_atual.tenant_id
    else:
        tenant = service.resolver_tenant_bootstrap()
        tenant_id = tenant.id
        service.aplicar_contexto_tenant(tenant_id)

    bootstrap_necessario = not service.tenant_ja_possui_usuario(tenant_id)

    if not bootstrap_necessario:
        if usuario_atual is None:
            raise CREDENCIAIS_INVALIDAS
        if usuario_atual.perfil not in PERFIS_QUE_GERENCIAM_USUARIOS:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas administradores podem cadastrar novos usuários.",
            )

    usuario = service.criar(dados, tenant_id)
    return success_response(
        UsuarioOut.model_validate(usuario).model_dump(mode="json"),
        message="Usuário cadastrado com sucesso.",
    )


@router.get("", dependencies=[Depends(require_perfil(*PERFIS_QUE_GERENCIAM_USUARIOS))])
def listar_usuarios(
    tenant_id: uuid.UUID | None = Query(
        default=None,
        description="Só tem efeito para quem está autenticado como SUPER_ADMIN - "
        "filtra a listagem para um tenant específico. Sem isso, um SUPER_ADMIN "
        "vê usuários de TODOS os tenants.",
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = UsuarioService(db)
    items, total = service.listar(tenant_id=tenant_id, page=page, page_size=page_size)
    data = {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [UsuarioOut.model_validate(item).model_dump(mode="json") for item in items],
    }
    return success_response(data, message="Usuários listados com sucesso.")


@router.put(
    "/{usuario_id}", dependencies=[Depends(require_perfil(*PERFIS_QUE_GERENCIAM_USUARIOS))]
)
def atualizar_usuario(usuario_id: uuid.UUID, dados: UsuarioUpdate, db: Session = Depends(get_db)):
    service = UsuarioService(db)
    usuario = service.atualizar(usuario_id, dados)
    return success_response(
        UsuarioOut.model_validate(usuario).model_dump(mode="json"),
        message="Usuário atualizado com sucesso.",
    )


@router.delete(
    "/{usuario_id}", dependencies=[Depends(require_perfil(*PERFIS_QUE_GERENCIAM_USUARIOS))]
)
def remover_usuario(usuario_id: uuid.UUID, db: Session = Depends(get_db)):
    service = UsuarioService(db)
    service.remover(usuario_id)
    return success_response(message="Usuário removido com sucesso.")
