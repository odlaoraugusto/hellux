export type Sexo = "MASCULINO" | "FEMININO" | "NAO_INFORMADO";

export interface Paciente {
  id: string;
  nome: string;
  prontuario: string;
  data_nascimento: string | null;
  sexo: Sexo;
  setor: string | null;
  leito: string | null;
  observacoes: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface PacienteListagem {
  total: number;
  page: number;
  page_size: number;
  items: Paciente[];
}

export interface PacienteFormData {
  nome: string;
  prontuario: string;
  data_nascimento?: string | null;
  sexo: Sexo;
  setor?: string | null;
  leito?: string | null;
  observacoes?: string | null;
}
