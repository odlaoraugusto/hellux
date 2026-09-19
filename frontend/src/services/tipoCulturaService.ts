import { api, ApiResponse } from "./api";
import { TipoCultura, TipoCulturaFormData, TipoCulturaListagem } from "../types/tipoCultura";

export async function listarTiposCultura(): Promise<TipoCulturaListagem> {
  const response = await api.get<ApiResponse<TipoCulturaListagem>>("/api/tipos-cultura");
  return response.data.data;
}

export async function criarTipoCultura(dados: TipoCulturaFormData): Promise<TipoCultura> {
  const response = await api.post<ApiResponse<TipoCultura>>("/api/tipos-cultura", dados);
  return response.data.data;
}

export async function atualizarTipoCultura(
  id: string,
  dados: Partial<TipoCulturaFormData>
): Promise<TipoCultura> {
  const response = await api.put<ApiResponse<TipoCultura>>(`/api/tipos-cultura/${id}`, dados);
  return response.data.data;
}

export async function removerTipoCultura(id: string): Promise<void> {
  await api.delete(`/api/tipos-cultura/${id}`);
}
