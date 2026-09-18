export type PerfilUsuario = "ADMIN" | "BIOMEDICO" | "TECNICO" | "VISUALIZADOR";

export interface Usuario {
  id: string;
  nome: string;
  login: string;
  perfil: PerfilUsuario;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface UsuarioListagem {
  total: number;
  page: number;
  page_size: number;
  items: Usuario[];
}

export interface UsuarioFormData {
  nome: string;
  login: string;
  senha: string;
  perfil: PerfilUsuario;
}

export interface UsuarioUpdateData {
  nome?: string;
  perfil?: PerfilUsuario;
  senha?: string;
}
