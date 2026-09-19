interface CarregandoBarrasProps {
  rotulo?: string
  tamanho?: 'pequeno' | 'padrao'
}

export function CarregandoBarras({ rotulo, tamanho = 'padrao' }: CarregandoBarrasProps) {
  return (
    <div className={`carregando-barras carregando-barras--${tamanho}`} role="status" aria-live="polite">
      <span className="carregando-barras__pista">
        <span className="carregando-barras__barra" />
        <span className="carregando-barras__barra" />
        <span className="carregando-barras__barra" />
        <span className="carregando-barras__barra" />
      </span>
      {rotulo ? (
        <span className="carregando-barras__rotulo">{rotulo}</span>
      ) : (
        <span className="visualmente-oculto">Carregando</span>
      )}
    </div>
  )
}

export default CarregandoBarras
