import { FormEvent, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import HelluxIcon from "../components/HelluxIcon";
import { extrairMensagemErro } from "../services/api";

export default function LoginPage() {
  const { login, autenticado, carregando } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [loginValue, setLoginValue] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [entrando, setEntrando] = useState(false);
  const [manterConectado, setManterConectado] = useState(false);
  const [mostrarAjudaSenha, setMostrarAjudaSenha] = useState(false);

  if (!carregando && autenticado) {
    const destino = (location.state as { from?: string })?.from ?? "/";
    return <Navigate to={destino} replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setEntrando(true);
    try {
      await login(loginValue, senha);
      navigate("/");
    } catch (err: unknown) {
      setErro(extrairMensagemErro(err, "Não foi possível entrar. Tente novamente."));
    } finally {
      setEntrando(false);
    }
  }

  return (
    <div className="mg-login-container" style={{ fontFamily: "var(--mg-font-family)" }}>
      {/* Painel esquerdo - identidade da marca */}
      <div className="mg-login-painel-marca">
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 40 }}>
          <HelluxIcon size={40} variante="negativo" />
          <span style={{ fontWeight: 700, fontSize: 20, lineHeight: 1, color: "#fff" }}>
            Hellux
          </span>
        </div>

        <h1 style={{ fontSize: 34, fontWeight: 700, lineHeight: 1.25, margin: "0 0 16px 0" }}>
          Transformando dados microbiológicos em decisões.
        </h1>

        <p style={{ fontSize: 15, color: "#e2e8f0", lineHeight: 1.6, margin: 0, maxWidth: 440 }}>
          Plataforma inteligente para gestão da microbiologia hospitalar: da coleta da amostra
          aos indicadores da CCIH, em um só lugar.
        </p>
      </div>

      {/* Painel direito - formulário */}
      <div className="mg-login-painel-form">
        <div style={{ width: "100%", maxWidth: 400 }}>
          <span className="mg-badge mg-badge-sucesso" style={{ marginBottom: 20, display: "inline-block" }}>
            • Ambiente seguro
          </span>

          <h2 style={{ fontSize: 26, margin: "0 0 8px 0" }}>Bem-vindo de volta</h2>
          <p style={{ margin: "0 0 24px 0", fontSize: 14, color: "var(--mg-cinza-600)" }}>
            Acesse sua conta para continuar a gestão microbiológica.
          </p>

          <form onSubmit={handleSubmit}>
            {erro && (
              <p style={{ color: "var(--mg-erro)", fontSize: 14, marginTop: 0 }}>{erro}</p>
            )}

            <div className="mg-field" style={{ marginBottom: 14 }}>
              <label>Usuário</label>
              <input
                type="text"
                required
                autoFocus
                value={loginValue}
                onChange={(e) => setLoginValue(e.target.value)}
                placeholder="usuario"
              />
            </div>

            <div className="mg-field" style={{ marginBottom: 12 }}>
              <label>Senha</label>
              <input
                type="password"
                required
                value={senha}
                onChange={(e) => setSenha(e.target.value)}
              />
            </div>

            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 20,
                fontSize: 13,
              }}
            >
              <label style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--mg-cinza-600)" }}>
                <input
                  type="checkbox"
                  checked={manterConectado}
                  onChange={(e) => setManterConectado(e.target.checked)}
                />
                Manter conectado
              </label>

              <button
                type="button"
                onClick={() => setMostrarAjudaSenha((atual) => !atual)}
                style={{
                  background: "none",
                  border: "none",
                  padding: 0,
                  color: "var(--mg-primaria)",
                  fontWeight: 500,
                  fontSize: 13,
                }}
              >
                Esqueci minha senha
              </button>
            </div>

            {mostrarAjudaSenha && (
              <p style={{ fontSize: 12, color: "var(--mg-cinza-600)", marginTop: -12, marginBottom: 16 }}>
                Entre em contato com o administrador do sistema para redefinir sua senha.
              </p>
            )}

            <button
              className="mg-btn mg-btn-primary"
              type="submit"
              disabled={entrando}
              style={{ width: "100%", justifyContent: "center" }}
            >
              {entrando ? "Entrando..." : "Entrar"}
            </button>
          </form>

          <p style={{ fontSize: 12, color: "var(--mg-cinza-400)", textAlign: "center", marginTop: 24 }}>
            Primeiro acesso? Cadastre-se pela API (POST /api/usuarios) - o primeiro usuário
            criado se torna administrador automaticamente.
          </p>
          <p style={{ fontSize: 11, color: "var(--mg-cinza-400)", textAlign: "center", marginTop: 6 }}>
            Hellux &copy; {new Date().getFullYear()} · v1.2 · Ambiente hospitalar
          </p>
        </div>
      </div>
    </div>
  );
}
