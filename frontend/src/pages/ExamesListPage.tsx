import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import StatusExameBadge from "../components/StatusExameBadge";
import { atualizarExame, listarExames, removerExame } from "../services/exameService";
import { extrairMensagemErro } from "../services/api";
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

export default function ExamesListPage() {
  const navigate = useNavigate();
  const [visao, setVisao] = useState<Visao>("todas");
  const [exames, setExames] = useState<ExameOut[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  // Estado do fluxo "Liberar" - não existe endpoint dedicado no backend
  // novo, é só um PUT com o status final escolhido (ver exame_router.py).
  const [liberandoId, setLiberandoId] = useState<string | null>(null);
  const [statusEscolhido, setStatusEscolhido] = useState<StatusExame>("NEGATIVO");
  const [confirmandoLiberacao, setConfirmandoLiberacao] = useState(false);

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
      carregar();
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível liberar o exame."));
    } finally {
      setConfirmandoLiberacao(false);
    }
  }

  async function handleRemover(exame: ExameOut) {
    const confirmar = window.confirm(
      `Remover o exame de "${exame.material?.nome ?? ""}" do paciente "${
        exame.paciente?.nome ?? ""
      }"?`
    );
    if (!confirmar) return;
    await removerExame(exame.id);
    carregar();
  }

  return (
    <MainLayout titulo="Exames" subtitulo="Pedido, resultado, isolados e antibiograma em um só lugar">
      <div className="mg-page-header">
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

      <div className="mg-card">
        {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
        {!erro && carregando && <p style={{ color: "var(--mg-cinza-600)" }}>Carregando...</p>}

        {!erro && !carregando && exames.length === 0 && (
          <p style={{ color: "var(--mg-cinza-600)" }}>
            {visao === "todas"
              ? "Nenhum exame cadastrado."
              : "Nenhum exame em andamento no momento - tudo liberado! 🎉"}
          </p>
        )}

        {!erro && !carregando && exames.length > 0 && (
          <>
            <table className="mg-table">
              <thead>
                <tr>
                  <th>Prontuário</th>
                  <th>Paciente</th>
                  <th>Setor</th>
                  <th>Tipo de Cultura</th>
                  <th>Material</th>
                  <th>Status</th>
                  <th>Previsão de Liberação</th>
                  <th>Isolados</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {exames.map((exame) => (
                  <tr key={exame.id}>
                    <td>{exame.paciente?.prontuario ?? "—"}</td>
                    <td>{exame.paciente?.nome ?? "—"}</td>
                    <td>{exame.setor?.nome ?? "—"}</td>
                    <td>{exame.tipo_cultura?.nome ?? "—"}</td>
                    <td>{exame.material?.nome ?? "—"}</td>
                    <td>
                      <StatusExameBadge status={exame.status} />
                    </td>
                    <td>{formatarData(exame.previsao_liberacao)}</td>
                    <td>
                      {exame.isolados.length > 0
                        ? exame.isolados.map((i) => i.microrganismo.nome).join(", ")
                        : "—"}
                    </td>
                    <td style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
                      {liberandoId === exame.id ? (
                        <>
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
                        </>
                      ) : (
                        <>
                          <button
                            className="mg-btn mg-btn-outline"
                            onClick={() => navigate(`/exames/${exame.id}/editar`)}
                          >
                            Continuar/Editar
                          </button>
                          {STATUS_EM_ANDAMENTO.includes(exame.status) && (
                            <button
                              className="mg-btn mg-btn-secondary"
                              onClick={() => abrirLiberar(exame)}
                            >
                              Liberar
                            </button>
                          )}
                          <button
                            className="mg-btn mg-btn-outline"
                            style={{ color: "var(--mg-erro)" }}
                            onClick={() => handleRemover(exame)}
                          >
                            Remover
                          </button>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p style={{ marginTop: 14, fontSize: 13, color: "var(--mg-cinza-600)" }}>
              {total} exame{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
            </p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
