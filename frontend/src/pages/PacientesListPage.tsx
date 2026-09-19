import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import StatusBadge from "../components/StatusBadge";
import { useDebounce } from "../hooks/useDebounce";
import { listarPacientes, removerPaciente } from "../services/pacienteService";
import { Paciente } from "../types/paciente";

export default function PacientesListPage() {
  const navigate = useNavigate();
  const [termo, setTermo] = useState("");
  const [pacientes, setPacientes] = useState<Paciente[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

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

  return (
    <MainLayout titulo="Pacientes" subtitulo="Cadastro e histórico de pacientes">
      <div className="mg-page-header">
        <div style={{ display: "flex", gap: 10 }}>
          <input
            placeholder="Buscar por nome ou prontuário..."
            value={termo}
            onChange={(e) => setTermo(e.target.value)}
            style={{
              padding: "9px 14px",
              borderRadius: "var(--mg-radius-sm)",
              border: "1px solid var(--mg-cinza-200)",
              width: 320,
              fontSize: 14,
            }}
          />
        </div>
        <button className="mg-btn mg-btn-primary" onClick={() => navigate("/pacientes/novo")}>
          + Novo Paciente
        </button>
      </div>

      <div className="mg-card">
        {erro && (
          <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>
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
                  <th>Prontuário</th>
                  <th>Nome</th>
                  <th>Setor</th>
                  <th>Leito</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {pacientes.map((p) => (
                  <tr key={p.id}>
                    <td>{p.prontuario}</td>
                    <td>{p.nome}</td>
                    <td>{p.setor ?? "—"}</td>
                    <td>{p.leito ?? "—"}</td>
                    <td>
                      <StatusBadge status={p.status_internacao} />
                    </td>
                    <td style={{ display: "flex", gap: 8 }}>
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
                ))}
              </tbody>
            </table>
            <p style={{ marginTop: 14, fontSize: 13, color: "var(--mg-cinza-600)" }}>
              {total} paciente{total !== 1 ? "s" : ""} encontrado{total !== 1 ? "s" : ""}
            </p>
          </>
        )}
      </div>
    </MainLayout>
  );
}
