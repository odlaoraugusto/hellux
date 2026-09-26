import { useEffect, useState } from "react";
import { Activity, Clock, FlaskConical, type LucideIcon } from "lucide-react";
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { obterResumoDashboard } from "../services/dashboardService";
import { ContagemDiaria, ResumoDashboard } from "../types/dashboard";
import { STATUS_PAINEL_LABELS, STATUS_PAINEL_TOKEN } from "../types/exame";

interface KpiCardProps {
  titulo: string;
  valor: string | number;
  icone: LucideIcon;
  /** Sufixo dos tokens de status (`--mg-st-<tom>` / `--mg-st-<tom>-bg`); sem ele usa a cor primária. */
  tom?: string;
  nota?: string;
  /** Cor da nota (ex.: variação positiva/negativa); padrão = texto suave. */
  corNota?: string;
}

function KpiCard({ titulo, valor, icone: Icone, tom, nota, corNota }: KpiCardProps) {
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
      {nota && (
        <span className="mg-tile-nota" style={corNota ? { color: corNota } : undefined}>
          {nota}
        </span>
      )}
    </div>
  );
}

function formatarDia(iso: string): string {
  const [, mes, dia] = iso.split("-");
  return `${dia}/${mes}`;
}

function variacaoMes(atual: number, anterior: number): { texto: string; cor?: string } {
  if (anterior === 0) return { texto: "sem culturas no mês anterior" };
  const pct = Math.round(((atual - anterior) / anterior) * 100);
  const sinal = pct > 0 ? "+" : "";
  return {
    texto: `${sinal}${pct}% vs. mês anterior`,
    cor: pct > 0 ? "var(--mg-st-negativa)" : pct < 0 ? "var(--mg-st-positiva)" : undefined,
  };
}

function TooltipColetas({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { payload: ContagemDiaria }[];
}) {
  if (!active || !payload?.length) return null;
  const { data, quantidade } = payload[0].payload;
  return (
    <div className="mg-chart-tooltip">
      <span>{formatarDia(data)}</span>
      <b>
        {quantidade} cultura{quantidade === 1 ? "" : "s"}
      </b>
    </div>
  );
}

