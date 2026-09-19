interface EstatisticaSecundaria {
  rotulo: string;
  valor: string;
}

interface StatCardProps {
  titulo: string;
  valor: string | number;
  corDestaque?: string;
  estatisticaSecundaria?: EstatisticaSecundaria;
}

/**
 * Número grande + título, com um traço colorido opcional no topo.
 * Base `.mg-card` (borda sutil, sem sombra) - reutilizável em qualquer
 * página que precise destacar um indicador numérico.
 */
export default function StatCard({ titulo, valor, corDestaque, estatisticaSecundaria }: StatCardProps) {
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
      <div>
        <p style={{ margin: 0, fontSize: 13, color: "var(--mg-cinza-600)" }}>{titulo}</p>
        <h2 style={{ margin: "6px 0 0 0", fontSize: 32 }}>{valor}</h2>
      </div>

      {estatisticaSecundaria && (
        <div style={{ textAlign: "right", borderLeft: "var(--mg-border-sutil)", paddingLeft: 16 }}>
          <p style={{ margin: 0, fontSize: 12, color: "var(--mg-cinza-600)" }}>
            {estatisticaSecundaria.rotulo}
          </p>
          <p style={{ margin: "4px 0 0 0", fontSize: 22, fontWeight: 600 }}>
            {estatisticaSecundaria.valor}
          </p>
        </div>
      )}
    </div>
  );
}
