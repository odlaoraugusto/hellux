import { Antimicrobiano } from "./antimicrobiano";
import { Material } from "./material";
import { Microrganismo } from "./microrganismo";
import { Paciente } from "./paciente";
import { Setor } from "./setor";
import { TipoCultura } from "./tipoCultura";

/**
 * Espelha `app/schemas/exame.py` do backend (fluxo de Exame unificado -
 * Fase 1/2). `Exame` é a entidade "dona" de todo o fluxo: resolve o
 * paciente por prontuário, e grava o pedido + resultado + isolados +
 * antibiograma numa única operação.
 */

export type StatusExame =
  | "AGUARDANDO_TRIAGEM"
  | "NEGATIVO_PARCIAL"
  | "POSITIVO_PARCIAL"
  | "NEGATIVO"
  | "POSITIVO"
  | "CONTAMINACAO";

export const STATUS_EXAME_OPCOES: StatusExame[] = [
  "AGUARDANDO_TRIAGEM",
  "NEGATIVO_PARCIAL",
  "POSITIVO_PARCIAL",
  "NEGATIVO",
  "POSITIVO",
  "CONTAMINACAO",
];

export const STATUS_EXAME_LABELS: Record<StatusExame, string> = {
  AGUARDANDO_TRIAGEM: "Aguardando triagem",
  NEGATIVO_PARCIAL: "Negativo parcial",
  POSITIVO_PARCIAL: "Positivo parcial",
  NEGATIVO: "Negativo",
  POSITIVO: "Positivo",
  CONTAMINACAO: "Contaminação",
};

export const STATUS_EXAME_BADGE_CLASSNAME: Record<StatusExame, string> = {
  AGUARDANDO_TRIAGEM: "mg-badge-info",
  NEGATIVO_PARCIAL: "mg-badge-alerta",
  POSITIVO_PARCIAL: "mg-badge-alerta",
  NEGATIVO: "mg-badge-sucesso",
  POSITIVO: "mg-badge-erro",
  CONTAMINACAO: "mg-badge-erro",
};

// Estados "em andamento" (ainda não finalizados) - espelha
// STATUS_EM_ANDAMENTO do backend (app/models/exame.py).
export const STATUS_EM_ANDAMENTO: StatusExame[] = [
  "AGUARDANDO_TRIAGEM",
  "NEGATIVO_PARCIAL",
  "POSITIVO_PARCIAL",
];

// Status a partir dos quais é possível lançar isolados - espelha
// STATUS_POSITIVO do backend.
export const STATUS_PERMITE_ISOLADOS: StatusExame[] = ["POSITIVO_PARCIAL", "POSITIVO"];

// Status finais aceitos pela ação de "Liberar" na listagem - o único jeito
// de finalizar um exame hoje é um PUT com um desses três valores.
export const STATUS_LIBERACAO_OPCOES: StatusExame[] = ["NEGATIVO", "POSITIVO", "CONTAMINACAO"];

export type MecanismoResistencia =
  | "NENHUM"
  | "MRSA"
  | "ESBL"
  | "CARBAPENEMASE_KPC"
  | "VRE"
  | "D_TESTE_POSITIVO"
  | "OUTRO";

export const MECANISMO_RESISTENCIA_OPCOES: MecanismoResistencia[] = [
  "NENHUM",
  "MRSA",
  "ESBL",
  "CARBAPENEMASE_KPC",
  "VRE",
  "D_TESTE_POSITIVO",
  "OUTRO",
];

export const MECANISMO_RESISTENCIA_LABELS: Record<MecanismoResistencia, string> = {
  NENHUM: "Nenhum",
  MRSA: "MRSA",
  ESBL: "ESBL",
  CARBAPENEMASE_KPC: "Carbapenemase (KPC)",
  VRE: "VRE",
  D_TESTE_POSITIVO: "D-teste positivo",
  OUTRO: "Outro",
};

export type ResultadoSIR = "SENSIVEL" | "INTERMEDIARIO" | "RESISTENTE";

export const RESULTADO_SIR_OPCOES: ResultadoSIR[] = ["SENSIVEL", "INTERMEDIARIO", "RESISTENTE"];

export const RESULTADO_SIR_LABELS: Record<ResultadoSIR, string> = {
  SENSIVEL: "Sensível (S)",
  INTERMEDIARIO: "Intermediário (I)",
  RESISTENTE: "Resistente (R)",
};

export interface ExameAntibiogramaIn {
  antimicrobiano_id: string;
  resultado: ResultadoSIR;
}

export interface ExameAntibiogramaOut {
  antimicrobiano: Antimicrobiano;
  resultado: ResultadoSIR;
}

export interface ExameIsoladoIn {
  microrganismo_id: string;
  mecanismo_resistencia: MecanismoResistencia;
  nao_realizado_tecnico: boolean;
  motivo_dispensa_tsa?: string | null;
  antibiograma: ExameAntibiogramaIn[];
}

export interface ExameIsoladoOut {
  id: string;
  microrganismo: Microrganismo;
  mecanismo_resistencia: MecanismoResistencia;
  nao_realizado_tecnico: boolean;
  motivo_dispensa_tsa: string | null;
  antibiograma: ExameAntibiogramaOut[];
}

export interface ExameCreate {
  paciente_prontuario: string;
  paciente_nome: string;
  setor_id?: string | null;
  tipo_cultura_id: string;
  material_id: string;
  data_coleta?: string | null;
  previsao_liberacao?: string | null;
  status: StatusExame;
  identificacao_preliminar?: string | null;
  observacoes?: string | null;
  isolados: ExameIsoladoIn[];
}

export interface ExameUpdate {
  setor_id?: string | null;
  tipo_cultura_id?: string | null;
  material_id?: string | null;
  data_coleta?: string | null;
  previsao_liberacao?: string | null;
  status?: StatusExame;
  identificacao_preliminar?: string | null;
  observacoes?: string | null;
  isolados?: ExameIsoladoIn[];
}

export interface ExameOut {
  id: string;
  paciente_id: string;
  paciente: Paciente | null;
  setor_id: string | null;
  setor: Setor | null;
  tipo_cultura_id: string;
  tipo_cultura: TipoCultura | null;
  material_id: string;
  material: Material | null;
  data_coleta: string;
  previsao_liberacao: string | null;
  status: StatusExame;
  identificacao_preliminar: string | null;
  observacoes: string | null;
  isolados: ExameIsoladoOut[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ExameListagem {
  total: number;
  page: number;
  page_size: number;
  items: ExameOut[];
}

/**
 * Preview extraído automaticamente de um laudo colado pelo usuário
 * (`POST /api/exames/{id}/importar-laudo`). `*_id` vem `null` quando o
 * nome citado no laudo não bateu exatamente com o catálogo do tenant -
 * nesse caso o usuário precisa escolher manualmente no formulário.
 */
export interface LaudoImportadoAntibiograma {
  antimicrobiano_id: string | null;
  antimicrobiano_nome_laudo: string;
  resultado: ResultadoSIR;
}

export interface LaudoImportadoIsolado {
  microrganismo_id: string | null;
  microrganismo_nome_laudo: string;
  mecanismo_resistencia: MecanismoResistencia;
  antibiograma: LaudoImportadoAntibiograma[];
}

export interface LaudoImportado {
  paciente_confere: boolean;
  prontuario_laudo: string | null;
  nome_paciente_laudo: string | null;
  isolados: LaudoImportadoIsolado[];
}
