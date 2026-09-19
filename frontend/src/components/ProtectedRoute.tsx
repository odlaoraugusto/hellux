import { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { CarregandoBarras } from "./CarregandoBarras";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children }: { children: ReactNode }) {
  const { autenticado, carregando } = useAuth();

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

  return <>{children}</>;
}
