import { api, ApiResponse } from "./api";
import { ExameCreate, ExameListagem, ExameOut, ExameUpdate, StatusExame } from "../types/exame";

export async function listarExames(
  status?: StatusExame[],
  page = 1,
  pageSize = 20
): Promise<ExameListagem> {
  // Monta os params manualmente (em vez de passar `{ status, page, ... }`
  // direto pro axios) pra garantir `?status=A&status=B` - o serializador
  // padrão do axios usa `status[]=A&status[]=B`, que o FastAPI não
  // reconhece como o mesmo query param repetido.
  const params = new URLSearchParams();
  (status ?? []).forEach((s) => params.append("status", s));
  params.set("page", String(page));
  params.set("page_size", String(pageSize));

  const response = await api.get<ApiResponse<ExameListagem>>("/api/exames", { params });
  return response.data.data;
}

export async function obterExame(id: string): Promise<ExameOut> {
  const response = await api.get<ApiResponse<ExameOut>>(`/api/exames/${id}`);
  return response.data.data;
}

export async function criarExame(dados: ExameCreate): Promise<ExameOut> {
  const response = await api.post<ApiResponse<ExameOut>>("/api/exames", dados);
  return response.data.data;
}

export async function atualizarExame(id: string, dados: ExameUpdate): Promise<ExameOut> {
  const response = await api.put<ApiResponse<ExameOut>>(`/api/exames/${id}`, dados);
  return response.data.data;
}

export async function removerExame(id: string): Promise<void> {
  await api.delete(`/api/exames/${id}`);
}
