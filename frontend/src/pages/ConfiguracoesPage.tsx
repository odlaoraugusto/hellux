import { FormEvent, useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { useAuth } from "../context/AuthContext";
import {
  atualizarUsuario,
  criarUsuario,
  listarUsuarios,
  removerUsuario,
} from "../services/usuarioService";
import { atualizarParametro, listarParametros } from "../services/parametroService";
import {
  criarMicrorganismo,
  listarMicrorganismos,
  removerMicrorganismo,
} from "../services/microrganismoService";
import {
  criarAntimicrobiano,
  listarAntimicrobianos,
  removerAntimicrobiano,
} from "../services/antimicrobianoService";
import { criarSetor, listarSetores, removerSetor } from "../services/setorService";
import { criarMaterial, listarMateriais, removerMaterial } from "../services/materialService";
import {
  criarTipoCultura,
  listarTiposCultura,
  removerTipoCultura,
} from "../services/tipoCulturaService";
import { listarLogsAuditoria } from "../services/auditoriaService";
import { extrairMensagemErro } from "../services/api";
import { Usuario, PerfilUsuario } from "../types/usuario";
import { ParametroSistema } from "../types/parametro";
import { Microrganismo } from "../types/microrganismo";
import { Setor } from "../types/setor";
import { Material } from "../types/material";
import { Antimicrobiano } from "../types/antimicrobiano";
import { TipoCultura } from "../types/tipoCultura";
import { LogAuditoria } from "../types/auditoria";

type Aba = "usuarios" | "parametros" | "catalogos" | "auditoria";

const PERFIS: PerfilUsuario[] = ["ADMIN", "BIOMEDICO", "TECNICO", "VISUALIZADOR"];

function SecaoUsuarios({ souAdmin }: { souAdmin: boolean }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [mostrarForm, setMostrarForm] = useState(false);
  const [nome, setNome] = useState("");
  const [loginValue, setLoginValue] = useState("");
  const [senha, setSenha] = useState("");
  const [perfil, setPerfil] = useState<PerfilUsuario>("VISUALIZADOR");
  const [salvando, setSalvando] = useState(false);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const res = await listarUsuarios();
      setUsuarios(res.items);
    } catch {
      setErro("Não foi possível carregar os usuários (é preciso ser ADMIN).");
    } finally {
      setCarregando(false);
    }
  }

  // Carrega a lista de usuários uma vez, na montagem da aba.
  useEffect(() => {
    carregar();
  }, []);

  async function handleCriar(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await criarUsuario({ nome, login: loginValue, senha, perfil });
      setNome("");
      setLoginValue("");
      setSenha("");
      setPerfil("VISUALIZADOR");
      setMostrarForm(false);
      carregar();
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível criar o usuário."));
    } finally {
      setSalvando(false);
    }
  }

  async function handleMudarPerfil(usuario: Usuario, novoPerfil: PerfilUsuario) {
    await atualizarUsuario(usuario.id, { perfil: novoPerfil });
    carregar();
  }

  async function handleRemover(usuario: Usuario) {
    const confirmar = window.confirm(`Remover o usuário "${usuario.nome}"?`);
    if (!confirmar) return;
    await removerUsuario(usuario.id);
    carregar();
  }

  return (
    <div className="mg-card">
      <div className="mg-page-header" style={{ marginBottom: 12 }}>
        <h3 style={{ margin: 0 }}>Usuários</h3>
        {souAdmin && (
          <button className="mg-btn mg-btn-primary" onClick={() => setMostrarForm((v) => !v)}>
            {mostrarForm ? "Cancelar" : "+ Novo Usuário"}
          </button>
        )}
      </div>

      {mostrarForm && (
        <form
          onSubmit={handleCriar}
          className="mg-form-grid"
          style={{ marginBottom: 20, paddingBottom: 16, borderBottom: "1px solid var(--mg-cinza-200)" }}
        >
          <div className="mg-field">
            <label>Nome</label>
            <input required value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>
          <div className="mg-field">
            <label>Login</label>
            <input required type="text" value={loginValue} onChange={(e) => setLoginValue(e.target.value)} />
          </div>
          <div className="mg-field">
            <label>Senha</label>
            <input
              required
              type="password"
              minLength={8}
              value={senha}
              onChange={(e) => setSenha(e.target.value)}
            />
          </div>
          <div className="mg-field">
            <label>Perfil</label>
            <select value={perfil} onChange={(e) => setPerfil(e.target.value as PerfilUsuario)}>
              {PERFIS.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>
          <div style={{ gridColumn: "1 / -1" }}>
            <button className="mg-btn mg-btn-primary" type="submit" disabled={salvando}>
              {salvando ? "Salvando..." : "Cadastrar usuário"}
            </button>
          </div>
        </form>
      )}

      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
      {!erro && carregando && <CarregandoBarras />}
      {!erro && !carregando && (
        <table className="mg-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Login</th>
              <th>Perfil</th>
              <th>Status</th>
              {souAdmin && <th>Ações</th>}
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id}>
                <td>{u.nome}</td>
                <td>{u.login}</td>
                <td>
                  {souAdmin ? (
                    <select
                      value={u.perfil}
                      onChange={(e) => handleMudarPerfil(u, e.target.value as PerfilUsuario)}
                    >
                      {PERFIS.map((p) => (
                        <option key={p} value={p}>
                          {p}
                        </option>
                      ))}
                    </select>
                  ) : (
                    u.perfil
                  )}
                </td>
                <td>
                  <span className={`mg-badge ${u.is_active ? "mg-badge-sucesso" : "mg-badge-erro"}`}>
                    {u.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
                {souAdmin && (
                  <td>
                    <button
                      className="mg-btn mg-btn-outline"
                      style={{ color: "var(--mg-erro)" }}
                      onClick={() => handleRemover(u)}
                    >
                      Remover
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function SecaoParametros({ souAdmin }: { souAdmin: boolean }) {
  const [parametros, setParametros] = useState<ParametroSistema[]>([]);
  const [edicoes, setEdicoes] = useState<Record<string, string>>({});
  const [carregando, setCarregando] = useState(true);

  async function carregar() {
    setCarregando(true);
    const res = await listarParametros();
    setParametros(res);
    setCarregando(false);
  }

  // Carrega os parâmetros do sistema uma vez, na montagem da aba.
  useEffect(() => {
    carregar();
  }, []);

  async function handleSalvar(chave: string) {
    const novoValor = edicoes[chave];
    if (novoValor === undefined) return;
    await atualizarParametro(chave, novoValor);
    carregar();
  }

  return (
    <div className="mg-card">
      <h3 style={{ marginTop: 0 }}>Parâmetros do Sistema</h3>
      {carregando && <CarregandoBarras />}
      {!carregando && parametros.length === 0 && (
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
          Nenhum parâmetro semeado ainda (rode as migrações do Alembic).
        </p>
      )}
      {!carregando &&
        parametros.map((p) => (
          <div
            key={p.chave}
            style={{
              display: "flex",
              gap: 12,
              alignItems: "center",
              padding: "12px 0",
              borderBottom: "1px solid var(--mg-cinza-100)",
            }}
          >
            <div style={{ flex: 1 }}>
              <strong style={{ fontSize: 14 }}>{p.chave}</strong>
              <p style={{ margin: "2px 0 0 0", fontSize: 13, color: "var(--mg-cinza-600)" }}>
                {p.descricao}
              </p>
            </div>
            <input
              style={{ width: 120 }}
              defaultValue={p.valor}
              disabled={!souAdmin}
              onChange={(e) => setEdicoes((prev) => ({ ...prev, [p.chave]: e.target.value }))}
            />
            {souAdmin && (
              <button className="mg-btn mg-btn-outline" onClick={() => handleSalvar(p.chave)}>
                Salvar
              </button>
            )}
          </div>
        ))}
    </div>
  );
}

function SecaoCatalogos({ souAdmin }: { souAdmin: boolean }) {
  const [microrganismos, setMicrorganismos] = useState<Microrganismo[]>([]);
  const [antimicrobianos, setAntimicrobianos] = useState<Antimicrobiano[]>([]);
  const [setores, setSetores] = useState<Setor[]>([]);
  const [materiais, setMateriais] = useState<Material[]>([]);
  const [tiposCultura, setTiposCultura] = useState<TipoCultura[]>([]);
  const [novoMicro, setNovoMicro] = useState("");
  const [novoAnti, setNovoAnti] = useState("");
  const [novoSetor, setNovoSetor] = useState("");
  const [novoSetorMacroGrupo, setNovoSetorMacroGrupo] = useState("");
  const [novoMaterial, setNovoMaterial] = useState("");
  const [novoTipoCultura, setNovoTipoCultura] = useState("");

  async function carregar() {
    const [micro, anti, setoresRes, materiaisRes, tiposCulturaRes] = await Promise.all([
      listarMicrorganismos(),
      listarAntimicrobianos(),
      listarSetores(),
      listarMateriais(),
      listarTiposCultura(),
    ]);
    setMicrorganismos(micro.items);
    setAntimicrobianos(anti.items);
    setSetores(setoresRes.items);
    setMateriais(materiaisRes.items);
    setTiposCultura(tiposCulturaRes.items);
  }

  // Carrega os catálogos de microrganismos, antimicrobianos, setores,
  // materiais e tipos de cultura uma vez, na montagem da aba.
  useEffect(() => {
    carregar();
  }, []);

  async function handleAdicionarMicro() {
    if (!novoMicro.trim()) return;
    await criarMicrorganismo({ nome: novoMicro.trim(), gram: "NAO_SE_APLICA", tipo: "BACTERIA" });
    setNovoMicro("");
    carregar();
  }

  async function handleAdicionarAnti() {
    if (!novoAnti.trim()) return;
    await criarAntimicrobiano({ nome: novoAnti.trim() });
    setNovoAnti("");
    carregar();
  }

  async function handleAdicionarSetor() {
    if (!novoSetor.trim()) return;
    await criarSetor({ nome: novoSetor.trim(), macro_grupo: novoSetorMacroGrupo.trim() || null });
    setNovoSetor("");
    setNovoSetorMacroGrupo("");
    carregar();
  }

  async function handleAdicionarMaterial() {
    if (!novoMaterial.trim()) return;
    await criarMaterial({ nome: novoMaterial.trim() });
    setNovoMaterial("");
    carregar();
  }

  async function handleAdicionarTipoCultura() {
    if (!novoTipoCultura.trim()) return;
    await criarTipoCultura({ nome: novoTipoCultura.trim() });
    setNovoTipoCultura("");
    carregar();
  }

  async function handleRemoverMicro(m: Microrganismo) {
    if (!window.confirm(`Remover "${m.nome}" do catálogo?`)) return;
    await removerMicrorganismo(m.id);
    carregar();
  }

  async function handleRemoverAnti(a: Antimicrobiano) {
    if (!window.confirm(`Remover "${a.nome}" do catálogo?`)) return;
    await removerAntimicrobiano(a.id);
    carregar();
  }

  async function handleRemoverSetor(s: Setor) {
    if (!window.confirm(`Remover "${s.nome}" do catálogo?`)) return;
    await removerSetor(s.id);
    carregar();
  }

  async function handleRemoverMaterial(m: Material) {
    if (!window.confirm(`Remover "${m.nome}" do catálogo?`)) return;
    await removerMaterial(m.id);
    carregar();
  }

  async function handleRemoverTipoCultura(t: TipoCultura) {
    if (!window.confirm(`Remover "${t.nome}" do catálogo?`)) return;
    await removerTipoCultura(t.id);
    carregar();
  }

  return (
    <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
      <div className="mg-card" style={{ flex: 1, minWidth: 300 }}>
        <h3 style={{ marginTop: 0 }}>Microrganismos</h3>
        <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 12 }}>
          {microrganismos.map((m) => (
            <div
              key={m.id}
              style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 14 }}
            >
              <span>{m.nome}</span>
              {souAdmin && (
                <button
                  className="mg-btn mg-btn-outline"
                  style={{ padding: "2px 8px", fontSize: 12, color: "var(--mg-erro)" }}
                  onClick={() => handleRemoverMicro(m)}
                >
                  Remover
                </button>
              )}
            </div>
          ))}
        </div>
        {souAdmin && (
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Novo microrganismo..."
              value={novoMicro}
              onChange={(e) => setNovoMicro(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="mg-btn mg-btn-outline" onClick={handleAdicionarMicro}>
              + Adicionar
            </button>
          </div>
        )}
      </div>

      <div className="mg-card" style={{ flex: 1, minWidth: 300 }}>
        <h3 style={{ marginTop: 0 }}>Antimicrobianos</h3>
        <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 12 }}>
          {antimicrobianos.map((a) => (
            <div
              key={a.id}
              style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 14 }}
            >
              <span>{a.nome}</span>
              {souAdmin && (
                <button
                  className="mg-btn mg-btn-outline"
                  style={{ padding: "2px 8px", fontSize: 12, color: "var(--mg-erro)" }}
                  onClick={() => handleRemoverAnti(a)}
                >
                  Remover
                </button>
              )}
            </div>
          ))}
        </div>
        {souAdmin && (
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Novo antimicrobiano..."
              value={novoAnti}
              onChange={(e) => setNovoAnti(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="mg-btn mg-btn-outline" onClick={handleAdicionarAnti}>
              + Adicionar
            </button>
          </div>
        )}
      </div>

      <div className="mg-card" style={{ flex: 1, minWidth: 300 }}>
        <h3 style={{ marginTop: 0 }}>Setores</h3>
        <p style={{ marginTop: -8, fontSize: 12, color: "var(--mg-cinza-400)" }}>
          Usado para padronizar o campo "Setor" dos Exames. O macro-grupo agrupa setores
          (ex.: "UTI", "Enfermaria") pra não fragmentar a Matriz de Sensibilidade CCIH.
        </p>
        <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 12 }}>
          {setores.map((s) => (
            <div
              key={s.id}
              style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "6px 0", fontSize: 14 }}
            >
              <span>
                {s.nome}
                {s.macro_grupo && (
                  <span style={{ marginLeft: 6, fontSize: 12, color: "var(--mg-cinza-400)" }}>
                    ({s.macro_grupo})
                  </span>
                )}
              </span>
              {souAdmin && (
                <button
                  className="mg-btn mg-btn-outline"
                  style={{ padding: "2px 8px", fontSize: 12, color: "var(--mg-erro)" }}
                  onClick={() => handleRemoverSetor(s)}
                >
                  Remover
                </button>
              )}
            </div>
          ))}
        </div>
        {souAdmin && (
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Novo setor..."
              value={novoSetor}
              onChange={(e) => setNovoSetor(e.target.value)}
              style={{ flex: 1 }}
            />
            <input
              placeholder="Macro-grupo (opcional)"
              value={novoSetorMacroGrupo}
              onChange={(e) => setNovoSetorMacroGrupo(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="mg-btn mg-btn-outline" onClick={handleAdicionarSetor}>
              + Adicionar
            </button>
          </div>
        )}
      </div>

      <div className="mg-card" style={{ flex: 1, minWidth: 300 }}>
        <h3 style={{ marginTop: 0 }}>Materiais</h3>
        <p style={{ marginTop: -8, fontSize: 12, color: "var(--mg-cinza-400)" }}>
          Usado para padronizar o campo "Material" dos Exames.
        </p>
        <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 12 }}>
          {materiais.map((m) => (
            <div
              key={m.id}
              style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 14 }}
            >
              <span>{m.nome}</span>
              {souAdmin && (
                <button
                  className="mg-btn mg-btn-outline"
                  style={{ padding: "2px 8px", fontSize: 12, color: "var(--mg-erro)" }}
                  onClick={() => handleRemoverMaterial(m)}
                >
                  Remover
                </button>
              )}
            </div>
          ))}
        </div>
        {souAdmin && (
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Novo material..."
              value={novoMaterial}
              onChange={(e) => setNovoMaterial(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="mg-btn mg-btn-outline" onClick={handleAdicionarMaterial}>
              + Adicionar
            </button>
          </div>
        )}
      </div>

      <div className="mg-card" style={{ flex: 1, minWidth: 300 }}>
        <h3 style={{ marginTop: 0 }}>Tipos de Cultura</h3>
        <p style={{ marginTop: -8, fontSize: 12, color: "var(--mg-cinza-400)" }}>
          Usado para padronizar o campo "Tipo de Cultura" dos Exames.
        </p>
        <div style={{ maxHeight: 300, overflowY: "auto", marginBottom: 12 }}>
          {tiposCultura.map((t) => (
            <div
              key={t.id}
              style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", fontSize: 14 }}
            >
              <span>{t.nome}</span>
              {souAdmin && (
                <button
                  className="mg-btn mg-btn-outline"
                  style={{ padding: "2px 8px", fontSize: 12, color: "var(--mg-erro)" }}
                  onClick={() => handleRemoverTipoCultura(t)}
                >
                  Remover
                </button>
              )}
            </div>
          ))}
        </div>
        {souAdmin && (
          <div style={{ display: "flex", gap: 8 }}>
            <input
              placeholder="Novo tipo de cultura..."
              value={novoTipoCultura}
              onChange={(e) => setNovoTipoCultura(e.target.value)}
              style={{ flex: 1 }}
            />
            <button className="mg-btn mg-btn-outline" onClick={handleAdicionarTipoCultura}>
              + Adicionar
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function SecaoAuditoria({ souAdmin }: { souAdmin: boolean }) {
  const [logs, setLogs] = useState<LogAuditoria[]>([]);
  const [total, setTotal] = useState(0);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  // Carrega os logs de auditoria (se admin) uma vez, na montagem da aba;
  // depende de souAdmin, que só muda se o usuário logado mudar.
  useEffect(() => {
    if (!souAdmin) {
      setCarregando(false);
      return;
    }
    listarLogsAuditoria()
      .then((res) => {
        setLogs(res.items);
        setTotal(res.total);
      })
      .catch(() => setErro("Não foi possível carregar os logs de auditoria."))
      .finally(() => setCarregando(false));
  }, [souAdmin]);

  if (!souAdmin) {
    return (
      <div className="mg-card">
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
          Apenas usuários ADMIN podem visualizar os logs de auditoria.
        </p>
      </div>
    );
  }

  return (
    <div className="mg-card">
      <h3 style={{ marginTop: 0 }}>Logs de Auditoria</h3>
      <p style={{ color: "var(--mg-cinza-600)", fontSize: 13, marginTop: -8, marginBottom: 16 }}>
        Toda ação de escrita (criar, editar, remover) fica registrada aqui automaticamente.
      </p>

      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
      {!erro && carregando && <CarregandoBarras />}
      {!erro && !carregando && logs.length === 0 && (
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>Nenhum log registrado ainda.</p>
      )}

      {!erro && !carregando && logs.length > 0 && (
        <>
          <table className="mg-table">
            <thead>
              <tr>
                <th>Data/Hora</th>
                <th>Usuário</th>
                <th>Método</th>
                <th>Caminho</th>
                <th>Status</th>
                <th>IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.criado_em).toLocaleString("pt-BR")}</td>
                  <td>{log.usuario_login ?? "—"}</td>
                  <td>
                    <span className="mg-badge mg-badge-info">{log.metodo}</span>
                  </td>
                  <td style={{ fontFamily: "monospace", fontSize: 12 }}>{log.caminho}</td>
                  <td>
                    <span
                      className={`mg-badge ${
                        log.status_code < 300
                          ? "mg-badge-sucesso"
                          : log.status_code < 500
                            ? "mg-badge-alerta"
                            : "mg-badge-erro"
                      }`}
                    >
                      {log.status_code}
                    </span>
                  </td>
                  <td>{log.ip_origem ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p style={{ marginTop: 14, fontSize: 13, color: "var(--mg-cinza-600)" }}>
            {total} registro{total !== 1 ? "s" : ""} no total (exibindo os mais recentes)
          </p>
        </>
      )}
    </div>
  );
}

export default function ConfiguracoesPage() {
  const { usuario } = useAuth();
  const souAdmin = usuario?.perfil === "ADMIN";
  const [aba, setAba] = useState<Aba>("usuarios");

  const abas: { id: Aba; label: string }[] = [
    { id: "usuarios", label: "Usuários" },
    { id: "parametros", label: "Parâmetros" },
    { id: "catalogos", label: "Catálogos" },
    { id: "auditoria", label: "Auditoria" },
  ];

  return (
    <MainLayout titulo="Configurações" subtitulo="Usuários, parâmetros, catálogos e auditoria">
      <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
        {abas.map((a) => (
          <button
            key={a.id}
            className={`mg-btn ${aba === a.id ? "mg-btn-primary" : "mg-btn-outline"}`}
            onClick={() => setAba(a.id)}
          >
            {a.label}
          </button>
        ))}
      </div>

      {!souAdmin && (
        <p style={{ fontSize: 13, color: "var(--mg-cinza-600)", marginBottom: 16 }}>
          Você está vendo em modo somente leitura. Apenas usuários ADMIN podem alterar
          usuários, parâmetros e catálogos.
        </p>
      )}

      {aba === "usuarios" && <SecaoUsuarios souAdmin={souAdmin} />}
      {aba === "parametros" && <SecaoParametros souAdmin={souAdmin} />}
      {aba === "catalogos" && <SecaoCatalogos souAdmin={souAdmin} />}
      {aba === "auditoria" && <SecaoAuditoria souAdmin={souAdmin} />}
    </MainLayout>
  );
}
