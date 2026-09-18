import { api, ApiResponse, TOKEN_STORAGE_KEY } from "./api";
import { Usuario } from "../types/usuario";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

export async function login(loginValue: string, senha: string): Promise<string> {
  const body = new URLSearchParams();
  body.set("username", loginValue);
  body.set("password", senha);

  const response = await api.post<ApiResponse<TokenResponse>>("/api/auth/login", body, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  const token = response.data.data.access_token;
  localStorage.setItem(TOKEN_STORAGE_KEY, token);
  return token;
}

export function logout(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY);
}

export function obterTokenAtual(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export async function obterUsuarioLogado(): Promise<Usuario> {
  const response = await api.get<ApiResponse<Usuario>>("/api/auth/me");
  return response.data.data;
}
