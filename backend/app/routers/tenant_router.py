"""
Router do módulo Tenants - gestão de unidades/hospitais-cliente.

Todo restrito a SUPER_ADMIN (perfil que não pertence a tenant nenhum -
ver app/models/usuario.py). Cadastrar um tenant já cria, na mesma
chamada, o primeiro usuário ADMIN dele.
"""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import require_perfil
from app.core.response import success_response
from app.db.session import get_db
from app.models.usuario import PerfilUsuarioEnum
from app.schemas.tenant import TenantCreate, TenantOut, TenantUpdate
from app.schemas.usuario import UsuarioOut
from app.services.tenant_service import TenantService

router = APIRouter(
    prefix="/api/tenants",
    tags=["Tenants"],
    dependencies=[Depends(require_perfil(PerfilUsuarioEnum.SUPER_ADMIN))],
)


@router.get("")
def listar_tenants(db: Session = Depends(get_db)):
    service = TenantService(db)
    itens = service.listar()
    data = {"total": len(itens), "items": [TenantOut.model_validate(i).model_dump(mode="json") for i in itens]}
    return success_response(data, message="Tenants listados com sucesso.")


@router.get("/{tenant_id}")
def obter_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant = service.obter(tenant_id)
    return success_response(
        TenantOut.model_validate(tenant).model_dump(mode="json"), message="Tenant encontrado."
    )


@router.post("", status_code=201)
def criar_tenant(dados: TenantCreate, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant, admin = service.criar(dados)
    return success_response(
        {
            "tenant": TenantOut.model_validate(tenant).model_dump(mode="json"),
            "admin": UsuarioOut.model_validate(admin).model_dump(mode="json"),
        },
        message="Tenant e administrador inicial cadastrados com sucesso.",
    )


@router.put("/{tenant_id}")
def atualizar_tenant(tenant_id: uuid.UUID, dados: TenantUpdate, db: Session = Depends(get_db)):
    service = TenantService(db)
    tenant = service.atualizar(tenant_id, dados)
    return success_response(
        TenantOut.model_validate(tenant).model_dump(mode="json"),
        message="Tenant atualizado com sucesso.",
    )
