import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import StatusBadge from "../components/StatusBadge";
import StatusExameBadge from "../components/StatusExameBadge";
import { useDebounce } from "../hooks/useDebounce";
import { listarPacientes, removerPaciente } from "../services/pacienteService";
import { listarExames } from "../services/exameService";
import { formatarNomeCatalogo } from "../utils/texto";
import { Paciente } from "../types/paciente";
import { ExameOut } from "../types/exame";

export default function PacientesListPage() {
  const navigate = useNavigate();
  const [termo, setTermo] = useState("");
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [expandidoId, setExpandidoId] = useState<string | null>(null);
  const [historicoPorPaciente, setHistoricoPorPaciente] = useState<
    Record<string, ExameOut[]>
  >({});
  const [historicoCarregandoId, setHistoricoCarregandoId] = useState<string | null>(null);
  const [historicoErroId, setHistoricoErroId] = useState<string | null>(null);

  const termoDebounced = useDebounce(termo);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await listarPacientes(termoDebounced || undefined);
      setPacientes(resultado.items);
      setTotal(resultado.total);
    } catch {
      setErro(
        "Não foi possível carregar os pacientes. Verifique se a API está rodando em " +
          "http://localhost:8000."
      );
    } finally {
      setCarregando(false);
    }
  }

  // Refaz a busca toda vez que o termo (com debounce) muda.
  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [termoDebounced]);

  async function handleRemover(paciente: Paciente) {
    const confirmar = window.confirm(
      `Remover o paciente "${paciente.nome}" (prontuário ${paciente.prontuario})?`
    );
    if (!confirmar) return;
    await removerPaciente(paciente.id);
    carregar();
  }

  async function alternarExpandir(paciente: Paciente) {
    if (expandidoId === paciente.id) {
      setExpandidoId(null);
      return;
    }

    setExpandidoId(paciente.id);

    // Já carregado antes - reaproveita do cache em memória em vez de
    // refazer a chamada toda vez que o usuário reabre o mesmo paciente.
    if (historicoPorPaciente[paciente.id]) return;

    setHistoricoCarregandoId(paciente.id);
    setHistoricoErroId(null);
    try {
      const resultado = await listarExames(undefined, paciente.id, 1, 100);
      setHistoricoPorPaciente((atual) => ({ ...atual, [paciente.id]: resultado.items }));
    } catch {
      setHistoricoErroId(paciente.id);
    } finally {
      setHistoricoCarregandoId(null);
    }
  }

  return (
    <MainLayout titulo="Pacientes" subtitulo="Cadastro e histórico de pacientes">
      <div className="mg-page-header">
        <div style={{ display: "flex", gap: 10 }}>
          <input
            placeholder="Buscar por nome ou prontuário..."
            value={termo}
            onChange={(e) => setTermo(e.target.value)}
            style={{
              padding: "8px 10px",
              borderRadius: "var(--mg-radius-sm)",
              border: "1px solid var(--mg-cinza-200)",
              width: 320,
              fontSize: 13,
            }}
          />
        </div>
        <button className="mg-btn mg-btn-primary" onClick={() => navigate("/pacientes/novo")}>
          + Novo Paciente
        </button>
      </div>

      <div className="mg-card">
        {erro && (
          <p style={{ color: "var(--mg-erro)", fontSize: 13 }}>{erro}</p>
        )}

        {!erro && carregando && <CarregandoBarras />}

        {!erro && !carregando && pacientes.length === 0 && (
          <p style={{ color: "var(--mg-cinza-600)" }}>
            Nenhum paciente encontrado{termo ? ` para "${termo}"` : ""}.
          </p>
        )}

        {!erro && !carregando && pacientes.length > 0 && (
          <>
            <table className="mg-table">
              <thead>
                <tr>
                  <th style={{ width: 28 }}></th>
                  <th>Prontuário</th>
                  <th>Nome</th>
                  <th>Setor</th>
                  <th>Leito</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {pacientes.map((p) => {
                  const expandido = expandidoId === p.id;
                  const historico = historicoPorPaciente[p.id];
                  return (
                    <>
                      <tr
                        key={p.id}
                        className="mg-exames-item"
                        style={{ cursor: "pointer" }}
                        onClick={() => alternarExpandir(p)}
                      >
                        <td>
                          {expandido ? (
                            <ChevronDown size={16} color="var(--mg-cinza-400)" />
                          ) : (
                            <ChevronRight size={16} color="var(--mg-cinza-400)" />
                          )}
                        </td>
                        <td>{p.prontuario}</td>
                        <td>{p.nome}</td>
                        <td>{p.setor ?? "—"}</td>
                        <td>{p.leito ?? "—"}</td>
                        <td>
                          <StatusBadge status={p.status_internacao} />
                        </td>
                        <td style={{ display: "flex", gap: 8 }} onClick={(e) => e.stopPropagation()}>
                          <button
                            className="mg-btn mg-btn-outline"
                            onClick={() => navigate(`/pacientes/${p.id}/editar`)}
                          >
                            Editar
                          </button>
                          <button
                            className="mg-btn mg-btn-outline"
                            style={{ color: "var(--mg-erro)" }}
                            onClick={() => handleRemover(p)}
                          >
                            Remover
                          </button>
                        </td>
                      </tr>
                      {expandido && (
                        <tr key={`${p.id}-historico`}>
                          <td colSpan={7} style={{ background: "var(--mg-cinza-100)", padding: 0 }}>
                            <div style={{ padding: "10px 12px 12px 40px" }}>
                              {historicoCarregandoId === p.id && <CarregandoBarras tamanho="pequeno" />}
                              {historicoErroId === p.id && (
                                <p style={{ color: "var(--mg-erro)", fontSize: 12, margin: 0 }}>
                                  Não foi possível carregar o histórico deste paciente.
                                </p>
                              )}
                              {historico && historico.length === 0 && (
                                <p style={{ color: "var(--mg-cinza-600)", fontSize: 12, margin: 0 }}>
                                  Nenhum exame registrado pra este paciente ainda.
                                </p>
                              )}
                              {historico && historico.length > 0 && (
                                <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                  {historico.map((exame) => (
                                    <div
                                      key={exame.id}
                                      style={{
                                        display: "flex",
                                        alignItems: "center",
                                        justifyContent: "space-between",
                                        gap: 12,
                                        padding: "6px 8px",
                                        borderRadius: "var(--mg-radius-sm)",
                                        cursor: "pointer",
                                        fontSize: 12.5,
                                      }}
                                      onClick={() => navigate(`/exames/${exame.id}/editar`)}
                                    >
                                      <span style={{ color: "var(--mg-cinza-600)", minWidth: 90 }}>
                                        {exame.data_coleta
                                          ? new Date(exame.data_coleta).toLocaleDateString("pt-BR")
                                          : "—"}
                                      </span>
                                      <span style={{ flex: 1 }}>
                                        {formatarNomeCatalogo(exame.tipo_cultura?.nome ?? "—")}
                                        {exame.material ? ` · ${formatarNomeCatalogo(exame.material.nome)}` : ""}
                                      </span>
                                      <StatusExameBadge status={exame.status} />
                                    </div>
                                  ))}
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
            <p style={{ marginTop: 12, fontSize: 12, color: "var(--mg-cinza-600)" }}>
              {total} paciente{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
            </p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
