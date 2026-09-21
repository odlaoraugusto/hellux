import { Usuario } from "./usuario";

/**
 * Espelha `backend/app/schemas/tenant.py`. Um tenant é um hospital-cliente;
 * só um usuário SUPER_ADMIN (sem tenant próprio) gerencia essa lista.
 */
export interface Tenant {
  id: string;
  nome_fantasia: string;
  razao_social: string | null;
  cnpj: string | null;
  logo_url: string | null;
  subtitulo_cabecalho: string | null;
  ativo: boolean;
  created_at: string;
  updated_at: string;
}

export interface TenantListagem {
  total: number;
  items: Tenant[];
}

export interface TenantCreate {
  nome_fantasia: string;
  razao_social?: string;
  cnpj?: string;
  logo_url?: string;
  subtitulo_cabecalho?: string;
  // O cadastro de um tenant já cria, na mesma chamada, o primeiro
  // usuário ADMIN dele.
  admin_nome: string;
  admin_login: string;
  admin_senha: string;
}

export interface TenantUpdate {
  nome_fantasia?: string;
  razao_social?: string;
  cnpj?: string;
  logo_url?: string;
  subtitulo_cabecalho?: string;
  ativo?: boolean;
}

/** Resposta de `POST /api/tenants`: o tenant recém-criado + seu primeiro admin. */
export interface TenantComAdmin {
  tenant: Tenant;
  admin: Usuario;
}
