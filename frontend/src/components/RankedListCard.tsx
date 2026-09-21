import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { formatarNomeCatalogo } from "../utils/texto";

export interface ItemRankeado {
  nome: string;
  quantidade: number;
  /** Rótulo alternativo pro valor (ex.: "42%") - se ausente, mostra `quantidade`. */
  rotuloValor?: string;
}

interface RankedListCardProps {
  titulo: string;
  itens: ItemRankeado[];
}

const MAX_ITENS = 5;
const OPACIDADE_POR_POSICAO = [1, 0.8, 0.65, 0.5, 0.4];
const ALTURA_BARRA = 32;

/**
 * Título + gráfico de barras horizontais (recharts) com até 5 itens - uma
 * cor só, opacidade decrescente por posição (não multicor: os catálogos
 * de tipo de cultura/material são livres por tenant, cardinalidade
 * imprevisível - uma cor por categoria viraria ruído sem significado).
 * Se houver mais de 5 itens, agrupa o restante numa linha final "+N outros".
 */
export default function RankedListCard({ titulo, itens }: RankedListCardProps) {
  const visiveis = itens.slice(0, MAX_ITENS);
  const restantes = itens.slice(MAX_ITENS);
  const somaRestantes = restantes.reduce((soma, item) => soma + item.quantidade, 0);

  return (
    <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
      <h3 style={{ marginTop: 0 }}>{titulo}</h3>

      {itens.length === 0 ? (
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 13 }}>Nenhum dado este mês.</p>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={visiveis.length * ALTURA_BARRA}>
            <BarChart
              data={visiveis}
              layout="vertical"
              margin={{ top: 0, right: 24, bottom: 0, left: 0 }}
              barCategoryGap={10}
            >
              <XAxis type="number" hide allowDecimals={false} />
              <YAxis
                type="category"
                dataKey="nome"
                width={120}
                tickLine={false}
                axisLine={false}
                tick={{ fontSize: 11, fill: "var(--mg-texto)" }}
                tickFormatter={formatarNomeCatalogo}
              />
              <Tooltip
                cursor={{ fill: "var(--mg-cinza-100)" }}
                labelFormatter={(label: string) => formatarNomeCatalogo(label)}
                formatter={(value: number, _nome: string, item) => [
                  (item.payload as ItemRankeado).rotuloValor ?? value,
                  "Exames",
                ]}
                labelStyle={{ fontSize: 11, fontWeight: 600 }}
                contentStyle={{
                  fontSize: 12,
                  borderRadius: 8,
                  border: "1px solid var(--mg-cinza-200)",
                  boxShadow: "var(--mg-shadow-elevado)",
                }}
              />
              <Bar dataKey="quantidade" radius={[0, 4, 4, 0]} maxBarSize={16}>
                {visiveis.map((item, i) => (
                  <Cell
                    key={item.nome}
                    fill="var(--mg-primaria)"
                    fillOpacity={OPACIDADE_POR_POSICAO[i] ?? 0.4}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>

          {restantes.length > 0 && (
            <p style={{ margin: "8px 0 0 0", fontSize: 11, color: "var(--mg-cinza-600)" }}>
              +{restantes.length} outros ({somaRestantes})
            </p>
          )}
        </>
      )}
    </div>
  );
}
