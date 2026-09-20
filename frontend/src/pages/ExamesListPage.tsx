import { useEffect, useState } from "react";
import { Route, Routes, useLocation, useMatch, useNavigate, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import StatusExameBadge from "../components/StatusExameBadge";
import ExameFormPage from "./ExameFormPage";
import { atualizarExame, listarExames, removerExame } from "../services/exameService";
import { extrairMensagemErro } from "../services/api";
import { formatarNomeCatalogo } from "../utils/texto";
import {
  ExameOut,
  STATUS_EM_ANDAMENTO,
  STATUS_EXAME_LABELS,
  STATUS_LIBERACAO_OPCOES,
  StatusExame,
} from "../types/exame";

type Visao = "todas" | "andamento";

function formatarData(iso: string | null) {
  if (!iso) return "—";
  return new Date(`${iso}T00:00:00`).toLocaleDateString("pt-BR");
}

interface ListaExamesProps {
  exames: ExameOut[];
  total: number;
  carregando: boolean;
  erro: string | null;
  visao: Visao;
  selecionadoId?: string;
  onSelecionar: (exame: ExameOut) => void;
  onLiberado: () => void;
}

/** Lista compacta - cada exame é uma linha, com o fluxo "Liberar" inline. */
function ListaExames({
  exames,
  total,
  carregando,
  erro,
  visao,
  selecionadoId,
  onSelecionar,
  onLiberado,
}: ListaExamesProps) {
  // Estado do fluxo "Liberar" - não existe endpoint dedicado no backend
  // novo, é só um PUT com o status final escolhido (ver exame_router.py).
  const [liberandoId, setLiberandoId] = useState<string | null>(null);
  const [statusEscolhido, setStatusEscolhido] = useState<StatusExame>("NEGATIVO");
  const [confirmandoLiberacao, setConfirmandoLiberacao] = useState(false);

  function abrirLiberar(exame: ExameOut) {
    setLiberandoId(exame.id);
    setStatusEscolhido("NEGATIVO");
  }

  function cancelarLiberar() {
    setLiberandoId(null);
  }

  async function confirmarLiberar(exame: ExameOut) {
    setConfirmandoLiberacao(true);
    try {
      await atualizarExame(exame.id, { status: statusEscolhido });
      setLiberandoId(null);
      // A lista de exames vive no componente pai (`ExamesListPage`) - sem
      // avisar ele pra recarregar, o badge de status desta linha ficaria
      // desatualizado (e ela não sumiria da aba "Em andamento") até o
      // usuário trocar de aba/recarregar a página manualmente.
      onLiberado();
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível liberar o exame."));
    } finally {
      setConfirmandoLiberacao(false);
    }
  }

  return (
    <div className="mg-card mg-exames-lista">
      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
      {!erro && carregando && <CarregandoBarras />}

      {!erro && !carregando && exames.length === 0 && (
        <p style={{ color: "var(--mg-cinza-600)" }}>
          {visao === "todas"
            ? "Nenhum exame cadastrado."
            : "Nenhum exame em andamento no momento - tudo liberado! 🎉"}
        </p>
      )}

      {!erro && !carregando && exames.length > 0 && (
        <>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {exames.map((exame) => {
              const liberando = liberandoId === exame.id;
              return (
                <div
                  key={exame.id}
                  className={`mg-exames-item ${
                    exame.id === selecionadoId ? "mg-exames-item-selecionado" : ""
                  }`}
                  onClick={liberando ? undefined : () => onSelecionar(exame)}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: 14 }}>
                      <strong>{exame.paciente?.nome ?? "—"}</strong>{" "}
                      <span style={{ color: "var(--mg-cinza-600)", fontSize: 12 }}>
                        · #{exame.paciente?.prontuario ?? "—"}
                      </span>
                    </p>
                    <p style={{ margin: "2px 0 0 0", fontSize: 12, color: "var(--mg-cinza-600)" }}>
                      {formatarNomeCatalogo(exame.tipo_cultura?.nome ?? "—")} ·{" "}
                      {formatarNomeCatalogo(exame.material?.nome ?? "—")}
                    </p>
                  </div>

                  {liberando ? (
                    <div
                      style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <select
                        value={statusEscolhido}
                        onChange={(e) => setStatusEscolhido(e.target.value as StatusExame)}
                      >
                        {STATUS_LIBERACAO_OPCOES.map((s) => (
                          <option key={s} value={s}>
                            {STATUS_EXAME_LABELS[s]}
                          </option>
                        ))}
                      </select>
                      <button
                        className="mg-btn mg-btn-secondary"
                        disabled={confirmandoLiberacao}
                        onClick={() => confirmarLiberar(exame)}
                      >
                        {confirmandoLiberacao ? "Salvando..." : "Confirmar"}
                      </button>
                      <button className="mg-btn mg-btn-outline" onClick={cancelarLiberar}>
                        Cancelar
                      </button>
                    </div>
                  ) : (
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 6 }}>
                      <StatusExameBadge status={exame.status} />
                      <span style={{ fontSize: 11, color: "var(--mg-cinza-600)" }}>
                        {formatarData(exame.previsao_liberacao)}
                      </span>
                      {STATUS_EM_ANDAMENTO.includes(exame.status) && (
                        <button
                          className="mg-btn mg-btn-secondary"
                          style={{ padding: "2px 10px", fontSize: 12 }}
                          onClick={(e) => {
                            e.stopPropagation();
                            abrirLiberar(exame);
                          }}
                        >
                          Liberar
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          <p style={{ marginTop: 14, fontSize: 13, color: "var(--mg-cinza-600)" }}>
            {total} exame{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
          </p>
        </>
      )}
    </div>
  );
}

/** Estado vazio exibido em `/exames` (nenhuma sub-rota ativa). */
function PainelVazio() {
  return (
    <div
      className="mg-card mg-exames-detalhe"
      style={{ textAlign: "center", color: "var(--mg-cinza-600)", padding: "48px 24px" }}
    >
      <p style={{ margin: 0 }}>
        Selecione um exame na lista ao lado, ou clique em <strong>+ Novo Exame</strong>.
      </p>
    </div>
  );
}

interface PainelProps {
  onSalvo: (exame: ExameOut) => void;
  onCancelar: () => void;
}

function PainelNovo({ onSalvo, onCancelar }: PainelProps) {
  return (
    <div className="mg-exames-detalhe">
      <ExameFormPage onSalvo={onSalvo} onCancelar={onCancelar} />
    </div>
  );
}

function PainelEditar({ onSalvo, onCancelar, onRemover }: PainelProps & { onRemover: (id: string) => void }) {
  const { id } = useParams();
  if (!id) return null;
  return (
    <div className="mg-exames-detalhe">
      <ExameFormPage
        exameId={id}
        onSalvo={onSalvo}
        onCancelar={onCancelar}
        onRemover={() => onRemover(id)}
      />
    </div>
  );
}

export default function ExamesListPage() {
  const navigate = useNavigate();
  const location = useLocation();
  // `useParams()` não serve aqui: esta rota (`/exames/*` em App.tsx) não
  // declara `:id` - quem declara é a sub-rota `:id/editar` das <Routes>
  // aninhadas logo abaixo, então usamos `useMatch` pra ler o `:id` direto
  // da URL atual, independente da posição na árvore de rotas.
  const matchEditar = useMatch("/exames/:id/editar");
  const idSelecionado = matchEditar?.params.id;
  const [visao, setVisao] = useState<Visao>("todas");
  const [exames, setExames] = useState<ExameOut[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await listarExames(visao === "andamento" ? STATUS_EM_ANDAMENTO : undefined);
      setExames(resultado.items);
      setTotal(resultado.total);
    } catch {
      setErro(
        "Não foi possível carregar os exames. Verifique se a API está rodando em " +
          "http://localhost:8000."
      );
    } finally {
      setCarregando(false);
    }
  }

  // Recarrega a lista toda vez que a visão (Todas / Em andamento) muda.
  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visao]);

  // A rota-filha está ativa (novo/editar) sempre que a URL não for
  // exatamente `/exames` - controla o comportamento responsivo (< 1024px)
  // via `data-detalhe-ativo` no container (ver global.css).
  const rotaFilhaAtiva = location.pathname !== "/exames";

  function handleSalvarNovo(exame: ExameOut) {
    carregar();
    navigate(`/exames/${exame.id}/editar`);
  }

  function handleSalvarEdicao() {
    carregar();
    navigate("/exames");
  }

  function handleCancelar() {
    navigate("/exames");
  }

  async function handleRemover(id: string) {
    const exame = exames.find((e) => e.id === id);
    const confirmar = window.confirm(
      `Remover o exame de "${exame?.material?.nome ?? ""}" do paciente "${
        exame?.paciente?.nome ?? ""
      }"?`
    );
    if (!confirmar) return;
    await removerExame(id);
    carregar();
    navigate("/exames");
  }

  return (
    <MainLayout titulo="Exames" subtitulo="Pedido, resultado, isolados e antibiograma em um só lugar">
      <div className="mg-exames-layout" data-detalhe-ativo={rotaFilhaAtiva ? "true" : "false"}>
        <div className="mg-exames-lista" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="mg-page-header" style={{ margin: 0 }}>
            <div style={{ display: "flex", gap: 8 }}>
              <button
                className={`mg-btn ${visao === "todas" ? "mg-btn-primary" : "mg-btn-outline"}`}
                onClick={() => setVisao("todas")}
              >
                Todas
              </button>
              <button
                className={`mg-btn ${visao === "andamento" ? "mg-btn-primary" : "mg-btn-outline"}`}
                onClick={() => setVisao("andamento")}
              >
                Em andamento
              </button>
            </div>
            <button className="mg-btn mg-btn-primary" onClick={() => navigate("/exames/novo")}>
              + Novo Exame
            </button>
          </div>

          <ListaExames
            exames={exames}
            total={total}
            carregando={carregando}
            erro={erro}
            visao={visao}
            selecionadoId={idSelecionado}
            onSelecionar={(exame) => navigate(`/exames/${exame.id}/editar`)}
            onLiberado={carregar}
          />
        </div>

        <Routes>
          <Route index element={<PainelVazio />} />
          <Route
            path="novo"
            element={<PainelNovo onSalvo={handleSalvarNovo} onCancelar={handleCancelar} />}
          />
          <Route
            path=":id/editar"
            element={
              <PainelEditar
                onSalvo={handleSalvarEdicao}
                onCancelar={handleCancelar}
                onRemover={handleRemover}
              />
            }
          />
        </Routes>
      </div>
    </MainLayout>
  );
}
