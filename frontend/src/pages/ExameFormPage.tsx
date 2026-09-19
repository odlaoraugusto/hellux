import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { atualizarExame, criarExame, obterExame } from "../services/exameService";
import { listarSetores } from "../services/setorService";
import { listarTiposCultura } from "../services/tipoCulturaService";
import { listarMateriais } from "../services/materialService";
import { listarMicrorganismos } from "../services/microrganismoService";
import { listarAntimicrobianos } from "../services/antimicrobianoService";
import { listarPacientes } from "../services/pacienteService";
import { extrairMensagemErro } from "../services/api";
import { useDebounce } from "../hooks/useDebounce";
import {
  ExameAntibiogramaIn,
  ExameCreate,
  ExameIsoladoIn,
  ExameUpdate,
  MECANISMO_RESISTENCIA_LABELS,
  MECANISMO_RESISTENCIA_OPCOES,
  MecanismoResistencia,
  RESULTADO_SIR_LABELS,
  RESULTADO_SIR_OPCOES,
  ResultadoSIR,
  STATUS_EXAME_LABELS,
  STATUS_EXAME_OPCOES,
  STATUS_PERMITE_ISOLADOS,
  StatusExame,
} from "../types/exame";
import { Setor } from "../types/setor";
import { TipoCultura } from "../types/tipoCultura";
import { Material } from "../types/material";
import { Microrganismo } from "../types/microrganismo";
import { Antimicrobiano } from "../types/antimicrobiano";

interface FormState {
  paciente_prontuario: string;
  paciente_nome: string;
  setor_id: string;
  tipo_cultura_id: string;
  material_id: string;
  data_coleta: string;
  previsao_liberacao: string;
  status: StatusExame;
  identificacao_preliminar: string;
  observacoes: string;
}

const FORM_INICIAL: FormState = {
  paciente_prontuario: "",
  paciente_nome: "",
  setor_id: "",
  tipo_cultura_id: "",
  material_id: "",
  data_coleta: "",
  previsao_liberacao: "",
  status: "AGUARDANDO_TRIAGEM",
  identificacao_preliminar: "",
  observacoes: "",
};

// Estrutura de edição local de um isolado - espelha `ExameIsoladoIn`, mas
// com `motivo_dispensa_tsa` sempre string (nunca null) pra facilitar o
// binding com o <input>, e é convertida pro formato do backend só na hora
// de montar o payload (ver `montarIsoladosPayload`).
interface IsoladoEditavel {
  microrganismo_id: string;
  mecanismo_resistencia: MecanismoResistencia;
  nao_realizado_tecnico: boolean;
  motivo_dispensa_tsa: string;
  antibiograma: ExameAntibiogramaIn[];
}

function criarIsoladoVazio(): IsoladoEditavel {
  return {
    microrganismo_id: "",
    mecanismo_resistencia: "NENHUM",
    nao_realizado_tecnico: false,
    motivo_dispensa_tsa: "",
    antibiograma: [],
  };
}

