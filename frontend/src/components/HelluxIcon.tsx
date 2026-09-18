interface HelluxIconProps {
  size?: number;
  className?: string;
  /**
   * "colorido" - símbolo original (navy + verde), usar sobre fundos claros.
   * "negativo" - símbolo branco sobre fundo navy arredondado (já com o
   *   próprio fundo embutido), usar sobre superfícies escuras (ex.: sidebar).
   */
  variante?: "colorido" | "negativo";
}

/**
 * Símbolo oficial do Hellux, vetorizado a partir do Manual de
 * Identidade Visual v1.0 (ver design/svg/). Usar sempre este componente em
 * vez de recriar o ícone ou usar emojis.
 */
export default function HelluxIcon({
  size = 32,
  className,
  variante = "colorido",
}: HelluxIconProps) {
  const src = variante === "negativo" ? "/simbolo-negativo.svg" : "/simbolo.svg";
  return (
    <img
      src={src}
      width={size}
      height={size}
      className={className}
      alt="Hellux"
      style={{ display: "block" }}
    />
  );
}
