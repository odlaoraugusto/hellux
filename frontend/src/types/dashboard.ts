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
}
