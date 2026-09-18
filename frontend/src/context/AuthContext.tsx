import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import {
  login as loginService,
  logout as logoutService,
  obterTokenAtual,
  obterUsuarioLogado,
} from "../services/authService";
import { Usuario } from "../types/usuario";

interface AuthContextValue {
  usuario: Usuario | null;
  carregando: boolean;
  autenticado: boolean;
  login: (login: string, senha: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [carregando, setCarregando] = useState(true);

  async function carregarUsuario() {
    const token = obterTokenAtual();
    if (!token) {
      setUsuario(null);
      setCarregando(false);
      return;
    }
    try {
      const usuarioAtual = await obterUsuarioLogado();
      setUsuario(usuarioAtual);
    } catch {
      setUsuario(null);
    } finally {
      setCarregando(false);
    }
  }

  // Carrega a sessão (se houver token salvo) uma única vez, na montagem do provider.
  useEffect(() => {
    carregarUsuario();
  }, []);

  async function login(loginValue: string, senha: string) {
    await loginService(loginValue, senha);
    await carregarUsuario();
  }

  function logout() {
    logoutService();
    setUsuario(null);
  }

  return (
    <AuthContext.Provider
      value={{ usuario, carregando, autenticado: Boolean(usuario), login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth precisa ser usado dentro de um AuthProvider");
  }
  return context;
}