function TooltipStatus({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { name: string; value: number }[];
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="mg-chart-tooltip">
      <span>{payload[0].name}</span>
      <b>{payload[0].value}</b>
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

  if (erro || carregando || !resumo) {
    return (
      <MainLayout titulo="Visão geral da produção de microbiologia">
        {erro && <p style={{ color: "var(--mg-erro)", fontSize: 13 }}>{erro}</p>}
        {!erro && <CarregandoBarras />}
      </MainLayout>
    );
  }

  const variacao = variacaoMes(resumo.total_exames_mes, resumo.total_exames_mes_anterior);
  const totalStatus = resumo.distribuicao_status.reduce((soma, s) => soma + s.quantidade, 0);
  const fatias = resumo.distribuicao_status.map((s) => ({
    name: STATUS_PAINEL_LABELS[s.status],
    value: s.quantidade,
    cor: `var(--mg-st-${STATUS_PAINEL_TOKEN[s.status]}-solid)`,
  }));
  const coletas = resumo.coletas_30_dias;
  const maxMicro = Math.max(1, ...resumo.top_microrganismos.map((m) => m.quantidade));

  return (
    <MainLayout titulo="Visão geral da produção de microbiologia">
      <div className="mg-tiles mg-tiles-3">
        <KpiCard
          titulo="Culturas no mês"
          valor={resumo.total_exames_mes}
          icone={FlaskConical}
          nota={variacao.texto}
          corNota={variacao.cor}
        />
        <KpiCard
          titulo="Taxa de positividade"
          valor={`${resumo.taxa_positividade_mes.toLocaleString("pt-BR")}%`}
          icone={Activity}
          tom="positiva"
          nota="no mês corrente"
        />
        <KpiCard
          titulo="Em processamento"
          valor={resumo.aguardando_atualizacao}
          icone={Clock}
          tom="andamento"
          nota="aguardando triagem ou resultado"
        />
      </div>

      <div className="mg-dash-grid">
        <div className="mg-card">
          <h3 className="mg-card-titulo">Culturas coletadas por dia</h3>
          <p className="mg-card-sub">Últimos 30 dias</p>
          <ResponsiveContainer width="100%" height={150}>
            <BarChart data={coletas} margin={{ top: 8, right: 0, bottom: 0, left: 0 }} barCategoryGap={2}>
              <XAxis
                dataKey="data"
                tickFormatter={formatarDia}
                ticks={coletas.length ? [coletas[0].data, coletas[coletas.length - 1].data] : []}
                interval="preserveStartEnd"
                axisLine={{ stroke: "var(--mg-borda)" }}
                tickLine={false}
                tick={{ fontSize: 10, fill: "var(--mg-texto-fraco)" }}
              />
              <Tooltip content={<TooltipColetas />} cursor={{ fill: "var(--mg-superficie-3)" }} />
              <Bar dataKey="quantidade" radius={[4, 4, 0, 0]} minPointSize={3} isAnimationActive={false}>
                {coletas.map((dia, i) => (
                  <Cell
                    key={dia.data}
                    fill={i === coletas.length - 1 ? "var(--mg-secundaria)" : "var(--mg-primaria)"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="mg-card">
          <h3 className="mg-card-titulo">Distribuição por status</h3>
          <p className="mg-card-sub">Todas as culturas ativas na base</p>
          <div className="mg-donut">
            <div className="mg-donut-grafico">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={totalStatus ? fatias : [{ name: "Sem culturas", value: 1, cor: "var(--mg-superficie-3)" }]}
                    dataKey="value"
                    innerRadius={46}
                    outerRadius={64}
                    startAngle={90}
                    endAngle={-270}
                    stroke="var(--mg-branco)"
                    strokeWidth={2}
                    isAnimationActive={false}
                  >
                    {(totalStatus ? fatias : [{ cor: "var(--mg-superficie-3)" }]).map((f, i) => (
                      <Cell key={i} fill={f.cor} />
                    ))}
                  </Pie>
                  {totalStatus > 0 && <Tooltip content={<TooltipStatus />} />}
                </PieChart>
              </ResponsiveContainer>
              <div className="mg-donut-centro">
                <b>{totalStatus}</b>
                <span>culturas</span>
              </div>
            </div>
            <ul className="mg-legenda">
              {fatias.map((f) => (
                <li key={f.name}>
                  <span className="mg-legenda-cor" style={{ background: f.cor }} />
                  {f.name}
                  <b>{f.value}</b>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      <div className="mg-dash-grid">
        <div className="mg-card">
          <h3 className="mg-card-titulo">Microrganismos mais isolados</h3>
          <p className="mg-card-sub">Top 6 · últimos 30 dias</p>
          {resumo.top_microrganismos.length === 0 ? (
            <p className="mg-card-sub">Ainda não há culturas positivas registradas.</p>
          ) : (
            <div className="mg-hbar">
              {resumo.top_microrganismos.map((m) => (
                <div
                  key={m.nome}
                  className="mg-hbar-linha"
                  title={`${m.nome}: ${m.quantidade} isolado(s)`}
                >
                  <span className="mg-hbar-nome">{m.nome}</span>
                  <span className="mg-hbar-trilho">
                    <span
                      className="mg-hbar-barra"
                      style={{ width: `${(m.quantidade / maxMicro) * 100}%` }}
                    />
                  </span>
                  <span className="mg-hbar-valor">{m.quantidade}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mg-card">
          <h3 className="mg-card-titulo">Alertas importantes</h3>
          <p className="mg-card-sub">Gerados automaticamente a partir dos exames</p>
          {resumo.alertas.length === 0 ? (
            <p style={{ color: "var(--mg-texto-suave)", fontSize: 13 }}>Nenhum alerta no momento.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 4 }}>
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
    </MainLayout>
  );
}
