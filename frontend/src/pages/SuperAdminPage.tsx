import { FormEvent, useEffect, useState } from "react";
import HelluxIcon from "../components/HelluxIcon";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { useAuth } from "../context/AuthContext";
import { extrairMensagemErro } from "../services/api";
import { atualizarTenant, criarTenant, listarTenants } from "../services/tenantService";
import { criarUsuario, listarUsuariosPorTenant } from "../services/usuarioService";
import { Tenant, TenantCreate } from "../types/tenant";
import { PerfilUsuario, Usuario } from "../types/usuario";

const PERFIS_TENANT: PerfilUsuario[] = ["ADMIN", "BIOMEDICO", "TECNICO", "VISUALIZADOR"];

const TENANT_CREATE_VAZIO: TenantCreate = {
  nome_fantasia: "",
  razao_social: "",
  cnpj: "",
  logo_url: "",
  subtitulo_cabecalho: "",
  admin_nome: "",
  admin_login: "",
  admin_senha: "",
};

/**
 * Painel exclusivo de SUPER_ADMIN: gerencia a lista de tenants
 * (hospitais-cliente) e os usuários de cada um. Layout próprio,
 * intencionalmente fora de MainLayout/Sidebar/Topbar - um SUPER_ADMIN
 * nunca deve navegar em dado clínico do hospital.
 */
