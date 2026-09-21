"""
Script de bootstrap de tenant/SUPER_ADMIN (Fase 1 - fundação multi-tenant).

Dois modos:

1. Bootstrap de um TENANT novo (modo padrão): cria o tenant, aplica o
   contexto de Row Level Security (`SET LOCAL app.current_tenant_id`)
   para o id recém-criado DENTRO DA MESMA TRANSAÇÃO, e só então insere o
   primeiro usuário ADMIN daquele tenant - a ordem importa porque a
   tabela `usuarios` tem RLS forçada (ver app/db/session.py): inserir o
   usuário antes de setar o contexto seria bloqueado pela própria
   policy. Também semeia um TipoCultura padrão ("Cultura Geral") para o
   tenant não nascer sem nenhuma opção de catálogo.

   Desde a Fase 1, o caminho recomendado pra esse caso é a API
   (POST /api/tenants, autenticado como SUPER_ADMIN - ver
   app/routers/tenant_router.py) - este script continua existindo para
   bootstrap local/CLI sem precisar de um SUPER_ADMIN já existente.

2. Bootstrap do PRIMEIRO SUPER_ADMIN do sistema todo (`--super-admin`):
   não tem tenant nenhum (tenant_id fica NULL) - só é possível via
   script porque não existe (nem pode existir) um endpoint de API que
   crie o primeiro SUPER_ADMIN sem que outro SUPER_ADMIN já autenticado
   o faça (problema do ovo e da galinha).

Uso:
    python scripts/bootstrap_tenant.py \
        --nome-fantasia "Hospital Exemplo" \
        --admin-nome "Fulano de Tal" --admin-login "fulano.admin" --admin-senha "..."

    python scripts/bootstrap_tenant.py --super-admin \
        --nome "Operação Hellux" --login "superadmin" --senha "..."
"""
import argparse
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.core.security import hash_senha  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.models.tenant import Tenant  # noqa: E402
from app.models.tipo_cultura import TipoCultura  # noqa: E402
from app.models.usuario import PerfilUsuarioEnum, Usuario  # noqa: E402

TIPO_CULTURA_PADRAO = "Cultura Geral"


def _set_local_tenant(db, tenant_id: uuid.UUID | None, is_super_admin: bool = False) -> None:
    """
    Equivalente ao `set_tenant_context` de app/core/tenant_context.py,
    mas executado DIRETO (sem rollback) porque aqui controlamos a
    transação manualmente - o tenant recém-criado ainda não foi
    commitado, e um rollback o descartaria.
    """
    if db.bind.dialect.name != "postgresql":
        return
    if tenant_id:
        db.execute(text(f"SET LOCAL app.current_tenant_id = '{uuid.UUID(str(tenant_id))}'"))
    if is_super_admin:
        db.execute(text("SET LOCAL app.is_super_admin = 'true'"))


def bootstrap_tenant(
    nome_fantasia: str,
    admin_nome: str,
    admin_login: str,
    admin_senha: str,
    razao_social: str | None = None,
    cnpj: str | None = None,
) -> tuple[Tenant, Usuario]:
    db = SessionLocal()
    try:
        tenant = Tenant(nome_fantasia=nome_fantasia, razao_social=razao_social, cnpj=cnpj)
        db.add(tenant)
        db.flush()  # gera o id do tenant sem encerrar a transação

        _set_local_tenant(db, tenant.id)

        admin = Usuario(
            tenant_id=tenant.id,
            nome=admin_nome,
            login=admin_login.lower(),
            senha_hash=hash_senha(admin_senha),
            perfil=PerfilUsuarioEnum.ADMIN,
        )
        db.add(admin)

        tipo_cultura_padrao = TipoCultura(tenant_id=tenant.id, nome=TIPO_CULTURA_PADRAO)
        db.add(tipo_cultura_padrao)

        db.commit()
        # Mesmo problema documentado em `bootstrap_super_admin` logo abaixo -
        # o `SET LOCAL app.current_tenant_id` acima não sobrevive ao
        # commit, e o `refresh(admin)` precisa dele (RLS de `usuarios`).
        db.refresh(tenant)  # tenants não tem RLS - este não precisa do contexto
        _set_local_tenant(db, tenant.id)
        db.refresh(admin)
        return tenant, admin
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def bootstrap_super_admin(nome: str, login: str, senha: str) -> Usuario:
    db = SessionLocal()
    try:
        _set_local_tenant(db, tenant_id=None, is_super_admin=True)

        super_admin = Usuario(
            tenant_id=None,
            nome=nome,
            login=login.lower(),
            senha_hash=hash_senha(senha),
            perfil=PerfilUsuarioEnum.SUPER_ADMIN,
        )
        db.add(super_admin)
        db.commit()
        # `db.commit()` encerra a transação e descarta o `SET LOCAL` acima
        # (é por-transação, não por-sessão) - sem reaplicar, o SELECT
        # implícito do `refresh()` roda sem `app.is_super_admin`, a policy
        # de RLS de `usuarios` não bate com nenhuma linha, e o SQLAlchemy
        # levanta `InvalidRequestError` (linha "sumiu" do ponto de vista
        # da query). Mesmo problema documentado em `app/db/session.py`
        # (listener `after_begin`) - aqui não dá pra usar o listener
        # porque o `SET LOCAL` é feito via SQL cru, não via
        # `session.info`, então reaplicamos manualmente.
        _set_local_tenant(db, tenant_id=None, is_super_admin=True)
        db.refresh(super_admin)
        return super_admin
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--super-admin",
        action="store_true",
        help="Cria o primeiro SUPER_ADMIN do sistema (sem tenant), em vez de um tenant.",
    )

    # Modo tenant
    parser.add_argument("--nome-fantasia")
    parser.add_argument("--razao-social", default=None)
    parser.add_argument("--cnpj", default=None)
    parser.add_argument("--admin-nome")
    parser.add_argument("--admin-login")
    parser.add_argument("--admin-senha")

    # Modo super-admin
    parser.add_argument("--nome")
    parser.add_argument("--login")
    parser.add_argument("--senha")

    args = parser.parse_args()

    if args.super_admin:
        faltando = [
            campo
            for campo, valor in (("--nome", args.nome), ("--login", args.login), ("--senha", args.senha))
            if not valor
        ]
    else:
        faltando = [
            campo
            for campo, valor in (
                ("--nome-fantasia", args.nome_fantasia),
                ("--admin-nome", args.admin_nome),
                ("--admin-login", args.admin_login),
                ("--admin-senha", args.admin_senha),
            )
            if not valor
        ]
    if faltando:
        parser.error(f"argumento(s) obrigatório(s) faltando: {', '.join(faltando)}")

    return args


if __name__ == "__main__":
    args = _parse_args()

    if args.super_admin:
        usuario = bootstrap_super_admin(args.nome, args.login, args.senha)
        print(f"SUPER_ADMIN criado: {usuario.login} (id={usuario.id})")
    else:
        tenant, admin = bootstrap_tenant(
            nome_fantasia=args.nome_fantasia,
            admin_nome=args.admin_nome,
            admin_login=args.admin_login,
            admin_senha=args.admin_senha,
            razao_social=args.razao_social,
            cnpj=args.cnpj,
        )
        print(f"Tenant criado: {tenant.nome_fantasia} (id={tenant.id})")
        print(f"Admin criado: {admin.login} (id={admin.id})")
