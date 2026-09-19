import { ContagemCatalogo } from "../types/dashboard";

interface RankedListCardProps {
  titulo: string;
  itens: ContagemCatalogo[];
}

const MAX_ITENS = 5;
const OPACIDADE_POR_POSICAO = [1, 0.8, 0.65, 0.5, 0.4];

/**
 * Título + lista de até 5 itens como barras horizontais (uma cor só,
 * opacidade decrescente por posição). Se houver mais de 5 itens, agrupa
 * o restante numa linha final "+N outros".
 */
export default function RankedListCard({ titulo, itens }: RankedListCardProps) {
  const visiveis = itens.slice(0, MAX_ITENS);
  const restantes = itens.slice(MAX_ITENS);
  const somaRestantes = restantes.reduce((soma, item) => soma + item.quantidade, 0);
  const maiorValor = Math.max(1, ...visiveis.map((item) => item.quantidade));

  return (
    <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
      <h3 style={{ marginTop: 0 }}>{titulo}</h3>

      {itens.length === 0 ? (
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>Nenhum dado este mês.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {visiveis.map((item, i) => (
            <div key={item.nome} style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span
                style={{
                  flex: "0 0 120px",
                  fontSize: 13,
                  color: "var(--mg-texto)",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
                title={item.nome}
              >
                {item.nome}
              </span>
              <div style={{ flex: 1, background: "var(--mg-cinza-100)", borderRadius: 4, height: 10 }}>
                <div
                  style={{
                    width: `${(item.quantidade / maiorValor) * 100}%`,
                    height: "100%",
                    borderRadius: 4,
                    background: "var(--mg-primaria)",
                    opacity: OPACIDADE_POR_POSICAO[i] ?? 0.4,
                  }}
                />
              </div>
              <span
                style={{
                  flex: "0 0 auto",
                  fontSize: 13,
                  fontWeight: 600,
                  fontVariantNumeric: "tabular-nums",
                  minWidth: 24,
                  textAlign: "right",
                }}
              >
                {item.quantidade}
              </span>
            </div>
          ))}

          {restantes.length > 0 && (
            <p style={{ margin: "4px 0 0 0", fontSize: 12, color: "var(--mg-cinza-600)" }}>
              +{restantes.length} outros ({somaRestantes})
            </p>
          )}
        </div>
      )}
    </div>
  );
}
