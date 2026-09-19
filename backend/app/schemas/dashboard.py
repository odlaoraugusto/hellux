"""
Schema de saída do Dashboard.
"""
from pydantic import BaseModel


class TopMicrorganismoOut(BaseModel):
    nome: str
    quantidade: int


class AlertaOut(BaseModel):
    tipo: str  # "prazo" | "resistencia" | "info"
    mensagem: str


class ContagemCatalogoOut(BaseModel):
    """Contagem de exames agrupados por um item de catálogo (tipo de
    cultura, material ou setor) - usado nos gráficos mensais do
    dashboard redesenhado."""

    nome: str
    quantidade: int


class ResumoDashboardOut(BaseModel):
    culturas_hoje: int
    aguardando_atualizacao: int
    prazo_vencido: int
    liberados_hoje: int
    top_microrganismos: list[TopMicrorganismoOut]
    alertas: list[AlertaOut]
    total_exames_mes: int
    taxa_positividade_mes: float
    por_tipo_cultura: list[ContagemCatalogoOut]
    por_material: list[ContagemCatalogoOut]
    por_setor: list[ContagemCatalogoOut]
