"""
Schemas de saída do módulo CCIH (Comissão de Controle de Infecção
Hospitalar) - Documento Mestre, seção 6 (Sprint 9).
"""
from datetime import date

from pydantic import BaseModel


class DistribuicaoSetorOut(BaseModel):
    setor: str
    total_positivas: int


class PerfilMicrobiologicoOut(BaseModel):
    microrganismo: str
    quantidade: int
    percentual: float


class TaxaResistenciaOut(BaseModel):
    antimicrobiano: str
    total_testado: int
    total_resistente: int
    percentual_resistente: float
    total_sensivel: int
    percentual_sensivel: float


class IndicadoresCCIHOut(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    filtro_setor: str | None = None
    total_solicitacoes: int
    total_culturas_positivas: int
    taxa_positividade: float
    distribuicao_por_setor: list[DistribuicaoSetorOut]
    perfil_microbiologico: list[PerfilMicrobiologicoOut]
    taxa_resistencia: list[TaxaResistenciaOut]


class MatrizSensibilidadeItemOut(BaseModel):
    """
    Uma célula da Matriz de Sensibilidade CCIH (Fase 1.5): resultado
    agregado de um antimicrobiano testado contra um grupo fenotípico de
    microrganismos, num macro-grupo de setores.
    """

    macro_grupo: str
    grupo_fenotipico: str
    antimicrobiano: str
    total_testado: int
    sensivel: int
    intermediario: int
    resistente: int
    percentual_sensivel: float
    percentual_intermediario: float
    percentual_resistente: float


class MatrizSensibilidadeOut(BaseModel):
    periodo_inicio: date
    periodo_fim: date
    itens: list[MatrizSensibilidadeItemOut]
