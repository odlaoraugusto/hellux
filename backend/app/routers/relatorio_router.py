"""
Router do módulo Relatórios (Sprint 10).

Diferente dos demais routers, estes endpoints não retornam o contrato
padrão JSON - eles devolvem o arquivo binário diretamente (Excel/PDF)
para download, com os headers apropriados.
"""
import io
import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_tenant, get_current_user
from app.db.session import get_db
from app.models.tenant import Tenant
from app.services.relatorio_service import RelatorioService

router = APIRouter(
    prefix="/api/relatorios", tags=["Relatórios"], dependencies=[Depends(get_current_user)]
)

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA_TYPE = "application/pdf"


def _download(conteudo: bytes, media_type: str, nome_arquivo: str) -> StreamingResponse:
    return StreamingResponse(
        io.BytesIO(conteudo),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{nome_arquivo}"'},
    )


@router.get("/pacientes.xlsx")
def exportar_pacientes_excel(
    db: Session = Depends(get_db), tenant: Tenant | None = Depends(get_current_tenant)
):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_pacientes(tenant)
    return _download(conteudo, XLSX_MEDIA_TYPE, "relatorio_pacientes.xlsx")


@router.get("/exames.xlsx")
def exportar_exames_excel(
    db: Session = Depends(get_db), tenant: Tenant | None = Depends(get_current_tenant)
):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_exames(tenant)
    return _download(conteudo, XLSX_MEDIA_TYPE, "relatorio_exames.xlsx")


@router.get("/exames-parciais.xlsx")
def exportar_exames_parciais_excel(
    db: Session = Depends(get_db), tenant: Tenant | None = Depends(get_current_tenant)
):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_exames_parciais(tenant)
    return _download(conteudo, XLSX_MEDIA_TYPE, "relatorio_resultados_parciais.xlsx")


@router.get("/ccih.pdf")
def exportar_ccih_pdf(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    setor_id: uuid.UUID | None = Query(default=None, description="Filtra por setor do exame"),
    db: Session = Depends(get_db),
    tenant: Tenant | None = Depends(get_current_tenant),
):
    service = RelatorioService(db)
    conteudo = service.gerar_pdf_ccih(data_inicio, data_fim, tenant=tenant, setor_id=setor_id)
    return _download(conteudo, PDF_MEDIA_TYPE, "relatorio_ccih.pdf")


@router.get("/ccih-vigilancia.pdf")
def exportar_ccih_vigilancia_pdf(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    setor_id: uuid.UUID | None = Query(default=None, description="Filtra por setor do exame"),
    db: Session = Depends(get_db),
    tenant: Tenant | None = Depends(get_current_tenant),
):
    service = RelatorioService(db)
    conteudo = service.gerar_pdf_ccih(
        data_inicio, data_fim, tenant=tenant, setor_id=setor_id, vigilancia=True
    )
    return _download(conteudo, PDF_MEDIA_TYPE, "relatorio_ccih_vigilancia.pdf")