export default function ExameFormPage() {
  const { id } = useParams();
  const editando = Boolean(id);
  const navigate = useNavigate();

  const [form, setForm] = useState<FormState>(FORM_INICIAL);
  const [isolados, setIsolados] = useState<IsoladoEditavel[]>([]);

  const [setores, setSetores] = useState<Setor[]>([]);
  const [tiposCultura, setTiposCultura] = useState<TipoCultura[]>([]);
  const [materiais, setMateriais] = useState<Material[]>([]);
  const [microrganismos, setMicrorganismos] = useState<Microrganismo[]>([]);
  const [antimicrobianos, setAntimicrobianos] = useState<Antimicrobiano[]>([]);

  const [carregando, setCarregando] = useState(editando);
  const [salvando, setSalvando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const [buscandoPaciente, setBuscandoPaciente] = useState(false);
  const [pacienteEncontrado, setPacienteEncontrado] = useState<boolean | null>(null);
  const prontuarioDebounced = useDebounce(form.paciente_prontuario, 350);

  // Carrega os catálogos (setor, tipo de cultura, material, microrganismo,
  // antimicrobiano) uma vez, na montagem do form.
  useEffect(() => {
    listarSetores().then((res) => setSetores(res.items));
    listarTiposCultura().then((res) => setTiposCultura(res.items));
    listarMateriais().then((res) => setMateriais(res.items));
    listarMicrorganismos().then((res) => setMicrorganismos(res.items));
    listarAntimicrobianos().then((res) => setAntimicrobianos(res.items));
  }, []);

  useEffect(() => {
    if (!id) return;
    obterExame(id)
      .then((exame) => {
        setForm({
          paciente_prontuario: exame.paciente?.prontuario ?? "",
          paciente_nome: exame.paciente?.nome ?? "",
          setor_id: exame.setor_id ?? "",
          tipo_cultura_id: exame.tipo_cultura_id,
          material_id: exame.material_id,
          data_coleta: exame.data_coleta ? exame.data_coleta.slice(0, 10) : "",
          previsao_liberacao: exame.previsao_liberacao ?? "",
          status: exame.status,
          identificacao_preliminar: exame.identificacao_preliminar ?? "",
          observacoes: exame.observacoes ?? "",
        });
        setIsolados(
          exame.isolados.map((isolado) => ({
            microrganismo_id: isolado.microrganismo.id,
            mecanismo_resistencia: isolado.mecanismo_resistencia,
            nao_realizado_tecnico: isolado.nao_realizado_tecnico,
            motivo_dispensa_tsa: isolado.motivo_dispensa_tsa ?? "",
            antibiograma: isolado.antibiograma.map((a) => ({
              antimicrobiano_id: a.antimicrobiano.id,
              resultado: a.resultado,
            })),
          }))
        );
      })
      .catch(() => setErro("Não foi possível carregar os dados do exame."))
      .finally(() => setCarregando(false));
  }, [id]);

  // Ao digitar o prontuário (só na criação), busca com debounce se já
  // existe um paciente com esse prontuário exato - se achar, preenche o
  // nome automaticamente; se não achar, avisa que será cadastrado um novo.
  useEffect(() => {
    if (editando) return;
    if (!prontuarioDebounced) {
      setPacienteEncontrado(null);
      return;
    }
    let cancelado = false;
    setBuscandoPaciente(true);
    listarPacientes(prontuarioDebounced, 1, 5)
      .then((res) => {
        if (cancelado) return;
        const encontrado = res.items.find((p) => p.prontuario === prontuarioDebounced);
        if (encontrado) {
          setPacienteEncontrado(true);
          setForm((prev) => ({ ...prev, paciente_nome: encontrado.nome }));
        } else {
          setPacienteEncontrado(false);
        }
      })
      .finally(() => {
        if (!cancelado) setBuscandoPaciente(false);
      });
    return () => {
      cancelado = true;
    };
  }, [prontuarioDebounced, editando]);

  function handleChange<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }));
  }

  // Isolados só fazem sentido quando o status indica cultura positiva
  // (espelha `STATUS_POSITIVO`/`_validar_isolados` no backend) - ao sair
  // desses status, os isolados lançados até então são descartados.
  function handleStatusChange(status: StatusExame) {
    setForm((prev) => ({ ...prev, status }));
    if (!STATUS_PERMITE_ISOLADOS.includes(status)) {
      setIsolados([]);
    }
  }

  function handleAdicionarIsolado() {
    setIsolados((prev) => [...prev, criarIsoladoVazio()]);
  }

  function handleRemoverIsolado(index: number) {
    setIsolados((prev) => prev.filter((_, i) => i !== index));
  }

  function handleAlterarIsolado(index: number, patch: Partial<IsoladoEditavel>) {
    setIsolados((prev) => prev.map((item, i) => (i === index ? { ...item, ...patch } : item)));
  }

  // Marcar "não realizado tecnicamente" dispensa a exigência de
  // antibiograma deste isolado (espelha `nao_realizado_tecnico` no
  // backend) - por isso a sub-seção de antibiograma é limpa ao marcar.
  function handleToggleNaoRealizado(index: number, valor: boolean) {
    setIsolados((prev) =>
      prev.map((item, i) =>
        i === index
          ? { ...item, nao_realizado_tecnico: valor, antibiograma: valor ? [] : item.antibiograma }
          : item
      )
    );
  }

  function handleAdicionarAntibiograma(index: number) {
    setIsolados((prev) =>
      prev.map((item, i) => {
        if (i !== index) return item;
        const usados = new Set(item.antibiograma.map((a) => a.antimicrobiano_id));
        const disponivel = antimicrobianos.find((a) => !usados.has(a.id));
        if (!disponivel) return item;
        const novaLinha: ExameAntibiogramaIn = {
          antimicrobiano_id: disponivel.id,
          resultado: "SENSIVEL",
        };
        return { ...item, antibiograma: [...item.antibiograma, novaLinha] };
      })
    );
  }

  function handleAlterarAntibiograma(
    isoladoIndex: number,
    linhaIndex: number,
    patch: Partial<ExameAntibiogramaIn>
  ) {
    setIsolados((prev) =>
      prev.map((item, i) =>
        i === isoladoIndex
          ? {
              ...item,
              antibiograma: item.antibiograma.map((a, j) => (j === linhaIndex ? { ...a, ...patch } : a)),
            }
          : item
      )
    );
  }

  function handleRemoverAntibiograma(isoladoIndex: number, linhaIndex: number) {
    setIsolados((prev) =>
      prev.map((item, i) =>
        i === isoladoIndex
          ? { ...item, antibiograma: item.antibiograma.filter((_, j) => j !== linhaIndex) }
          : item
      )
    );
  }

  // Valida a mesma regra do backend (`ExameIsoladoIn._validar_motivo_dispensa`)
  // no cliente, pra dar feedback imediato em vez de esperar o 422 da API.
  function validarIsolados(): string | null {
    for (const isolado of isolados) {
      if (!isolado.microrganismo_id) {
        return "Selecione o microrganismo de todos os isolados adicionados.";
      }
      if (isolado.nao_realizado_tecnico && !isolado.motivo_dispensa_tsa.trim()) {
        return 'Informe o motivo da dispensa de TSA nos isolados marcados como "não realizado tecnicamente".';
      }
    }
    return null;
  }

  function montarIsoladosPayload(): ExameIsoladoIn[] {
    return isolados.map((isolado) => ({
      microrganismo_id: isolado.microrganismo_id,
      mecanismo_resistencia: isolado.mecanismo_resistencia,
      nao_realizado_tecnico: isolado.nao_realizado_tecnico,
      motivo_dispensa_tsa: isolado.nao_realizado_tecnico ? isolado.motivo_dispensa_tsa : null,
      antibiograma: isolado.nao_realizado_tecnico ? [] : isolado.antibiograma,
    }));
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);

    const mostrarSecaoIsolados = STATUS_PERMITE_ISOLADOS.includes(form.status);
    if (mostrarSecaoIsolados) {
      const erroIsolados = validarIsolados();
      if (erroIsolados) {
        setErro(erroIsolados);
        return;
      }
    }

    const isoladosPayload = mostrarSecaoIsolados ? montarIsoladosPayload() : [];

    setSalvando(true);
    try {
      if (editando && id) {
        const payload: ExameUpdate = {
          setor_id: form.setor_id || null,
          tipo_cultura_id: form.tipo_cultura_id || null,
          material_id: form.material_id || null,
          data_coleta: form.data_coleta || null,
          previsao_liberacao: form.previsao_liberacao || null,
          status: form.status,
          identificacao_preliminar: form.identificacao_preliminar || null,
          observacoes: form.observacoes || null,
          isolados: isoladosPayload,
        };
        await atualizarExame(id, payload);
        navigate("/exames");
      } else {
        const payload: ExameCreate = {
          paciente_prontuario: form.paciente_prontuario,
          paciente_nome: form.paciente_nome,
          setor_id: form.setor_id || null,
          tipo_cultura_id: form.tipo_cultura_id,
          material_id: form.material_id,
          data_coleta: form.data_coleta || null,
          previsao_liberacao: form.previsao_liberacao || null,
          status: form.status,
          identificacao_preliminar: form.identificacao_preliminar || null,
          observacoes: form.observacoes || null,
          isolados: isoladosPayload,
        };
        const criado = await criarExame(payload);
        navigate(`/exames/${criado.id}/editar`);
      }
    } catch (err: unknown) {
      setErro(extrairMensagemErro(err, "Não foi possível salvar o exame."));
    } finally {
      setSalvando(false);
    }
  }

  const mostrarSecaoIsolados = STATUS_PERMITE_ISOLADOS.includes(form.status);

  // Mensagem de apoio abaixo do campo Prontuário (só na criação).
  let mensagemProntuario: string | null = null;
  let corMensagemProntuario = "var(--mg-cinza-400)";
  if (!editando) {
    if (buscandoPaciente) {
      mensagemProntuario = "Buscando...";
    } else if (pacienteEncontrado === true) {
      mensagemProntuario = "Paciente já cadastrado";
      corMensagemProntuario = "var(--mg-secundaria)";
    } else if (pacienteEncontrado === false && form.paciente_prontuario.length > 0) {
      mensagemProntuario = "Paciente novo será cadastrado automaticamente";
    }
  }

  return (
    <MainLayout
      titulo={editando ? "Editar Exame" : "Novo Exame"}
      subtitulo="Pedido, resultado, isolados e antibiograma em uma única tela"
    >
      <div className="mg-card" style={{ maxWidth: 900 }}>
        {carregando ? (
          <CarregandoBarras />
        ) : (
          <form onSubmit={handleSubmit}>
            {erro && (
              <p style={{ color: "var(--mg-erro)", fontSize: 14, marginTop: 0, marginBottom: 16 }}>
                {erro}
              </p>
            )}

            <h3 style={{ margin: "0 0 12px 0" }}>Exame</h3>
            <div className="mg-form-grid">
              <div className="mg-field">
                <label>Prontuário *</label>
                {editando ? (
                  <input value={form.paciente_prontuario} disabled />
                ) : (
                  <input
                    required
                    value={form.paciente_prontuario}
                    placeholder="Número do prontuário"
                    onChange={(e) => handleChange("paciente_prontuario", e.target.value)}
                  />
                )}
                {mensagemProntuario && (
                  <span style={{ fontSize: 12, color: corMensagemProntuario }}>
                    {mensagemProntuario}
                  </span>
                )}
              </div>

              <div className="mg-field">
                <label>Paciente *</label>
                {editando ? (
                  <input value={form.paciente_nome} disabled />
                ) : (
                  <input
                    required
                    value={form.paciente_nome}
                    placeholder="Nome do paciente"
                    onChange={(e) => handleChange("paciente_nome", e.target.value)}
                  />
                )}
              </div>

              <div className="mg-field">
                <label>Setor</label>
                <select value={form.setor_id} onChange={(e) => handleChange("setor_id", e.target.value)}>
                  <option value="">Não informado</option>
                  {setores.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mg-field">
                <label>Tipo de cultura *</label>
                <select
                  required
                  value={form.tipo_cultura_id}
                  onChange={(e) => handleChange("tipo_cultura_id", e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {tiposCultura.map((t) => (
                    <option key={t.id} value={t.id}>
                      {t.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mg-field">
                <label>Material *</label>
                <select
                  required
                  value={form.material_id}
                  onChange={(e) => handleChange("material_id", e.target.value)}
                >
                  <option value="">Selecione...</option>
                  {materiais.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.nome}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mg-field">
                <label>Data da coleta</label>
                <input
                  type="date"
                  value={form.data_coleta}
                  onChange={(e) => handleChange("data_coleta", e.target.value)}
                />
                <span style={{ fontSize: 12, color: "var(--mg-cinza-400)" }}>
                  Se deixar em branco, usa a data de hoje.
                </span>
              </div>

              <div className="mg-field">
                <label>Previsão de liberação</label>
                <input
                  type="date"
                  value={form.previsao_liberacao}
                  onChange={(e) => handleChange("previsao_liberacao", e.target.value)}
                />
                <span style={{ fontSize: 12, color: "var(--mg-cinza-400)" }}>
                  Se deixar em branco, é calculada automaticamente.
                </span>
              </div>

              <div className="mg-field">
                <label>Status</label>
                <select
                  value={form.status}
                  onChange={(e) => handleStatusChange(e.target.value as StatusExame)}
                >
                  {STATUS_EXAME_OPCOES.map((s) => (
                    <option key={s} value={s}>
                      {STATUS_EXAME_LABELS[s]}
                    </option>
                  ))}
                </select>
              </div>

              <div className="mg-field" style={{ gridColumn: "1 / -1" }}>
                <label>Identificação preliminar</label>
                <input
                  maxLength={300}
                  value={form.identificacao_preliminar}
                  placeholder="Ex.: Cocos Gram-positivos em cachos"
                  onChange={(e) => handleChange("identificacao_preliminar", e.target.value)}
                />
              </div>

              <div className="mg-field" style={{ gridColumn: "1 / -1" }}>
                <label>Observações</label>
                <textarea
                  rows={3}
                  maxLength={1000}
                  value={form.observacoes}
                  onChange={(e) => handleChange("observacoes", e.target.value)}
                />
              </div>
            </div>

            {mostrarSecaoIsolados && (
              <>
                <hr style={{ margin: "24px 0", border: "none", borderTop: "1px solid var(--mg-cinza-200)" }} />

                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 12,
                  }}
                >
                  <h3 style={{ margin: 0 }}>Isolados</h3>
                  <button type="button" className="mg-btn mg-btn-secondary" onClick={handleAdicionarIsolado}>
                    + Adicionar isolado
                  </button>
                </div>

                {isolados.length === 0 && (
                  <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
                    Nenhum isolado adicionado ainda.
                  </p>
                )}

                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                  {isolados.map((isolado, index) => (
                    <div
                      key={index}
                      style={{
                        border: "1px solid var(--mg-cinza-200)",
                        borderRadius: "var(--mg-radius-sm)",
                        padding: "12px 14px",
                      }}
                    >
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 10,
                        }}
                      >
                        <strong style={{ fontSize: 14 }}>Isolado {index + 1}</strong>
                        <button
                          type="button"
                          className="mg-btn mg-btn-outline"
                          style={{ color: "var(--mg-erro)" }}
                          onClick={() => handleRemoverIsolado(index)}
                        >
                          Remover isolado
                        </button>
                      </div>

                      <div className="mg-form-grid">
                        <div className="mg-field">
                          <label>Microrganismo *</label>
                          <select
                            required
                            value={isolado.microrganismo_id}
                            onChange={(e) =>
                              handleAlterarIsolado(index, { microrganismo_id: e.target.value })
                            }
                          >
                            <option value="">Selecione...</option>
                            {microrganismos.map((m) => (
                              <option key={m.id} value={m.id}>
                                {m.nome}
                              </option>
                            ))}
                          </select>
                        </div>

                        <div className="mg-field">
                          <label>Mecanismo de resistência</label>
                          <select
                            value={isolado.mecanismo_resistencia}
                            onChange={(e) =>
                              handleAlterarIsolado(index, {
                                mecanismo_resistencia: e.target.value as MecanismoResistencia,
                              })
                            }
                          >
                            {MECANISMO_RESISTENCIA_OPCOES.map((m) => (
                              <option key={m} value={m}>
                                {MECANISMO_RESISTENCIA_LABELS[m]}
                              </option>
                            ))}
                          </select>
                        </div>
                      </div>

                      <label
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: 6,
                          fontSize: 13,
                          margin: "10px 0",
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={isolado.nao_realizado_tecnico}
                          onChange={(e) => handleToggleNaoRealizado(index, e.target.checked)}
                        />
                        Não realizado tecnicamente (dispensa o antibiograma deste isolado)
                      </label>

                      {isolado.nao_realizado_tecnico ? (
                        <div className="mg-field">
                          <label>Motivo da dispensa *</label>
                          <input
                            required
                            maxLength={500}
                            value={isolado.motivo_dispensa_tsa}
                            placeholder="Ex.: microrganismo sem protocolo BrCAST"
                            onChange={(e) =>
                              handleAlterarIsolado(index, { motivo_dispensa_tsa: e.target.value })
                            }
                          />
                        </div>
                      ) : (
                        <div>
                          <label style={{ fontSize: 13, fontWeight: 600 }}>Antibiograma</label>
                          {isolado.antibiograma.length === 0 && (
                            <p style={{ fontSize: 13, color: "var(--mg-cinza-600)", margin: "4px 0 8px 0" }}>
                              Nenhum antimicrobiano adicionado ainda.
                            </p>
                          )}
                          {isolado.antibiograma.map((linha, linhaIndex) => (
                            <div
                              key={linhaIndex}
                              style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}
                            >
                              <select
                                style={{ flex: 2 }}
                                value={linha.antimicrobiano_id}
                                onChange={(e) =>
                                  handleAlterarAntibiograma(index, linhaIndex, {
                                    antimicrobiano_id: e.target.value,
                                  })
                                }
                              >
                                {antimicrobianos.map((a) => (
                                  <option key={a.id} value={a.id}>
                                    {a.nome}
                                  </option>
                                ))}
                              </select>
                              <select
                                style={{ flex: 1 }}
                                value={linha.resultado}
                                onChange={(e) =>
                                  handleAlterarAntibiograma(index, linhaIndex, {
                                    resultado: e.target.value as ResultadoSIR,
                                  })
                                }
                              >
                                {RESULTADO_SIR_OPCOES.map((r) => (
                                  <option key={r} value={r}>
                                    {RESULTADO_SIR_LABELS[r]}
                                  </option>
                                ))}
                              </select>
                              <button
                                type="button"
                                className="mg-btn mg-btn-outline"
                                style={{ color: "var(--mg-erro)" }}
                                onClick={() => handleRemoverAntibiograma(index, linhaIndex)}
                              >
                                Remover
                              </button>
                            </div>
                          ))}
                          <button
                            type="button"
                            className="mg-btn mg-btn-outline"
                            style={{ marginTop: 8 }}
                            disabled={antimicrobianos.length === 0}
                            onClick={() => handleAdicionarAntibiograma(index)}
                          >
                            + Adicionar antimicrobiano
                          </button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </>
            )}

            <div style={{ display: "flex", gap: 10, marginTop: 22 }}>
              <button className="mg-btn mg-btn-primary" type="submit" disabled={salvando}>
                {salvando ? "Salvando..." : "Salvar"}
              </button>
              <button
                type="button"
                className="mg-btn mg-btn-outline"
                onClick={() => navigate("/exames")}
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
