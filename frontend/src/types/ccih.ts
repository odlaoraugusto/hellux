export interface DistribuicaoSetor {
  setor: string;
  total_positivas: number;
}

export interface PerfilMicrobiologico {
  microrganismo: string;
  quantidade: number;
  percentual: number;
}

export interface TaxaResistencia {
  antimicrobiano: string;
  total_testado: number;
  total_resistente: number;
  percentual_resistente: number;
  total_sensivel: number;
  percentual_sensivel: number;
}

export interface IndicadoresCCIH {
  periodo_inicio: string;
  periodo_fim: string;
  filtro_setor: string | null;
  filtro_tipos_cultura: string[] | null;
  total_solicitacoes: number;
  total_culturas_positivas: number;
  taxa_positividade: number;
  distribuicao_por_setor: DistribuicaoSetor[];
  perfil_microbiologico: PerfilMicrobiologico[];
  taxa_resistencia: TaxaResistencia[];
}
