export interface TipoCultura {
  id: string;
  nome: string;
  descricao: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TipoCulturaListagem {
  total: number;
  items: TipoCultura[];
}

export interface TipoCulturaFormData {
  nome: string;
  descricao?: string | null;
}
