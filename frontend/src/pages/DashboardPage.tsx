import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import StatCard from "../components/StatCard";
import RankedListCard from "../components/RankedListCard";
import SectorGroupCard from "../components/SectorGroupCard";
import { obterResumoDashboard } from "../services/dashboardService";
import { ResumoDashboard } from "../types/dashboard";

interface KpiCardProps {
  titulo: string;
  valor: string | number;
  cor?: string;
}

function KpiCard({ titulo, valor, cor }: KpiCardProps) {
  return (
    <div className="mg-card" style={{ flex: 1, minWidth: 160 }}>
      <p style={{ margin: 0, fontSize: 13, color: "var(--mg-cinza-600)" }}>{titulo}</p>
      <h2 style={{ margin: "6px 0 0 0", fontSize: 28, color: cor }}>{valor}</h2>
    </div>
  );
}

const ALERTA_COR: Record<string, string> = {
  prazo: "var(--mg-erro)",
  resistencia: "var(--mg-alerta)",
  info: "var(--mg-informacao)",
};

export default function DashboardPage() {
  const [resumo, setResumo] = useState<ResumoDashboard | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    obterResumoDashboard()
      .then(setResumo)
      .catch(() =>
        setErro(
          "Não foi possível carregar o dashboard. Verifique se a API está rodando em " +
            "http://localhost:8000."
        )
      )
      .finally(() => setCarregando(false));
  }, []);

  return (
    <MainLayout titulo="Visão geral do laboratório">
      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}

      {!erro && carregando && <CarregandoBarras />}

      {!erro && !carregando && resumo && (
        <>
          <h3>Hoje</h3>
          <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
            <KpiCard titulo="Culturas Hoje" valor={resumo.culturas_hoje} />
            <KpiCard
              titulo="Aguardando Atualização"
              valor={resumo.aguardando_atualizacao}
              cor="var(--mg-neutro)"
            />
            <KpiCard
              titulo="Prazo Vencido"
              valor={resumo.prazo_vencido}
              cor="var(--mg-erro)"
            />
            <KpiCard
              titulo="Liberados Hoje"
              valor={resumo.liberados_hoje}
              cor="var(--mg-sucesso)"
            />
          </div>

          <h3>Este mês</h3>
          <div style={{ display: "flex", gap: 16 }}>
            <StatCard
              titulo="Total de culturas no mês"
              valor={resumo.total_exames_mes}
              estatisticaSecundaria={{
                rotulo: "Taxa de positividade",
                valor: `${resumo.taxa_positividade_mes}%`,
              }}
              serieTemporal={resumo.tendencia_7_dias}
            />
          </div>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 16 }}>
            <RankedListCard titulo="Por tipo de cultura" itens={resumo.por_tipo_cultura} />
            <RankedListCard titulo="Por material" itens={resumo.por_material} />
          </div>

          <h3 style={{ marginTop: 24 }}>Por setor</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))", gap: 12 }}>
            {resumo.por_setor.map((s) => (
              <SectorGroupCard key={s.nome} nome={s.nome} quantidade={s.quantidade} />
            ))}
            {resumo.por_setor.length === 0 && (
              <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
                Nenhum exame registrado este mês ainda.
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 24 }}>
            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Top Microrganismos (últimos 30 dias)</h3>
              {resumo.top_microrganismos.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
                  Ainda não há culturas positivas registradas.
                </p>
              ) : (
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  {resumo.top_microrganismos.map((m) => (
                    <li key={m.nome} style={{ fontSize: 14, marginBottom: 6 }}>
                      {m.nome} — <strong>{m.quantidade}</strong> ocorrência(s)
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Alertas Importantes</h3>
              {resumo.alertas.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
                  Nenhum alerta no momento.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {resumo.alertas.map((a, i) => (
                    <div
                      key={i}
                      style={{
                        borderLeft: `3px solid ${ALERTA_COR[a.tipo] ?? "var(--mg-informacao)"}`,
                        paddingLeft: 10,
                        fontSize: 14,
                      }}
                    >
                      {a.mensagem}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </MainLayout>
  );
}
