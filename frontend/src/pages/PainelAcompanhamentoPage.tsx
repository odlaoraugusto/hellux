import { CSSProperties, KeyboardEvent, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { extrairMensagemErro } from "../services/api";
import { obterPainelAcompanhamento } from "../services/exameService";
import {
  PainelLinha,
  STATUS_PAINEL_LABELS,
  STATUS_PAINEL_OPCOES,
  STATUS_PAINEL_TOKEN,
  StatusPainel,
} from "../types/exame";
import { formatarNomeCatalogo } from "../utils/texto";

const MESES = [
  "Janeiro",
  "Fevereiro",
  "Março",
  "Abril",
  "Maio",
  "Junho",
  "Julho",
  "Agosto",
  "Setembro",
  "Outubro",
  "Novembro",
  "Dezembro",
];

const ANO_ATUAL = new Date().getFullYear();
const ANOS = Array.from({ length: 6 }, (_, i) => ANO_ATUAL - i);

/** Linha já com todos os campos em texto - é o que a tabela mostra e o que os filtros comparam. */
interface LinhaPainel {
  id: string;
  status: StatusPainel;
  prontuario: string;
  nome: string;
  solicitacao: string;
  dataColeta: string;
  exame: string;
  material: string;
  setor: string;
  microrganismos: string;
  resistencia: string;
  sensibilidade: string;
  sdd: string;
  mecanismos: string;
}

type ColunaTexto = Exclude<keyof LinhaPainel, "id" | "status">;

interface Coluna {
  campo: ColunaTexto;
  titulo: string;
  /** "lista" = filtro por <select> com os valores existentes; senão, busca por trecho. */
  filtro: "texto" | "lista";
  placeholder?: string;
}

const COLUNAS_ANTES_STATUS: Coluna[] = [
  { campo: "prontuario", titulo: "Prontuário", filtro: "texto" },
  { campo: "nome", titulo: "Nome", filtro: "texto" },
  { campo: "solicitacao", titulo: "Nº Solicitação", filtro: "texto" },
  { campo: "dataColeta", titulo: "Data Coleta", filtro: "texto", placeholder: "dd/mm/aaaa" },
  { campo: "exame", titulo: "Exame", filtro: "lista" },
  { campo: "material", titulo: "Material", filtro: "lista" },
  { campo: "setor", titulo: "Setor", filtro: "lista" },
];

const COLUNAS_DEPOIS_STATUS: Coluna[] = [
  { campo: "microrganismos", titulo: "Microrganismo(s)", filtro: "texto" },
  { campo: "resistencia", titulo: "Resistência", filtro: "texto" },
  { campo: "sensibilidade", titulo: "Sensibilidade", filtro: "texto" },
  { campo: "sdd", titulo: "Sens. c/ Exposição Aumentada", filtro: "texto" },
  { campo: "mecanismos", titulo: "Mecanismos de Resistência", filtro: "texto" },
];

const TOTAL_COLUNAS = COLUNAS_ANTES_STATUS.length + 1 + COLUNAS_DEPOIS_STATUS.length;

const VAZIO = "—";

function normalizar(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .trim();
}

function formatarData(iso: string): string {
  // Mesma referência (data UTC) usada pelo filtro de mês/ano do backend.
  const [ano, mes, dia] = iso.slice(0, 10).split("-");
  return `${dia}/${mes}/${ano}`;
}

function juntar(valores: string[], separador = ", "): string {
  return valores.length ? valores.join(separador) : VAZIO;
}

function paraLinha(item: PainelLinha): LinhaPainel {
  return {
    id: item.id,
    status: item.status_painel,
    prontuario: item.prontuario ?? VAZIO,
    nome: item.paciente_nome ?? VAZIO,
    solicitacao: item.numero_solicitacao ?? VAZIO,
    dataColeta: formatarData(item.data_coleta),
    exame: item.tipo_cultura ? formatarNomeCatalogo(item.tipo_cultura) : VAZIO,
    material: item.material ? formatarNomeCatalogo(item.material) : VAZIO,
    setor: item.setor ?? VAZIO,
    microrganismos: juntar(item.microrganismos, "; "),
    resistencia: juntar(item.resistencia),
    sensibilidade: juntar(item.sensibilidade),
    sdd: juntar(item.sensivel_exposicao_aumentada),
    mecanismos: juntar(item.mecanismos_resistencia),
  };
}

function Celula({ valor }: { valor: string }) {
  return <td>{valor === VAZIO ? <span className="mg-celula-vazia">{VAZIO}</span> : valor}</td>;
}

export default function PainelAcompanhamentoPage() {
  const navigate = useNavigate();
  const [mes, setMes] = useState<number | "">("");
  const [ano, setAno] = useState<number | "">(ANO_ATUAL);
  const [linhas, setLinhas] = useState<LinhaPainel[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [filtros, setFiltros] = useState<Partial<Record<ColunaTexto, string>>>({});
  const [statusVisiveis, setStatusVisiveis] = useState<Set<StatusPainel>>(
    () => new Set(STATUS_PAINEL_OPCOES)
  );

  useEffect(() => {
    let cancelado = false;
    setCarregando(true);
    setErro(null);
    obterPainelAcompanhamento(mes || undefined, ano || undefined)
      .then((dados) => {
        if (!cancelado) setLinhas(dados.items.map(paraLinha));
      })
      .catch((err) => {
        if (!cancelado) {
          setErro(extrairMensagemErro(err, "Não foi possível carregar o painel de acompanhamento."));
        }
      })
      .finally(() => {
        if (!cancelado) setCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [mes, ano]);

  // Opções dos filtros por lista vêm dos próprios dados do período.
  const opcoesLista = useMemo(() => {
    const opcoes: Partial<Record<ColunaTexto, string[]>> = {};
    for (const coluna of COLUNAS_ANTES_STATUS.filter((c) => c.filtro === "lista")) {
      opcoes[coluna.campo] = [...new Set(linhas.map((l) => l[coluna.campo]))]
        .filter((v) => v !== VAZIO)
        .sort((a, b) => a.localeCompare(b, "pt-BR"));
    }
    return opcoes;
  }, [linhas]);

  const contagemPorStatus = useMemo(() => {
    const contagem = Object.fromEntries(STATUS_PAINEL_OPCOES.map((s) => [s, 0])) as Record<
      StatusPainel,
      number
    >;
    linhas.forEach((l) => contagem[l.status]++);
    return contagem;
  }, [linhas]);

  const linhasFiltradas = useMemo(() => {
    const ativos = Object.entries(filtros)
      .filter(([, valor]) => valor)
      .map(([campo, valor]) => {
        const coluna = [...COLUNAS_ANTES_STATUS, ...COLUNAS_DEPOIS_STATUS].find(
          (c) => c.campo === campo
        );
        return { campo: campo as ColunaTexto, valor: valor as string, exato: coluna?.filtro === "lista" };
      });

    return linhas.filter((linha) => {
      if (!statusVisiveis.has(linha.status)) return false;
      return ativos.every(({ campo, valor, exato }) =>
        exato ? linha[campo] === valor : normalizar(linha[campo]).includes(normalizar(valor))
      );
    });
  }, [linhas, filtros, statusVisiveis]);

  const temFiltro =
    mes !== "" ||
    ano !== "" ||
    Object.values(filtros).some(Boolean) ||
    statusVisiveis.size !== STATUS_PAINEL_OPCOES.length;

  function alterarFiltro(campo: ColunaTexto, valor: string) {
    setFiltros((prev) => ({ ...prev, [campo]: valor }));
  }

  function alternarStatus(status: StatusPainel) {
    setStatusVisiveis((prev) => {
      const proximo = new Set(prev);
      if (proximo.has(status)) proximo.delete(status);
      else proximo.add(status);
      return proximo;
    });
  }

  function limparFiltros() {
    setFiltros({});
    setStatusVisiveis(new Set(STATUS_PAINEL_OPCOES));
    setMes("");
    setAno("");
  }

  function abrirExame(id: string) {
    navigate(`/exames/${id}/editar`);
  }

  function handleTeclaLinha(e: KeyboardEvent<HTMLTableRowElement>, id: string) {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      abrirExame(id);
    }
  }

  function renderFiltro(coluna: Coluna) {
    const valor = filtros[coluna.campo] ?? "";
    if (coluna.filtro === "lista") {
      return (
        <select
          aria-label={`Filtrar por ${coluna.titulo}`}
          value={valor}
          onChange={(e) => alterarFiltro(coluna.campo, e.target.value)}
        >
          <option value="">todos</option>
          {(opcoesLista[coluna.campo] ?? []).map((opcao) => (
            <option key={opcao} value={opcao}>
              {opcao}
            </option>
          ))}
        </select>
      );
    }
    return (
      <input
        type="text"
        aria-label={`Filtrar por ${coluna.titulo}`}
        placeholder={coluna.placeholder ?? "filtrar…"}
        value={valor}
        onChange={(e) => alterarFiltro(coluna.campo, e.target.value)}
      />
    );
  }

  return (
    <MainLayout
      subtitulo="Painel de Acompanhamento"
      titulo="Todas as culturas em processamento e finalizadas"
    >
      <div className="mg-painel-toolbar">
        <div className="mg-status-legenda" role="group" aria-label="Mostrar status">
          {STATUS_PAINEL_OPCOES.map((status) => {
            const token = STATUS_PAINEL_TOKEN[status];
            return (
              <button
                key={status}
                type="button"
                className="mg-status-chip"
                aria-pressed={statusVisiveis.has(status)}
                onClick={() => alternarStatus(status)}
                style={{
                  background: `var(--mg-st-${token}-solid)`,
                  color: `var(--mg-st-${token}-on-solid)`,
                }}
              >
                {STATUS_PAINEL_LABELS[status]}
                <b>{contagemPorStatus[status]}</b>
              </button>
            );
          })}
        </div>

        <div className="mg-painel-periodo">
          <div>
            <label htmlFor="painel-mes">Mês</label>
            <select
              id="painel-mes"
              value={mes}
              onChange={(e) => setMes(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">Todos os meses</option>
              {MESES.map((nome, i) => (
                <option key={nome} value={i + 1}>
                  {nome}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="painel-ano">Ano</label>
            <select
              id="painel-ano"
              value={ano}
              onChange={(e) => setAno(e.target.value ? Number(e.target.value) : "")}
            >
              <option value="">Todos os anos</option>
              {ANOS.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 13 }}>{erro}</p>}

      <div className="mg-painel-wrap">
        <div className="mg-painel-scroll">
          <table className="mg-painel-tabela">
            <thead>
              <tr>
                {COLUNAS_ANTES_STATUS.map((c) => (
                  <th key={c.campo}>{c.titulo}</th>
                ))}
                <th>Status / Resultado</th>
                {COLUNAS_DEPOIS_STATUS.map((c) => (
                  <th key={c.campo}>{c.titulo}</th>
                ))}
              </tr>
              <tr className="mg-painel-filtros">
                {COLUNAS_ANTES_STATUS.map((c) => (
                  <th key={c.campo}>{renderFiltro(c)}</th>
                ))}
                <th />
                {COLUNAS_DEPOIS_STATUS.map((c) => (
                  <th key={c.campo}>{renderFiltro(c)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {carregando ? (
                <tr>
                  <td className="mg-painel-vazio" colSpan={TOTAL_COLUNAS}>
                    <div style={{ display: "flex", justifyContent: "center" }}>
                      <CarregandoBarras rotulo="Carregando culturas..." />
                    </div>
                  </td>
                </tr>
              ) : linhasFiltradas.length === 0 ? (
                <tr>
                  <td className="mg-painel-vazio" colSpan={TOTAL_COLUNAS}>
                    Nenhuma cultura encontrada para os filtros aplicados.
                  </td>
                </tr>
              ) : (
                linhasFiltradas.map((linha) => {
                  const token = STATUS_PAINEL_TOKEN[linha.status];
                  return (
                    <tr
                      key={linha.id}
                      tabIndex={0}
                      title="Abrir exame"
                      onClick={() => abrirExame(linha.id)}
                      onKeyDown={(e) => handleTeclaLinha(e, linha.id)}
                      style={
                        {
                          "--linha-bg": `var(--mg-st-${token}-solid)`,
                          "--linha-texto": `var(--mg-st-${token}-on-solid)`,
                        } as CSSProperties
                      }
                    >
                      {COLUNAS_ANTES_STATUS.map((c) => (
                        <Celula key={c.campo} valor={linha[c.campo]} />
                      ))}
                      <td>
                        <span className="mg-status-pill">{STATUS_PAINEL_LABELS[linha.status]}</span>
                      </td>
                      {COLUNAS_DEPOIS_STATUS.map((c) => (
                        <Celula key={c.campo} valor={linha[c.campo]} />
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {!carregando && (
        <div className="mg-painel-rodape">
          {linhasFiltradas.length} de {linhas.length} culturas exibidas
          {temFiltro && (
            <>
              {" · "}
              <button type="button" className="mg-link-btn" onClick={limparFiltros}>
                limpar filtros
              </button>
            </>
          )}
        </div>
      )}
    </MainLayout>
  );
}
