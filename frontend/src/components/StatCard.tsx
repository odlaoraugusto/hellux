import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { ContagemDiaria } from "../types/dashboard";

interface EstatisticaSecundaria {
  rotulo: string;
  valor: string;
}

interface StatCardProps {
  titulo: string;
  valor: string | number;
  corDestaque?: string;
  estatisticaSecundaria?: EstatisticaSecundaria;
  /** Série dos últimos dias (ex.: 7 dias) - quando presente, renderiza uma mini área abaixo do número. */
  serieTemporal?: ContagemDiaria[];
}

/**
 * Número grande + título, com um traço colorido opcional no topo.
 * Base `.mg-card` (borda sutil, sem sombra) - reutilizável em qualquer
 * página que precise destacar um indicador numérico.
 */
export default function StatCard({
  titulo,
  valor,
  corDestaque,
  estatisticaSecundaria,
  serieTemporal,
}: StatCardProps) {
  return (
    <div
      className="mg-card"
      style={{
        flex: 1,
        minWidth: 220,
        borderTop: corDestaque ? `3px solid ${corDestaque}` : undefined,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 16,
      }}
    >
      <div style={{ flex: 1 }}>
        <p style={{ margin: 0, fontSize: 12, color: "var(--mg-cinza-600)" }}>{titulo}</p>
        <h2 style={{ margin: "5px 0 0 0", fontSize: 26 }}>{valor}</h2>

        {serieTemporal && serieTemporal.length > 0 && (
          <div style={{ marginTop: 10 }}>
            <ResponsiveContainer width="100%" height={44}>
              <AreaChart data={serieTemporal} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
                <Area
                  type="monotone"
                  dataKey="quantidade"
                  stroke="var(--mg-primaria)"
                  fill="var(--mg-primaria)"
                  fillOpacity={0.15}
                  strokeWidth={2}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {estatisticaSecundaria && (
        <div style={{ textAlign: "right", borderLeft: "var(--mg-border-sutil)", paddingLeft: 14 }}>
          <p style={{ margin: 0, fontSize: 11, color: "var(--mg-cinza-600)" }}>
            {estatisticaSecundaria.rotulo}
          </p>
          <p style={{ margin: "4px 0 0 0", fontSize: 18, fontWeight: 600 }}>
            {estatisticaSecundaria.valor}
          </p>
        </div>
      )}
    </div>
  );
}
