import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import { obterIndicadoresCCIH, obterIndicadoresCCIHVigilancia } from "../services/ccihService";
import { listarSetores } from "../services/setorService";
import { IndicadoresCCIH } from "../types/ccih";

type Visao = "geral" | "vigilancia";

function hojeISO() {
  return new Date().toISOString().slice(0, 10);
}

function primeiroDiaDoMesISO() {
  const agora = new Date();
  return new Date(agora.getFullYear(), agora.getMonth(), 1).toISOString().slice(0, 10);
}

function BarraPercentual({ percentual, cor }: { percentual: number; cor: string }) {
  return (
    <div
      style={{
        background: "var(--mg-cinza-100)",
        borderRadius: 999,
        height: 8,
        width: "100%",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${Math.min(percentual, 100)}%`,
          background: cor,
          height: "100%",
          borderRadius: 999,
        }}
      />
    </div>
  );
}

export default function CcihPage() {
  const [visao, setVisao] = useState<Visao>("geral");
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMesISO());
  const [dataFim, setDataFim] = useState(hojeISO());
  const [setor, setSetor] = useState("");
  const [setoresCatalogo, setSetoresCatalogo] = useState<string[]>([]);
  const [indicadores, setIndicadores] = useState<IndicadoresCCIH | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const buscar = visao === "vigilancia" ? obterIndicadoresCCIHVigilancia : obterIndicadoresCCIH;
      const resultado = await buscar(dataInicio, dataFim, setor || undefined);
      setIndicadores(resultado);
    } catch {
      setErro(
        "Não foi possível carregar os indicadores da CCIH. Verifique se a API está " +
          "rodando em http://localhost:8000."
      );
    } finally {
      setCarregando(false);
    }
  }

  // Recarrega ao trocar de visão (Geral / Vigilância) e uma vez na montagem.
  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visao]);

  useEffect(() => {
    listarSetores().then((res) => setSetoresCatalogo(res.items.map((s) => s.nome)));
  }, []);

  return (
    <MainLayout titulo="CCIH" subtitulo="Indicadores epidemiológicos e perfil de resistência">
      <div className="mg-page-header" style={{ marginBottom: 10 }}>
        <div style={{ display: "flex", gap: 8 }}>
          <button
            className={`mg-btn ${visao === "geral" ? "mg-btn-primary" : "mg-btn-outline"}`}
            onClick={() => setVisao("geral")}
          >
            Geral
          </button>
          <button
            className={`mg-btn ${visao === "vigilancia" ? "mg-btn-primary" : "mg-btn-outline"}`}
            onClick={() => setVisao("vigilancia")}
          >
            Cultura de Vigilância
          </button>
        </div>
      </div>

      <div className="mg-page-header">
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div className="mg-field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <label style={{ margin: 0 }}>De</label>
            <input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
          </div>
          <div className="mg-field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <label style={{ margin: 0 }}>até</label>
            <input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
          </div>
          <div className="mg-field" style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
            <label style={{ margin: 0 }}>Setor</label>
            <select value={setor} onChange={(e) => setSetor(e.target.value)}>
              <option value="">Todos os setores</option>
              {setoresCatalogo.map((nome) => (
                <option key={nome} value={nome}>
                  {nome}
                </option>
              ))}
            </select>
          </div>
          <button className="mg-btn mg-btn-primary" onClick={carregar}>
            Aplicar
          </button>
        </div>
      </div>

      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
      {!erro && carregando && <CarregandoBarras />}

      {!erro && !carregando && indicadores && (
        <>
          <p style={{ margin: "-8px 0 16px 0", fontSize: 13, color: "var(--mg-cinza-600)" }}>
            Indicadores de{" "}
            {new Date(`${indicadores.periodo_inicio}T00:00:00`).toLocaleDateString("pt-BR")} até{" "}
            {new Date(`${indicadores.periodo_fim}T00:00:00`).toLocaleDateString("pt-BR")} ·{" "}
            {indicadores.filtro_setor ? (
              <strong>Setor: {indicadores.filtro_setor}</strong>
            ) : (
              "todos os setores"
            )}
          </p>

          <div style={{ display: "flex", gap: 16, marginBottom: 20, flexWrap: "wrap" }}>
            <div className="mg-card" style={{ flex: 1, minWidth: 160 }}>
              <p style={{ margin: 0, fontSize: 13, color: "var(--mg-cinza-600)" }}>Solicitações</p>
              <h2 style={{ margin: "6px 0 0 0", fontSize: 28 }}>{indicadores.total_solicitacoes}</h2>
            </div>
            <div className="mg-card" style={{ flex: 1, minWidth: 160 }}>
              <p style={{ margin: 0, fontSize: 13, color: "var(--mg-cinza-600)" }}>Culturas Positivas</p>
              <h2 style={{ margin: "6px 0 0 0", fontSize: 28, color: "var(--mg-erro)" }}>
                {indicadores.total_culturas_positivas}
              </h2>
            </div>
            <div className="mg-card" style={{ flex: 1, minWidth: 160 }}>
              <p style={{ margin: 0, fontSize: 13, color: "var(--mg-cinza-600)" }}>Taxa de Positividade</p>
              <h2 style={{ margin: "6px 0 0 0", fontSize: 28, color: "var(--mg-alerta)" }}>
                {indicadores.taxa_positividade}%
              </h2>
            </div>
          </div>

          <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Distribuição por Setor</h3>
              {indicadores.distribuicao_por_setor.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>Sem dados no período.</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {indicadores.distribuicao_por_setor.map((s) => (
                    <div key={s.setor}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                        <span>{s.setor}</span>
                        <strong>{s.total_positivas}</strong>
                      </div>
                      <BarraPercentual
                        percentual={
                          (s.total_positivas / indicadores.total_culturas_positivas) * 100 || 0
                        }
                        cor="var(--mg-primaria)"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
              <h3 style={{ marginTop: 0 }}>Perfil Microbiológico</h3>
              {indicadores.perfil_microbiologico.length === 0 ? (
                <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>Sem dados no período.</p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                  {indicadores.perfil_microbiologico.map((p) => (
                    <div key={p.microrganismo}>
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 4 }}>
                        <span>{p.microrganismo}</span>
                        <strong>{p.percentual}%</strong>
                      </div>
                      <BarraPercentual percentual={p.percentual} cor="var(--mg-secundaria)" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="mg-card">
            <h3 style={{ marginTop: 0 }}>Mapa de Resistência</h3>
            {indicadores.taxa_resistencia.length === 0 ? (
              <p style={{ color: "var(--mg-cinza-600)", fontSize: 14 }}>
                Nenhum antibiograma liberado no período.
              </p>
            ) : (
              <table className="mg-table">
                <thead>
                  <tr>
                    <th>Antimicrobiano</th>
                    <th>Testados</th>
                    <th>Resistentes</th>
                    <th>% Resistência</th>
                    <th>Sensíveis</th>
                    <th>% Sensibilidade</th>
                  </tr>
                </thead>
                <tbody>
                  {indicadores.taxa_resistencia.map((r) => (
                    <tr key={r.antimicrobiano}>
                      <td>{r.antimicrobiano}</td>
                      <td>{r.total_testado}</td>
                      <td>{r.total_resistente}</td>
                      <td>
                        <span
                          className={`mg-badge ${
                            r.percentual_resistente >= 50 ? "mg-badge-erro" : "mg-badge-alerta"
                          }`}
                        >
                          {r.percentual_resistente}%
                        </span>
                      </td>
                      <td>{r.total_sensivel}</td>
                      <td>
                        <span
                          className={`mg-badge ${
                            r.percentual_sensivel >= 50 ? "mg-badge-sucesso" : "mg-badge-alerta"
                          }`}
                        >
                          {r.percentual_sensivel}%
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </>
      )}
    </MainLayout>
  );
}
