import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../router/navItems";
import HelluxIcon from "./HelluxIcon";

interface SidebarProps {
  aberta?: boolean;
  onFechar?: () => void;
}

// No desktop (ver breakpoint em global.css) a sidebar fica sempre visível,
// fixa (sticky) na lateral. No mobile ela vira um drawer fixo fora da tela,
// controlado por `aberta` (aciona a classe `mg-sidebar--aberta`, que só
// tem efeito dentro do media query mobile).
export default function Sidebar({ aberta = false, onFechar }: SidebarProps) {
  return (
    <aside className={`mg-sidebar${aberta ? " mg-sidebar--aberta" : ""}`}>
      <div className="mg-sidebar-brand">
        <HelluxIcon size={34} variante="negativo" />
        <div>
          <div className="mg-sidebar-brand-nome">Hellux</div>
          <div className="mg-sidebar-brand-tag">Gestão Microbiológica</div>
        </div>
      </div>

      <nav className="mg-sidebar-nav">
        {NAV_ITEMS.map((item) => {
          const Icone = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              onClick={onFechar}
              className={({ isActive }) => `mg-nav-item${isActive ? " active" : ""}`}
            >
              <Icone size={17} strokeWidth={2} />
              <span style={{ flex: 1 }}>{item.label}</span>
              {!item.implementado && (
                <span
                  style={{
                    fontSize: 9,
                    padding: "2px 6px",
                    borderRadius: 999,
                    background: "rgba(255,255,255,0.12)",
                    color: "var(--mg-cinza-400)",
                  }}
                >
                  em breve
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      <div className="mg-sidebar-foot">Sistema Inteligente de Gestão Microbiológica</div>
    </aside>
  );
}
