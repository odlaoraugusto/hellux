import { api, ApiResponse } from "./api";
import { IndicadoresCCIH } from "../types/ccih";

export interface FiltroIndicadoresCCIH {
  dataInicio?: string;
  dataFim?: string;
  setorId?: string;
  tipoCulturaIds?: string[];
}

export async function obterIndicadoresCCIH(
  filtro: FiltroIndicadoresCCIH
): Promise<IndicadoresCCIH> {
  // Monta os params manualmente (mesmo padrão de `listarExames`) pra
  // garantir `?tipo_cultura_id=A&tipo_cultura_id=B` - o serializador
  // padrão do axios usaria `tipo_cultura_id[]=A&...`, que o FastAPI não
  // reconhece como o mesmo query param repetido.
  const params = new URLSearchParams();
  if (filtro.dataInicio) params.set("data_inicio", filtro.dataInicio);
  if (filtro.dataFim) params.set("data_fim", filtro.dataFim);
  if (filtro.setorId) params.set("setor_id", filtro.setorId);
  (filtro.tipoCulturaIds ?? []).forEach((id) => params.append("tipo_cultura_id", id));

  const response = await api.get<ApiResponse<IndicadoresCCIH>>("/api/ccih/indicadores", {
    params,
  });
  return response.data.data;
}
