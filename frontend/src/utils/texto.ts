/**
 * Nomes de catálogo (TipoCultura, Material etc.) são texto livre por
 * tenant - alguns são cadastrados em SNAKE_CASE (ex.: "CULTURA_GERAL").
 * Troca `_` por espaço só pra exibição, sem mexer no valor armazenado.
 */
export function formatarNomeCatalogo(nome: string): string {
  return nome.replace(/_/g, " ");
}