export default function SuperAdminPage() {
  const { usuario, logout } = useAuth();

  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [mostrarFormTenant, setMostrarFormTenant] = useState(false);
  const [formTenant, setFormTenant] = useState<TenantCreate>(TENANT_CREATE_VAZIO);
  const [salvandoTenant, setSalvandoTenant] = useState(false);
  const [mensagemSucesso, setMensagemSucesso] = useState<string | null>(null);

  const [tenantSelecionadoId, setTenantSelecionadoId] = useState<string | null>(null);

  async function carregarTenants() {
    setCarregando(true);
    setErro(null);
    try {
      const res = await listarTenants();
      setTenants(res.items);
    } catch (err: unknown) {
      setErro(extrairMensagemErro(err, "Não foi possível carregar os tenants."));
    } finally {
      setCarregando(false);
    }
  }

  // Carrega a lista de tenants uma vez, na montagem do painel.
  useEffect(() => {
    carregarTenants();
  }, []);

  async function handleCriarTenant(e: FormEvent) {
    e.preventDefault();
    setSalvandoTenant(true);
    setMensagemSucesso(null);
    try {
      // Campos opcionais vazios viram `undefined` (em vez de string vazia)
      // pra o backend gravar NULL de verdade, não uma string vazia.
      const payload: TenantCreate = {
        nome_fantasia: formTenant.nome_fantasia.trim(),
        razao_social: formTenant.razao_social?.trim() || undefined,
        cnpj: formTenant.cnpj?.trim() || undefined,
        logo_url: formTenant.logo_url?.trim() || undefined,
        subtitulo_cabecalho: formTenant.subtitulo_cabecalho?.trim() || undefined,
        admin_nome: formTenant.admin_nome.trim(),
        admin_login: formTenant.admin_login.trim(),
        admin_senha: formTenant.admin_senha,
      };
      const resultado = await criarTenant(payload);
      setMensagemSucesso(
        `Tenant "${resultado.tenant.nome_fantasia}" criado com sucesso! Login do administrador: ${resultado.admin.login}`
      );
      setFormTenant(TENANT_CREATE_VAZIO);
      setMostrarFormTenant(false);
      carregarTenants();
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível criar o tenant."));
    } finally {
      setSalvandoTenant(false);
    }
  }

  async function handleAlternarAtivo(tenant: Tenant) {
    try {
      await atualizarTenant(tenant.id, { ativo: !tenant.ativo });
      carregarTenants();
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível atualizar o tenant."));
    }
  }

  return (
    <div className="mg-superadmin-shell">
      <header className="mg-superadmin-header">
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <HelluxIcon size={32} />
          <div>
            <strong style={{ fontSize: 16 }}>Painel de Administração</strong>
            <p style={{ margin: 0, fontSize: 12, color: "var(--mg-cinza-600)" }}>
              Gestão de hospitais-cliente (tenants)
            </p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <span style={{ fontSize: 14, color: "var(--mg-cinza-600)" }}>{usuario?.nome}</span>
          <button className="mg-btn mg-btn-outline" onClick={logout}>
            Sair
          </button>
        </div>
      </header>

      <main className="mg-content" style={{ maxWidth: 1100, margin: "0 auto", width: "100%" }}>
        {mensagemSucesso && (
          <p
            style={{
              color: "var(--mg-sucesso)",
              background: "rgba(34, 197, 94, 0.1)",
              border: "1px solid rgba(34, 197, 94, 0.3)",
              borderRadius: "var(--mg-radius-sm)",
              padding: "10px 14px",
              fontSize: 14,
            }}
          >
            {mensagemSucesso}
          </p>
        )}

        <div className="mg-card">
          <div className="mg-page-header">
            <div>
              <h2 style={{ margin: 0 }}>Tenants</h2>
              <p>Hospitais-cliente cadastrados no sistema</p>
            </div>
            <button
              className="mg-btn mg-btn-primary"
              onClick={() => setMostrarFormTenant((v) => !v)}
            >
              {mostrarFormTenant ? "Cancelar" : "+ Novo Tenant"}
            </button>
          </div>

          {mostrarFormTenant && (
            <form
              onSubmit={handleCriarTenant}
              className="mg-form-grid"
              style={{
                marginBottom: 20,
                paddingBottom: 20,
                borderBottom: "1px solid var(--mg-cinza-200)",
              }}
            >
              <div className="mg-field">
                <label>Nome fantasia</label>
                <input
                  required
                  minLength={2}
                  value={formTenant.nome_fantasia}
                  onChange={(e) =>
                    setFormTenant((f) => ({ ...f, nome_fantasia: e.target.value }))
                  }
                />
              </div>
              <div className="mg-field">
                <label>Razão social</label>
                <input
                  value={formTenant.razao_social}
                  onChange={(e) =>
                    setFormTenant((f) => ({ ...f, razao_social: e.target.value }))
                  }
                />
              </div>
              <div className="mg-field">
                <label>CNPJ</label>
                <input
                  value={formTenant.cnpj}
                  onChange={(e) => setFormTenant((f) => ({ ...f, cnpj: e.target.value }))}
                />
              </div>
              <div className="mg-field">
                <label>Subtítulo do cabeçalho</label>
                <input
                  value={formTenant.subtitulo_cabecalho}
                  onChange={(e) =>
                    setFormTenant((f) => ({ ...f, subtitulo_cabecalho: e.target.value }))
                  }
                />
              </div>
              <div className="mg-field" style={{ gridColumn: "1 / -1" }}>
                <label>URL do logo</label>
                <input
                  value={formTenant.logo_url}
                  onChange={(e) => setFormTenant((f) => ({ ...f, logo_url: e.target.value }))}
                />
              </div>

              <div style={{ gridColumn: "1 / -1" }}>
                <strong style={{ fontSize: 13, color: "var(--mg-cinza-600)" }}>
                  Primeiro administrador do tenant
                </strong>
              </div>
              <div className="mg-field">
                <label>Nome do administrador</label>
                <input
                  required
                  minLength={2}
                  value={formTenant.admin_nome}
                  onChange={(e) => setFormTenant((f) => ({ ...f, admin_nome: e.target.value }))}
                />
              </div>
              <div className="mg-field">
                <label>Login do administrador</label>
                <input
                  required
                  minLength={3}
                  value={formTenant.admin_login}
                  onChange={(e) =>
                    setFormTenant((f) => ({ ...f, admin_login: e.target.value }))
                  }
                />
              </div>
              <div className="mg-field">
                <label>Senha do administrador</label>
                <input
                  required
                  type="password"
                  minLength={8}
                  value={formTenant.admin_senha}
                  onChange={(e) =>
                    setFormTenant((f) => ({ ...f, admin_senha: e.target.value }))
                  }
                />
              </div>

              <div style={{ gridColumn: "1 / -1" }}>
                <button className="mg-btn mg-btn-primary" type="submit" disabled={salvandoTenant}>
                  {salvandoTenant ? "Salvando..." : "Cadastrar tenant"}
                </button>
              </div>
            </form>
          )}

          {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
          {!erro && carregando && <CarregandoBarras />}
          {!erro && !carregando && tenants.length === 0 && (
            <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
              Nenhum tenant cadastrado ainda.
            </p>
          )}
          {!erro && !carregando && tenants.length > 0 && (
            <table className="mg-table">
              <thead>
                <tr>
                  <th>Nome fantasia</th>
                  <th>CNPJ</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((tenant) => (
                  <tr
                    key={tenant.id}
                    onClick={() =>
                      setTenantSelecionadoId((atual) => (atual === tenant.id ? null : tenant.id))
                    }
                    style={{
                      cursor: "pointer",
                      background:
                        tenantSelecionadoId === tenant.id ? "var(--mg-cinza-100)" : undefined,
                    }}
                  >
                    <td>{tenant.nome_fantasia}</td>
                    <td>{tenant.cnpj || "—"}</td>
                    <td>
                      <span
                        className={`mg-badge ${tenant.ativo ? "mg-badge-sucesso" : "mg-badge-erro"}`}
                      >
                        {tenant.ativo ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td>
                      <button
                        className="mg-btn mg-btn-outline"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleAlternarAtivo(tenant);
                        }}
                      >
                        {tenant.ativo ? "Desativar" : "Ativar"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {tenantSelecionadoId && (
          <SecaoUsuariosTenant
            tenant={tenants.find((t) => t.id === tenantSelecionadoId) ?? null}
          />
        )}
      </main>
    </div>
  );
}

function SecaoUsuariosTenant({ tenant }: { tenant: Tenant | null }) {
  const [usuarios, setUsuarios] = useState<Usuario[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  const [mostrarForm, setMostrarForm] = useState(false);
  const [nome, setNome] = useState("");
  const [loginValue, setLoginValue] = useState("");
  const [senha, setSenha] = useState("");
  const [perfil, setPerfil] = useState<PerfilUsuario>("VISUALIZADOR");
  const [salvando, setSalvando] = useState(false);

  async function carregar(tenantId: string) {
    setCarregando(true);
    setErro(null);
    try {
      const res = await listarUsuariosPorTenant(tenantId);
      setUsuarios(res.items);
    } catch (err: unknown) {
      setErro(extrairMensagemErro(err, "Não foi possível carregar os usuários deste tenant."));
    } finally {
      setCarregando(false);
    }
  }

  // Recarrega sempre que o tenant selecionado muda (troca de linha na
  // tabela acima) - sem cache, o mesmo comportamento simples usado no
  // resto do app.
  useEffect(() => {
    if (!tenant) return;
    setMostrarForm(false);
    carregar(tenant.id);
  }, [tenant?.id]);

  if (!tenant) return null;

  // TS não propaga a checagem acima pra dentro de declarações de função
  // aninhadas - capturar o id num const separado resolve sem precisar de "!".
  const tenantId = tenant.id;

  async function handleCriarUsuario(e: FormEvent) {
    e.preventDefault();
    setSalvando(true);
    try {
      await criarUsuario({ nome, login: loginValue, senha, perfil, tenant_id: tenantId });
      setNome("");
      setLoginValue("");
      setSenha("");
      setPerfil("VISUALIZADOR");
      setMostrarForm(false);
      carregar(tenantId);
    } catch (err: unknown) {
      window.alert(extrairMensagemErro(err, "Não foi possível criar o usuário."));
    } finally {
      setSalvando(false);
    }
  }

  return (
    <div className="mg-card" style={{ marginTop: 20 }}>
      <div className="mg-page-header">
        <div>
          <h3 style={{ margin: 0 }}>Usuários de {tenant.nome_fantasia}</h3>
        </div>
        <button className="mg-btn mg-btn-primary" onClick={() => setMostrarForm((v) => !v)}>
          {mostrarForm ? "Cancelar" : "+ Novo Usuário"}
        </button>
      </div>

      {mostrarForm && (
        <form
          onSubmit={handleCriarUsuario}
          className="mg-form-grid"
          style={{ marginBottom: 20, paddingBottom: 16, borderBottom: "1px solid var(--mg-cinza-200)" }}
        >
          <div className="mg-field">
            <label>Nome</label>
            <input required value={nome} onChange={(e) => setNome(e.target.value)} />
          </div>
          <div className="mg-field">
            <label>Login</label>
            <input
              required
              minLength={3}
              value={loginValue}
              onChange={(e) => setLoginValue(e.target.value)}
            />
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
              {PERFIS_TENANT.map((p) => (
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
      {!erro && !carregando && usuarios.length === 0 && (
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
          Este tenant ainda não tem usuários cadastrados.
        </p>
      )}
      {!erro && !carregando && usuarios.length > 0 && (
        <table className="mg-table">
          <thead>
            <tr>
              <th>Nome</th>
              <th>Login</th>
              <th>Perfil</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id}>
                <td>{u.nome}</td>
                <td>{u.login}</td>
                <td>{u.perfil}</td>
                <td>
                  <span className={`mg-badge ${u.is_active ? "mg-badge-sucesso" : "mg-badge-erro"}`}>
                    {u.is_active ? "Ativo" : "Inativo"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
