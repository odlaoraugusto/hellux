import { api, ApiResponse } from "./api";
import { Usuario, UsuarioFormData, UsuarioListagem, UsuarioUpdateData } from "../types/usuario";

export async function listarUsuarios(page = 1, pageSize = 50): Promise<UsuarioListagem> {
  const response = await api.get<ApiResponse<UsuarioListagem>>("/api/usuarios", {
    params: { page, page_size: pageSize },
  });
  return response.data.data;
}

/**
 * Lista os usuários de um tenant específico - uso exclusivo do painel de
 * SUPER_ADMIN (que não tem tenant implícito e por isso precisa informar
 * qual tenant quer ver; sem isso a API devolveria usuários de todos os
 * tenants, o que essa tela nunca deve fazer).
 */
export async function listarUsuariosPorTenant(
  tenantId: string,
  page = 1,
  pageSize = 100
): Promise<UsuarioListagem> {
  const response = await api.get<ApiResponse<UsuarioListagem>>("/api/usuarios", {
    params: { tenant_id: tenantId, page, page_size: pageSize },
  });
  return response.data.data;
}

export async function criarUsuario(dados: UsuarioFormData): Promise<Usuario> {
  const response = await api.post<ApiResponse<Usuario>>("/api/usuarios", dados);
  return response.data.data;
}

export async function atualizarUsuario(
  id: string,
  dados: UsuarioUpdateData
): Promise<Usuario> {
  const response = await api.put<ApiResponse<Usuario>>(`/api/usuarios/${id}`, dados);
  return response.data.data;
}

export async function removerUsuario(id: string): Promise<void> {
  await api.delete(`/api/usuarios/${id}`);
}
