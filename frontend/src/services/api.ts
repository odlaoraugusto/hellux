import axios, { AxiosError } from "axios";

export const TOKEN_STORAGE_KEY = "hellux_token";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Anexa o token JWT (quando existir) em toda requisição.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_STORAGE_KEY);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Se a sessão expirar/for inválida (401), limpa o token guardado.
// A navegação para a tela de login é feita pelo ProtectedRoute, que
// reage à ausência de token no próximo carregamento/consulta.
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem(TOKEN_STORAGE_KEY);
    }
    return Promise.reject(error);
  }
);

/**
 * Envelope de resposta padrão da API Hellux, conforme o contrato
 * definido no Documento Mestre (seção 8 - Padrão da API).
 */
export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T;
}

export interface ApiErrorResponse {
  success: false;
  message: string;
  errors: string[];
}

/**
 * Extrai a mensagem de erro do contrato padrão da API a partir de um erro
 * do axios, sem precisar tipar o catch como `any`.
 */
export function extrairMensagemErro(err: unknown, fallback: string): string {
  if (axios.isAxiosError(err)) {
    const mensagem = (err.response?.data as { message?: string } | undefined)?.message;
    if (mensagem) return mensagem;
  }
  return fallback;
}

/**
 * Extrai a mensagem de erro de uma requisição feita com `responseType:
 * "blob"` (usado nos downloads de relatório).
 *
 * Dois problemas específicos desse tipo de requisição, que não acontecem
 * numa chamada JSON comum:
 * 1. Quando a API responde com um erro (ex.: parâmetro inválido), o corpo
 *    ainda chega como Blob (por causa do responseType) - `extrairMensagemErro`
 *    normal não consegue ler `err.response.data.message` porque `data` é um
 *    Blob, não um objeto já parseado. Aqui o Blob é lido e parseado manualmente.
 * 2. Se a requisição nunca chegar a ter uma resposta (`err.response` ausente),
 *    o motivo mais comum não é falha de conexão - é alguma extensão do
 *    navegador (gerenciador de downloads como IDM) interceptando e cancelando
 *    a requisição original para baixar o arquivo por conta própria. Nesse
 *    caso o arquivo pode já ter sido salvo pela extensão, então o aviso é
 *    mais orientativo do que um erro definitivo.
 */
export async function extrairMensagemErroDownload(err: unknown): Promise<string> {
  if (axios.isAxiosError(err)) {
    const dados = err.response?.data;
    if (dados instanceof Blob && dados.type.includes("json")) {
      try {
        const corpo = JSON.parse(await dados.text()) as { message?: string };
        if (corpo.message) return corpo.message;
      } catch {
        // Corpo do erro não era o JSON esperado - segue para o aviso genérico.
      }
    }
    if (!err.response) {
      return (
        "O download não chegou a ser concluído pelo navegador. Se você usa um " +
        "gerenciador de downloads (ex.: IDM), verifique sua pasta de Downloads - " +
        "ele pode já ter capturado o arquivo. Caso contrário, confira sua conexão " +
        "e tente novamente."
      );
    }
  }
  return "Não foi possível baixar o relatório.";
}
