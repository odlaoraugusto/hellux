import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { CarregandoBarras } from "./CarregandoBarras";
import { useAuth } from "../context/AuthContext";
import SuperAdminPage from "../pages/SuperAdminPage";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { autenticado, carregando, usuario } = useAuth();

  if (carregando) {
    return (
      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          height: "100vh",
          fontFamily: "var(--mg-font-family)",
        }}
      >
        <CarregandoBarras rotulo="Carregando..." />
      </div>
    );
  }

  if (!autenticado) {
    return <Navigate to="/login" replace />;
  }

  // Um SUPER_ADMIN não pertence a nenhum tenant e nunca deve navegar em
  // dado clínico do hospital - qualquer rota protegida vira o painel dele,
  // as páginas do hospital nem chegam a montar.
  if (usuario?.perfil === "SUPER_ADMIN") {
    return <SuperAdminPage />;
  }

  return <>{children}</>;
}
