import { api, ApiResponse } from "./api";
import { Tenant, TenantComAdmin, TenantCreate, TenantListagem, TenantUpdate } from "../types/tenant";

export async function listarTenants(): Promise<TenantListagem> {
  const response = await api.get<ApiResponse<TenantListagem>>("/api/tenants");
  return response.data.data;
}

export async function criarTenant(dados: TenantCreate): Promise<TenantComAdmin> {
  const response = await api.post<ApiResponse<TenantComAdmin>>("/api/tenants", dados);
  return response.data.data;
}

export async function atualizarTenant(id: string, dados: TenantUpdate): Promise<Tenant> {
  const response = await api.put<ApiResponse<Tenant>>(`/api/tenants/${id}`, dados);
  return response.data.data;
}
