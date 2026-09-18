"""
Router do módulo Relatórios (Sprint 10).

Diferente dos demais routers, estes endpoints não retornam o contrato
padrão JSON - eles devolvem o arquivo binário diretamente (Excel/PDF)
para download, com os headers apropriados.
"""
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
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
def exportar_pacientes_excel(db: Session = Depends(get_db)):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_pacientes()
    return _download(conteudo, XLSX_MEDIA_TYPE, "hellux_pacientes.xlsx")


@router.get("/solicitacoes.xlsx")
def exportar_solicitacoes_excel(db: Session = Depends(get_db)):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_solicitacoes()
    return _download(conteudo, XLSX_MEDIA_TYPE, "hellux_solicitacoes.xlsx")


@router.get("/culturas-parciais.xlsx")
def exportar_culturas_parciais_excel(db: Session = Depends(get_db)):
    service = RelatorioService(db)
    conteudo = service.gerar_excel_culturas_parciais()
    return _download(conteudo, XLSX_MEDIA_TYPE, "hellux_resultados_parciais.xlsx")


@router.get("/ccih.pdf")
def exportar_ccih_pdf(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    origem: str | None = Query(default=None, description="Filtra por setor/origem da solicitação"),
    db: Session = Depends(get_db),
):
    service = RelatorioService(db)
    conteudo = service.gerar_pdf_ccih(data_inicio, data_fim, origem=origem)
    return _download(conteudo, PDF_MEDIA_TYPE, "hellux_relatorio_ccih.pdf")


@router.get("/ccih-vigilancia.pdf")
def exportar_ccih_vigilancia_pdf(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    origem: str | None = Query(default=None, description="Filtra por setor/origem da solicitação"),
    db: Session = Depends(get_db),
):
    service = RelatorioService(db)
    conteudo = service.gerar_pdf_ccih(data_inicio, data_fim, origem=origem, vigilancia=True)
    return _download(conteudo, PDF_MEDIA_TYPE, "hellux_relatorio_ccih_vigilancia.pdf")
