import { NavLink } from "react-router-dom";
import { NAV_ITEMS } from "../router/navItems";
import HelluxIcon from "./HelluxIcon";

export default function Sidebar() {
  return (
    <aside
      style={{
        width: 240,
        background: "var(--mg-sidebar-bg)",
        color: "#fff",
        display: "flex",
        flexDirection: "column",
        padding: "20px 14px",
        flexShrink: 0,
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "0 8px 24px 8px" }}>
        <HelluxIcon size={34} variante="negativo" />
        <div>
          <div style={{ fontWeight: 700, fontSize: 16, lineHeight: 1.1, color: "#fff" }}>
            Hellux
          </div>
          <div style={{ fontSize: 10, color: "var(--mg-cinza-400)" }}>
            Gestão Microbiológica
          </div>
        </div>
      </div>

      <nav style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {NAV_ITEMS.map((item) => {
          const Icone = item.icon;
          return (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            style={({ isActive }) => ({
              display: "flex",
              alignItems: "center",
              gap: 10,
              padding: "10px 12px",
              borderRadius: "var(--mg-radius-sm)",
              fontSize: 14,
              color: isActive ? "#fff" : "#cbd5e1",
              background: isActive ? "rgba(255,255,255,0.14)" : "transparent",
              fontWeight: isActive ? 600 : 400,
            })}
          >
            <Icone size={20} strokeWidth={2} />
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
    </aside>
  );
}
