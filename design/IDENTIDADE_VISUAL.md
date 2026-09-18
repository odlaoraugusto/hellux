# Identidade Visual do Hellux

Fonte oficial: `manual/Hellux_Manual_de_Identidade_Visual.docx` (v1.0, Julho de 2026).
Este arquivo consolida as regras que o frontend (`frontend/src/styles/tokens.css`)
segue à risca. Sempre que o manual evoluir, atualizar os dois lugares juntos.

## Paleta de cores

| Uso | Cor | Hex |
|---|---|---|
| Primária | Azul | `#0F4C81` |
| Secundária | Verde | `#2E8B57` |
| Texto | Grafite | `#1F2937` |
| Fundo | Branco-gelo | `#F8FAFC` |
| Sucesso | Verde | `#22C55E` |
| Alerta | Laranja | `#F59E0B` |
| Erro | Vermelho | `#DC2626` |
| Informação | Azul | `#3B82F6` |
| Bordas/divisores | Cinza | `#E5E7EB` |

## Tipografia

Família: **Poppins** (pesos Bold 700 / SemiBold 600 / Medium 500 / Regular 400 / Light 300).
Carregada via Google Fonts em `frontend/index.html` e aplicada globalmente
em `frontend/src/styles/global.css` através da variável `--mg-font-family`.

Hierarquia recomendada pelo manual: Bold para títulos e KPIs, SemiBold para
subtítulos/botões, Medium para rótulos de campo/menu/badges, Regular para
texto corrido, Light para legendas pontuais.

## Iconografia

Ícones de menu e módulos usam a biblioteca **Lucide Icons** (traço 2px,
estilo outline), conforme a seção 9 do manual — substituíram os emojis
usados nas versões anteriores da interface.

## Logomarca

**Fonte oficial:** pacote de identidade visual v1.0 entregue pelo usuário,
re-extraído por vetorização direto do ícone oficial em alta resolução
(fidelidade total ao desenho aprovado), em `design/svg/` e `design/png/`:

- `hellux-simbolo-colorido.svg` — símbolo principal, colorido (azul +
  verde), fundo transparente. Copiado para `frontend/public/simbolo.svg`,
  fonte de verdade do favicon e do componente React `HelluxIcon`
  (variante `colorido`, padrão). Usar sobre fundos claros.
- `hellux-simbolo-negativo.svg` — símbolo branco sobre tile azul
  primário arredondado (532×532, já com o próprio fundo embutido). Copiado
  para `frontend/public/simbolo-negativo.svg`, usado nos ícones de
  aplicação e no componente `HelluxIcon` (variante `negativo`) para
  superfícies escuras, como a sidebar.
- `hellux-simbolo-monocromatico.svg` / `hellux-simbolo-monocromatico-negativo.svg`
  — variações em tom único (impressão P&B, carimbos, marca d'água); não
  usadas ao vivo na interface, mantidas como referência de marca.
- `hellux-logo-horizontal.svg` / `hellux-logo-vertical.svg` — lockup
  completo: símbolo + wordmark "Hellux" + tagline, com o texto como
  `<text font-family="Poppins">` real (não path). Para usar ao vivo na
  interface, inlinar o SVG diretamente no JSX/DOM em vez de referenciar via
  `<img src>`, para garantir que a fonte Poppins já carregada pela página
  seja aplicada.

Onde a marca aparece hoje no sistema:

- Favicon do navegador (`frontend/public/favicon.ico` + `simbolo.svg`) e
  ícones de instalação do app/PWA (`frontend/public/android192.png`,
  `ios180.png`, `apple-touch-icon-152/167.png`, `windows256.png`,
  `icone512.png`, `maskable-512.png`, referenciados em
  `site.webmanifest`/`index.html`).
- Sidebar (`HelluxIcon variante="negativo"`, fundo `--mg-sidebar-bg` =
  cor primária) e painel de marca da tela de Login (`HelluxIcon
  variante="negativo"` sobre fundo primário, layout split-screen).
- Cabeçalho do relatório PDF da CCIH (`backend/app/assets/logo.png`, a
  partir de `hellux-simbolo-colorido-1024.png`).

- Redução mínima: 24px em telas / 8mm em impressos — nunca usar o símbolo
  abaixo disso.
- Variações: colorida (padrão), negativa (fundo escuro), monocromática e
  monocromática negativa (usos institucionais/impressão P&B).

## Área de proteção e usos incorretos

- Respeitar a área de proteção ao redor do logo (unidade X, ver manual
  seção 3) — não encostar texto/bordas.
- Não alterar as cores oficiais, distorcer proporções, aplicar sombras,
  contornos adicionais ou alterar a tipografia do wordmark.
- Não aplicar a logo sobre fundos de baixo contraste ou imagens.
- Sempre usar os arquivos originais fornecidos — não recriar o símbolo a
  partir de capturas de tela ou reduções sucessivas.

## Aplicação em produto

- **Login:** split-screen — painel de marca à esquerda (cor primária,
  símbolo + wordmark, headline institucional, testemunho) e formulário à
  direita, fundo claro (ver `design/mockups/login-screen.png`).
- **Dashboard/navegação:** sidebar fixa na cor primária com os módulos do
  sistema, cabeçalho branco com saudação/data e avatar, área de conteúdo
  em fundo claro com cards brancos (ver `design/mockups/dashboard-structure.png`).

## Missão, visão e valores (contexto de produto)

- **Missão:** transformar dados microbiológicos em informações confiáveis
  para promover qualidade e segurança na saúde.
- **Visão:** ser referência em gestão laboratorial inteligente na América
  Latina.
- **Valores:** precisão, integração, inovação, transparência, segurança e
  compromisso com a vida.

Esses princípios orientam decisões de produto (ex.: por que o módulo CCIH
e a "IA silenciosa" do dashboard são prioridade desde a v1.0).
