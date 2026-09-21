import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import {
  atualizarPaciente,
  criarPaciente,
  obterPaciente,
} from "../services/pacienteService";
import { extrairMensagemErro } from "../services/api";
import { PacienteFormData } from "../types/paciente";

const FORM_INICIAL: PacienteFormData = {
  nome: "",
  prontuario: "",
  data_nascimento: "",
  sexo: "NAO_INFORMADO",
  setor: "",
  leito: "",
  observacoes: "",
};

export default function PacienteFormPage() {
  const { id } = useParams();
  const editando = Boolean(id);
  const navigate = useNavigate();

  const [form, setForm] = useState<PacienteFormData>(FORM_INICIAL);
  const [carregando, setCarregando] = useState(editando);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    obterPaciente(id)
      .then((p) =>
        setForm({
          nome: p.nome,
          prontuario: p.prontuario,
          data_nascimento: p.data_nascimento ?? "",
          sexo: p.sexo,
          setor: p.setor ?? "",
          leito: p.leito ?? "",
          observacoes: p.observacoes ?? "",
        })
      )
      .catch(() => setErro("Não foi possível carregar os dados do paciente."))
      .finally(() => setCarregando(false));
  }, [id]);

  function handleChange<K extends keyof PacienteFormData>(campo: K, valor: PacienteFormData[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    setErro(null);
    try {
      const payload = {
        ...form,
        data_nascimento: form.data_nascimento || null,
        setor: form.setor || null,
        leito: form.leito || null,
        observacoes: form.observacoes || null,
      };
      if (editando && id) {
        await atualizarPaciente(id, payload);
      } else {
        await criarPaciente(payload);
      }
      navigate("/pacientes");
    } catch (err: unknown) {
      setErro(extrairMensagemErro(err, "Não foi possível salvar o paciente."));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <MainLayout
      titulo={editando ? "Editar Paciente" : "Novo Paciente"}
      subtitulo="Cadastro de pacientes"
    >
      <div className="mg-card" style={{ maxWidth: 720 }}>
        {carregando ? (
          <CarregandoBarras />
        ) : (
          <form onSubmit={handleSubmit}>
            {erro && (
              <p
                style={{
                  color: "var(--mg-erro)",
                  fontSize: 14,
                  marginTop: 0,
                  marginBottom: 16,
                }}
              >
                {erro}
              </p>
            )}

            <div className="mg-form-grid">
              <div className="mg-field">
                <label>Nome completo *</label>
                <input
                  required
                  value={form.nome}
                  onChange={(e) => handleChange("nome", e.target.value)}
                />
              </div>

              <div className="mg-field">
                <label>Prontuário *</label>
                <input
                  required
                  value={form.prontuario}
                  onChange={(e) => handleChange("prontuario", e.target.value)}
                />
              </div>

              <div className="mg-field">
                <label>Data de nascimento</label>
                <input
                  type="date"
                  value={form.data_nascimento ?? ""}
                  onChange={(e) => handleChange("data_nascimento", e.target.value)}
                />
              </div>

              <div className="mg-field">
                <label>Sexo</label>
                <select
                  value={form.sexo}
                  onChange={(e) => handleChange("sexo", e.target.value as PacienteFormData["sexo"])}
                >
                  <option value="NAO_INFORMADO">Não informado</option>
                  <option value="MASCULINO">Masculino</option>
                  <option value="FEMININO">Feminino</option>
                </select>
              </div>

              <div className="mg-field">
                <label>Setor</label>
                <input
                  value={form.setor ?? ""}
                  onChange={(e) => handleChange("setor", e.target.value)}
                  placeholder="Ex.: UTI, UTIN, Enfermaria"
                />
              </div>

              <div className="mg-field">
                <label>Leito</label>
                <input
                  value={form.leito ?? ""}
                  onChange={(e) => handleChange("leito", e.target.value)}
                />
              </div>

              <div className="mg-field" style={{ gridColumn: "1 / -1" }}>
                <label>Observações</label>
                <textarea
                  rows={3}
                  value={form.observacoes ?? ""}
                  onChange={(e) => handleChange("observacoes", e.target.value)}
                />
              </div>
            </div>

            <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
              <button className="mg-btn mg-btn-primary" type="submit" disabled={salvando}>
                {salvando ? "Salvando..." : "Salvar"}
              </button>
              <button
                type="button"
                className="mg-btn mg-btn-outline"
                onClick={() => navigate("/pacientes")}
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>
    </MainLayout>
  );
}
