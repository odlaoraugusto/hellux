import { useEffect, useState } from "react";
import { AlarmClock, CheckCircle2, Clock, FlaskConical, type LucideIcon } from "lucide-react";
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
  icone: LucideIcon;
  /** Sufixo dos tokens de status (`--mg-st-<tom>` / `--mg-st-<tom>-bg`); sem ele usa a cor primária. */
  tom?: string;
  nota?: string;
}

function KpiCard({ titulo, valor, icone: Icone, tom, nota }: KpiCardProps) {
  return (
    <div className="mg-tile">
      <div className="mg-tile-top">
        <span className="mg-tile-rotulo">{titulo}</span>
        <span
          className="mg-tile-icone"
          style={{
            background: tom ? `var(--mg-st-${tom}-bg)` : "var(--mg-primaria-tint)",
            color: tom ? `var(--mg-st-${tom})` : "var(--mg-primaria)",
          }}
        >
          <Icone size={17} strokeWidth={2} />
        </span>
      </div>
      <div className="mg-tile-valor">{valor}</div>
      {nota && <span className="mg-tile-nota">{nota}</span>}
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
      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 13 }}>{erro}</p>}

      {!erro && carregando && <CarregandoBarras />}

      {!erro && !carregando && resumo && (
        <>
          <h3>Hoje</h3>
          <div className="mg-tiles">
            <KpiCard titulo="Culturas Hoje" valor={resumo.culturas_hoje} icone={FlaskConical} />
            <KpiCard
              titulo="Aguardando Atualização"
              valor={resumo.aguardando_atualizacao}
              icone={Clock}
              tom="andamento"
              nota="triagem ou resultado parcial"
            />
            <KpiCard
              titulo="Prazo Vencido"
              valor={resumo.prazo_vencido}
              icone={AlarmClock}
              tom="positiva"
            />
            <KpiCard
              titulo="Liberados Hoje"
              valor={resumo.liberados_hoje}
              icone={CheckCircle2}
              tom="negativa"
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
              <p style={{ color: "var(--mg-cinza-600)", fontSize: 13 }}>
                Nenhum exame registrado este mês ainda.
              </p>
            )}
          </div>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginTop: 20 }}>
            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Top Microrganismos (últimos 30 dias)</h3>
              {resumo.top_microrganismos.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 13 }}>
                  Ainda não há culturas positivas registradas.
                </p>
              ) : (
                <ul style={{ paddingLeft: 18, margin: 0 }}>
                  {resumo.top_microrganismos.map((m) => (
                    <li key={m.nome} style={{ fontSize: 13, marginBottom: 5 }}>
                      {m.nome} — <strong>{m.quantidade}</strong> ocorrência(s)
                    </li>
                  ))}
                </ul>
              )}
            </div>

            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Alertas Importantes</h3>
              {resumo.alertas.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 13 }}>
                  Nenhum alerta no momento.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {resumo.alertas.map((a, i) => (
                    <div
                      key={i}
                      style={{
                        borderLeft: `3px solid ${ALERTA_COR[a.tipo] ?? "var(--mg-informacao)"}`,
                        paddingLeft: 10,
                        fontSize: 13,
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
