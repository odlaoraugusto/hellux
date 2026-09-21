export type PerfilUsuario = "ADMIN" | "BIOMEDICO" | "TECNICO" | "VISUALIZADOR" | "SUPER_ADMIN";

export interface Usuario {
  id: string;
  tenant_id: string | null;
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
  /**
   * Só é usado quando quem cadastra é um SUPER_ADMIN (que não tem tenant
   * próprio) - para os demais perfis, o backend resolve o tenant sozinho
   * a partir de quem está autenticado.
   */
  tenant_id?: string;
}

export interface UsuarioUpdateData {
  nome?: string;
  perfil?: PerfilUsuario;
  senha?: string;
}
