interface SectorGroupCardProps {
  nome: string;
  quantidade: number;
}

/**
 * Item compacto de grid: nome do setor + número. A página é responsável
 * por montar o grid (`repeat(auto-fill, minmax(180px, 1fr))`).
 */
export default function SectorGroupCard({ nome, quantidade }: SectorGroupCardProps) {
  return (
    <div className="mg-card" style={{ padding: 12 }}>
      <p
        style={{
          margin: 0,
          fontSize: 12,
          color: "var(--mg-cinza-600)",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
        title={nome}
      >
        {nome}
      </p>
      <h3 style={{ margin: "4px 0 0 0", fontSize: 18 }}>{quantidade}</h3>
    </div>
  );
}
