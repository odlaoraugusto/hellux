import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { CarregandoBarras } from "../components/CarregandoBarras";
import RankedListCard from "../components/RankedListCard";
import { obterIndicadoresCCIH } from "../services/ccihService";
import { listarSetores } from "../services/setorService";
import { listarTiposCultura } from "../services/tipoCulturaService";
import { IndicadoresCCIH } from "../types/ccih";
import { Setor } from "../types/setor";
import { TipoCultura } from "../types/tipoCultura";
import { formatarNomeCatalogo } from "../utils/texto";

function hojeISO() {
  return new Date().toISOString().slice(0, 10);
}

function primeiroDiaDoMesISO() {
  const agora = new Date();
  return new Date(agora.getFullYear(), agora.getMonth(), 1).toISOString().slice(0, 10);
}

export default function CcihPage() {
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMesISO());
  const [dataFim, setDataFim] = useState(hojeISO());
  const [setorId, setSetorId] = useState("");
  const [setoresCatalogo, setSetoresCatalogo] = useState<Setor[]>([]);
  const [tiposCulturaCatalogo, setTiposCulturaCatalogo] = useState<TipoCultura[]>([]);
  const [tiposCulturaSelecionados, setTiposCulturaSelecionados] = useState<string[]>([]);
  const [indicadores, setIndicadores] = useState<IndicadoresCCIH | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);

  async function carregar() {
    setCarregando(true);
    setErro(null);
    try {
      const resultado = await obterIndicadoresCCIH({
        dataInicio,
        dataFim,
        setorId: setorId || undefined,
        tipoCulturaIds: tiposCulturaSelecionados,
      });
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

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    carregar();
  }, []);

  useEffect(() => {
    listarSetores().then((res) => setSetoresCatalogo(res.items));
    listarTiposCultura().then((res) => setTiposCulturaCatalogo(res.items));
  }, []);

  function alternarTipoCultura(id: string) {
    setTiposCulturaSelecionados((atual) =>
      atual.includes(id) ? atual.filter((x) => x !== id) : [...atual, id]
    );
  }

  return (
    <MainLayout titulo="CCIH" subtitulo="Indicadores epidemiológicos e perfil de resistência">
      <div className="mg-page-header" style={{ flexDirection: "column", alignItems: "stretch", gap: 12 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center", flexWrap: "wrap" }}>
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
            <select value={setorId} onChange={(e) => setSetorId(e.target.value)}>
              <option value="">Todos os setores</option>
              {setoresCatalogo.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </select>
          </div>
          <button className="mg-btn mg-btn-primary" onClick={carregar}>
            Aplicar
          </button>
        </div>

        {tiposCulturaCatalogo.length > 0 && (
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            <label style={{ fontSize: 13, fontWeight: 500, color: "var(--mg-cinza-600)" }}>
              Tipo de cultura
            </label>
            {tiposCulturaCatalogo.map((t) => {
              const ativo = tiposCulturaSelecionados.includes(t.id);
              return (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => alternarTipoCultura(t.id)}
                  className={`mg-btn ${ativo ? "mg-btn-primary" : "mg-btn-outline"}`}
                  style={{ padding: "6px 12px", fontSize: 13 }}
                >
                  {formatarNomeCatalogo(t.nome)}
                </button>
              );
            })}
            {tiposCulturaSelecionados.length > 0 && (
              <button
                type="button"
                onClick={() => setTiposCulturaSelecionados([])}
                style={{
                  background: "none",
                  border: "none",
                  padding: "6px 4px",
                  fontSize: 13,
                  color: "var(--mg-cinza-600)",
                }}
              >
                Limpar
              </button>
            )}
          </div>
        )}
      </div>

      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 14 }}>{erro}</p>}
      {!erro && carregando && <CarregandoBarras />}

      {!erro && !carregando && indicadores && (
        <>
          <p style={{ margin: "-8px 0 16px 0", fontSize: 13, color: "var(--mg-cinza-600)" }}>
            Indicadores de{" "}
            {new Date(`${indicadores.periodo_inicio}T00:00:00`).toLocaleDateString("pt-BR")} até{" "}
            {new Date(`${indicadores.periodo_fim}T00:00:00`).toLocaleDateString("pt-BR")}
            {indicadores.filtro_setor && (
              <>
                {" "}
                · <strong>Setor: {indicadores.filtro_setor}</strong>
              </>
            )}
            {indicadores.filtro_tipos_cultura && indicadores.filtro_tipos_cultura.length > 0 && (
              <>
                {" "}
                · <strong>
                  Tipo de cultura:{" "}
                  {indicadores.filtro_tipos_cultura.map(formatarNomeCatalogo).join(", ")}
                </strong>
              </>
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
            <RankedListCard
              titulo="Distribuição por Setor"
              itens={indicadores.distribuicao_por_setor.map((s) => ({
                nome: s.setor,
                quantidade: s.total_positivas,
              }))}
            />

            <RankedListCard
              titulo="Perfil Microbiológico"
              itens={indicadores.perfil_microbiologico.map((p) => ({
                nome: p.microrganismo,
                quantidade: p.quantidade,
                rotuloValor: `${p.percentual}%`,
              }))}
            />
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
