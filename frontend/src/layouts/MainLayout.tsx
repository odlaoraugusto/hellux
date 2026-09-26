import { ReactNode, useState } from "react";
import Sidebar from "../components/Sidebar";
import Topbar from "../components/Topbar";

interface MainLayoutProps {
  titulo: string;
  subtitulo?: string;
  children: ReactNode;
}

export default function MainLayout({ titulo, subtitulo, children }: MainLayoutProps) {
  const [sidebarAberta, setSidebarAberta] = useState(false);

  return (
    <>
      {/* Fundo decorativo do layout v2 (manchas desfocadas + grade de pontos). */}
      <div className="mg-backdrop" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="mg-app-shell">
        <Sidebar aberta={sidebarAberta} onFechar={() => setSidebarAberta(false)} />
        {sidebarAberta && (
          <div className="mg-sidebar-overlay" onClick={() => setSidebarAberta(false)} />
        )}
        <div className="mg-main">
          <Topbar titulo={titulo} subtitulo={subtitulo} onAbrirMenu={() => setSidebarAberta(true)} />
          <div className="mg-content">{children}</div>
        </div>
      </div>
    </>
  );
}
