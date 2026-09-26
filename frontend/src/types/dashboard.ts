import { StatusPainel } from "./exame";

export interface TopMicrorganismo {
  nome: string;
  quantidade: number;
}

export type TipoAlerta = "prazo" | "resistencia" | "info";

export interface Alerta {
  tipo: TipoAlerta;
  mensagem: string;
}

export interface ContagemCatalogo {
  nome: string;
  quantidade: number;
}

export interface ContagemDiaria {
  data: string;
  quantidade: number;
}

export interface ContagemStatus {
  status: StatusPainel;
  quantidade: number;
}

export interface ResumoDashboard {
  culturas_hoje: number;
  aguardando_atualizacao: number;
  prazo_vencido: number;
  liberados_hoje: number;
  top_microrganismos: TopMicrorganismo[];
  alertas: Alerta[];
  total_exames_mes: number;
  taxa_positividade_mes: number;
  por_tipo_cultura: ContagemCatalogo[];
  por_material: ContagemCatalogo[];
  por_setor: ContagemCatalogo[];
  tendencia_7_dias: ContagemDiaria[];
  total_exames_mes_anterior: number;
  /** Culturas por data de coleta, últimos 30 dias (inclui hoje, ordem crescente). */
  coletas_30_dias: ContagemDiaria[];
  /** Todos os exames ativos, agrupados como no Painel de Acompanhamento. */
  distribuicao_status: ContagemStatus[];
}
