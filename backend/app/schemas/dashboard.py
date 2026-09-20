"""
Schema de saída do Dashboard.
"""
from datetime import date

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


class ContagemDiariaOut(BaseModel):
    """Contagem de exames criados em um dia específico - usado no
    sparkline de tendência dos últimos 7 dias do card "Total de
    culturas no mês"."""

    data: date
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
    tendencia_7_dias: list[ContagemDiariaOut]
