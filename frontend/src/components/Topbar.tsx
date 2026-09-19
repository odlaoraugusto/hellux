import { Menu, Search } from "lucide-react";
import { useAuth } from "../context/AuthContext";

interface TopbarProps {
  titulo: string;
  subtitulo?: string;
  onAbrirMenu?: () => void;
}

export default function Topbar({ titulo, subtitulo, onAbrirMenu }: TopbarProps) {
  const { usuario, logout } = useAuth();
  const hora = new Date().getHours();
  const saudacao = hora < 12 ? "Bom dia" : hora < 18 ? "Boa tarde" : "Boa noite";
  const iniciais = usuario?.nome?.trim()?.charAt(0)?.toUpperCase() ?? "U";

  return (
    <header className="mg-topbar">
      <button
        type="button"
        className="mg-topbar-menu-btn"
        onClick={onAbrirMenu}
        aria-label="Abrir menu"
      >
        <Menu size={22} strokeWidth={2} />
      </button>

      <div style={{ minWidth: 0, flex: 1 }}>
        <h2 style={{ fontSize: 18, margin: 0, overflowWrap: "anywhere" }}>
          {subtitulo ?? `${saudacao}${usuario ? `, ${usuario.nome.split(" ")[0]}` : ""}! 👋`}
        </h2>
        <p style={{ margin: "2px 0 0 0", fontSize: 13, color: "var(--mg-cinza-600)" }}>
          {titulo}
        </p>
      </div>

      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div className="mg-topbar-search" style={{ position: "relative" }}>
          <Search
            size={16}
            strokeWidth={2}
            style={{
              position: "absolute",
              left: 12,
              top: "50%",
              transform: "translateY(-50%)",
              color: "var(--mg-cinza-400)",
              pointerEvents: "none",
            }}
          />
          <input
            type="text"
            placeholder="Buscar paciente, cultura..."
            style={{
              padding: "8px 14px 8px 36px",
              borderRadius: "var(--mg-radius-sm)",
              border: "1px solid var(--mg-cinza-200)",
              background: "var(--mg-cinza-100)",
              fontSize: 13,
              width: 220,
            }}
          />
        </div>

        {usuario && (
          <span className="mg-topbar-perfil" style={{ fontSize: 13, color: "var(--mg-cinza-600)" }}>
            {usuario.perfil}
          </span>
        )}
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: "50%",
            background: "var(--mg-secundaria)",
            color: "#fff",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontWeight: 600,
            fontSize: 14,
          }}
          title={usuario?.login}
        >
          {iniciais}
        </div>
        <button
          className="mg-btn mg-btn-outline"
          style={{ padding: "6px 12px", fontSize: 13 }}
          onClick={logout}
        >
          Sair
        </button>
      </div>
    </header>
  );
}
