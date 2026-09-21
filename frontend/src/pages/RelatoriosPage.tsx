import { useEffect, useState } from "react";
import MainLayout from "../layouts/MainLayout";
import { api, extrairMensagemErroDownload } from "../services/api";
import { listarSetores } from "../services/setorService";
import { Setor } from "../types/setor";

function hojeISO() {
  return new Date().toISOString().slice(0, 10);
}

function primeiroDiaDoMesISO() {
  const agora = new Date();
  return new Date(agora.getFullYear(), agora.getMonth(), 1).toISOString().slice(0, 10);
}

/**
 * Baixa um arquivo autenticado da API.
 *
 * Os relatórios exigem login (o backend trava esses endpoints), então não
 * dá pra usar um simples `<a href>` - navegação de link não carrega o
 * header Authorization. Por isso o download é feito via axios (que já
 * anexa o token automaticamente) e o arquivo é entregue como Blob.
 */
async function baixarArquivo(
  caminho: string,
  nomeArquivo: string,
  params?: Record<string, string>
) {
  const response = await api.get(caminho, { params, responseType: "blob" });
  const url = window.URL.createObjectURL(new Blob([response.data]));
  const link = document.createElement("a");
  link.href = url;
  link.download = nomeArquivo;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

interface RelatorioCardProps {
  titulo: string;
  descricao: string;
  botaoLabel: string;
  onBaixar: () => Promise<void>;
}

function RelatorioCard({ titulo, descricao, botaoLabel, onBaixar }: RelatorioCardProps) {
  const [baixando, setBaixando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  async function handleClick() {
    setBaixando(true);
    setErro(null);
    try {
      await onBaixar();
    } catch (err: unknown) {
      setErro(await extrairMensagemErroDownload(err));
    } finally {
      setBaixando(false);
    }
  }

  return (
    <div className="mg-card" style={{ flex: 1, minWidth: 280 }}>
      <h3 style={{ marginTop: 0 }}>{titulo}</h3>
      <p style={{ color: "var(--mg-cinza-600)", fontSize: 13, minHeight: 36 }}>{descricao}</p>
      {erro && <p style={{ color: "var(--mg-erro)", fontSize: 12 }}>{erro}</p>}
      <button className="mg-btn mg-btn-primary" onClick={handleClick} disabled={baixando}>
        {baixando ? "Baixando..." : botaoLabel}
      </button>
    </div>
  );
}

export default function RelatoriosPage() {
  const [dataInicio, setDataInicio] = useState(primeiroDiaDoMesISO());
  const [dataFim, setDataFim] = useState(hojeISO());
  const [setorId, setSetorId] = useState("");
  const [setoresCatalogo, setSetoresCatalogo] = useState<Setor[]>([]);
  const [baixandoCcih, setBaixandoCcih] = useState(false);
  const [erroCcih, setErroCcih] = useState<string | null>(null);
  const [baixandoCcihVigilancia, setBaixandoCcihVigilancia] = useState(false);
  const [erroCcihVigilancia, setErroCcihVigilancia] = useState<string | null>(null);

  useEffect(() => {
    listarSetores().then((res) => setSetoresCatalogo(res.items));
  }, []);

  async function handleBaixarCcih() {
    setBaixandoCcih(true);
    setErroCcih(null);
    try {
      const params: Record<string, string> = { data_inicio: dataInicio, data_fim: dataFim };
      if (setorId) params.setor_id = setorId;
      await baixarArquivo("/api/relatorios/ccih.pdf", "hellux_relatorio_ccih.pdf", params);
    } catch (err: unknown) {
      setErroCcih(await extrairMensagemErroDownload(err));
    } finally {
      setBaixandoCcih(false);
    }
  }

  async function handleBaixarCcihVigilancia() {
    setBaixandoCcihVigilancia(true);
    setErroCcihVigilancia(null);
    try {
      const params: Record<string, string> = { data_inicio: dataInicio, data_fim: dataFim };
      if (setorId) params.setor_id = setorId;
      await baixarArquivo(
        "/api/relatorios/ccih-vigilancia.pdf",
        "hellux_relatorio_ccih_vigilancia.pdf",
        params
      );
    } catch (err: unknown) {
      setErroCcihVigilancia(await extrairMensagemErroDownload(err));
    } finally {
      setBaixandoCcihVigilancia(false);
    }
  }

  return (
    <MainLayout titulo="Relatórios" subtitulo="Exportação de dados e relatório da CCIH">
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap", marginBottom: 16 }}>
        <RelatorioCard
          titulo="Pacientes (Excel)"
          descricao="Exporta a lista completa de pacientes cadastrados, com setor e leito."
          botaoLabel="Baixar .xlsx"
          onBaixar={() =>
            baixarArquivo("/api/relatorios/pacientes.xlsx", "hellux_pacientes.xlsx")
          }
        />
        <RelatorioCard
          titulo="Exames (Excel)"
          descricao="Exporta todos os exames registrados, com setor, tipo de cultura, material e status."
          botaoLabel="Baixar .xlsx"
          onBaixar={() => baixarArquivo("/api/relatorios/exames.xlsx", "hellux_exames.xlsx")}
        />
        <RelatorioCard
          titulo="Resultados Parciais (Excel)"
          descricao="Exames ainda em andamento (não liberados), com previsão de liberação e o que está pendente em cada um."
          botaoLabel="Baixar .xlsx"
          onBaixar={() =>
            baixarArquivo(
              "/api/relatorios/exames-parciais.xlsx",
              "hellux_resultados_parciais.xlsx"
            )
          }
        />
      </div>

      <div className="mg-card" style={{ maxWidth: 560 }}>
        <h3 style={{ marginTop: 0 }}>Relatório CCIH (PDF)</h3>
        <p style={{ color: "var(--mg-cinza-600)", fontSize: 13 }}>
          Resumo geral, distribuição por setor, perfil microbiológico e mapa de resistência do
          período selecionado — calculado pela data da coleta. As culturas de vigilância ficam de
          fora deste relatório (têm o relatório dedicado abaixo).
        </p>

        <div className="mg-form-grid" style={{ marginBottom: 16 }}>
          <div className="mg-field">
            <label>De</label>
            <input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
          </div>
          <div className="mg-field">
            <label>Até</label>
            <input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
          </div>
          <div className="mg-field" style={{ gridColumn: "1 / -1" }}>
            <label>Setor</label>
            <select value={setorId} onChange={(e) => setSetorId(e.target.value)}>
              <option value="">Todos os setores</option>
              {setoresCatalogo.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.nome}
                </option>
              ))}
            </select>
          </div>
        </div>

        {erroCcih && <p style={{ color: "var(--mg-erro)", fontSize: 12 }}>{erroCcih}</p>}
        <button
          className="mg-btn mg-btn-primary"
          onClick={handleBaixarCcih}
          disabled={baixandoCcih}
          style={{ marginBottom: 8 }}
        >
          {baixandoCcih ? "Baixando..." : "Baixar relatório geral .pdf"}
        </button>

        {erroCcihVigilancia && (
          <p style={{ color: "var(--mg-erro)", fontSize: 12 }}>{erroCcihVigilancia}</p>
        )}
        <button
          className="mg-btn mg-btn-outline"
          onClick={handleBaixarCcihVigilancia}
          disabled={baixandoCcihVigilancia}
        >
          {baixandoCcihVigilancia ? "Baixando..." : "Baixar relatório de vigilância .pdf"}
        </button>
      </div>
    </MainLayout>
  );
}
