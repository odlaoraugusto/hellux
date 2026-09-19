"""
Service do módulo CCIH (Sprint 9).

Por padrão, os indicadores são calculados sobre o mês corrente, mas o
período pode ser customizado (usado pelo Relatório mensal automático e
por consultas ad-hoc da comissão).

Fase 1 (fluxo de Exame unificado): reescrito sobre `Exame`. O filtro que
antes era por `origem` (string livre da Solicitação) agora é por
`setor_id` (FK de verdade pro catálogo de Setores) - o nome do setor
filtrado continua vindo na resposta em `filtro_setor`, para não quebrar
o contrato da API.
"""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.repositories.ccih_repository import CCIHRepository
from app.repositories.setor_repository import SetorRepository
from app.repositories.tipo_cultura_repository import TipoCulturaRepository
from app.schemas.ccih import (
    DistribuicaoSetorOut,
    IndicadoresCCIHOut,
    MatrizSensibilidadeItemOut,
    MatrizSensibilidadeOut,
    PerfilMicrobiologicoOut,
    TaxaResistenciaOut,
)


def _primeiro_dia_do_mes(referencia: date) -> date:
    return referencia.replace(day=1)


class CCIHService:
    def __init__(self, db: Session):
        self.repository = CCIHRepository(db)
        self.setor_repository = SetorRepository(db)
        self.tipo_cultura_repository = TipoCulturaRepository(db)

    def indicadores(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        setor_id: uuid.UUID | None = None,
        tipo_cultura_ids: list[uuid.UUID] | None = None,
    ) -> IndicadoresCCIHOut:
        """
        Indicadores gerais. `tipo_cultura_ids` filtra por um ou mais tipos
        de cultura do catálogo do tenant (ex.: só Hemocultura + Vigilância)
        - lista vazia/None não filtra, traz todos.
        """
        return self._calcular(data_inicio, data_fim, setor_id, tipo_cultura_ids)

    def indicadores_vigilancia(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        setor_id: uuid.UUID | None = None,
    ) -> IndicadoresCCIHOut:
        """
        Compatibilidade com o relatório PDF de vigilância (Fase 1.6): usa
        o filtro livre por `tipo_cultura_ids` resolvendo o(s) tipo(s) de
        cultura cujo nome é "vigilância" (case-insensitive) no catálogo do
        tenant - mesmo comportamento de antes, só que reaproveitando o
        filtro novo em vez de um caminho de código à parte.
        """
        tipo = self.tipo_cultura_repository.get_by_nome("vigilancia")
        # Sem tipo "vigilância" cadastrado -> filtro com um id inexistente
        # de propósito, pra não bater com nenhum exame (mesmo efeito do
        # filtro antigo, que também não trazia nenhum resultado nesse caso
        # - lista vazia/None em `_filtro_tipo_cultura` significaria "sem
        # filtro" e traria tudo, o oposto do que queremos aqui).
        tipo_cultura_ids = [tipo.id] if tipo else [uuid.uuid4()]
        return self._calcular(data_inicio, data_fim, setor_id, tipo_cultura_ids)

    def matriz_sensibilidade(
        self,
        data_inicio: date | None = None,
        data_fim: date | None = None,
        apenas_vigilancia: bool | None = False,
    ) -> MatrizSensibilidadeOut:
        """
        Matriz de Sensibilidade CCIH (Fase 1.5) - agrupa por macro-setor x
        família fenotípica x antimicrobiano, com os três percentuais
        S/I/R. Endpoint aditivo, não substitui `indicadores()` (ver
        docstring de `CCIHRepository.matriz_sensibilidade`).
        """
        hoje = date.today()
        inicio = data_inicio or _primeiro_dia_do_mes(hoje)
        fim = data_fim or hoje

        itens_raw = self.repository.matriz_sensibilidade(
            inicio, fim, apenas_vigilancia=apenas_vigilancia
        )
        itens = [
            MatrizSensibilidadeItemOut(
                macro_grupo=macro_grupo,
                grupo_fenotipico=grupo_fenotipico,
                antimicrobiano=antimicrobiano,
                total_testado=testado,
                sensivel=sensivel,
                intermediario=intermediario,
                resistente=resistente,
                percentual_sensivel=round((sensivel / testado) * 100, 1) if testado > 0 else 0.0,
                percentual_intermediario=round((intermediario / testado) * 100, 1)
                if testado > 0
                else 0.0,
                percentual_resistente=round((resistente / testado) * 100, 1) if testado > 0 else 0.0,
            )
            for macro_grupo, grupo_fenotipico, antimicrobiano, testado, sensivel, intermediario, resistente
            in itens_raw
        ]

        return MatrizSensibilidadeOut(periodo_inicio=inicio, periodo_fim=fim, itens=itens)

    def _nome_do_setor(self, setor_id: uuid.UUID | None) -> str | None:
        if not setor_id:
            return None
        setor = self.setor_repository.get_by_id(setor_id)
        return setor.nome if setor else None

    def _nomes_dos_tipos_cultura(
        self, tipo_cultura_ids: list[uuid.UUID] | None
    ) -> list[str] | None:
        if not tipo_cultura_ids:
            return None
        nomes = [
            tipo.nome
            for tipo_id in tipo_cultura_ids
            if (tipo := self.tipo_cultura_repository.get_by_id(tipo_id)) is not None
        ]
        return nomes or None

    def _calcular(
        self,
        data_inicio: date | None,
        data_fim: date | None,
        setor_id: uuid.UUID | None,
        tipo_cultura_ids: list[uuid.UUID] | None,
    ) -> IndicadoresCCIHOut:
        hoje = date.today()
        inicio = data_inicio or _primeiro_dia_do_mes(hoje)
        fim = data_fim or hoje

        total_exames = self.repository.total_exames(
            inicio, fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_ids
        )

        total_finalizados = self.repository.total_exames_por_status(
            inicio, fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_ids
        )
        total_positivos = self.repository.total_exames_por_status(
            inicio,
            fim,
            apenas_positivos=True,
            setor_id=setor_id,
            tipo_cultura_ids=tipo_cultura_ids,
        )

        taxa_positividade = (
            round((total_positivos / total_finalizados) * 100, 1)
            if total_finalizados > 0
            else 0.0
        )

        distribuicao_raw = self.repository.distribuicao_por_setor(
            inicio, fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_ids
        )
        distribuicao = [
            DistribuicaoSetorOut(setor=setor, total_positivas=total)
            for setor, total in distribuicao_raw
        ]

        perfil_raw = self.repository.perfil_microbiologico(
            inicio, fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_ids
        )
        total_isolados = sum(qtd for _, qtd in perfil_raw)
        perfil = [
            PerfilMicrobiologicoOut(
                microrganismo=nome,
                quantidade=quantidade,
                percentual=round((quantidade / total_isolados) * 100, 1)
                if total_isolados > 0
                else 0.0,
            )
            for nome, quantidade in perfil_raw
        ]

        resistencia_raw = self.repository.taxa_resistencia(
            inicio, fim, setor_id=setor_id, tipo_cultura_ids=tipo_cultura_ids
        )
        resistencia = [
            TaxaResistenciaOut(
                antimicrobiano=nome,
                total_testado=testado,
                total_resistente=resistente,
                percentual_resistente=round((resistente / testado) * 100, 1)
                if testado > 0
                else 0.0,
                total_sensivel=sensivel,
                percentual_sensivel=round((sensivel / testado) * 100, 1)
                if testado > 0
                else 0.0,
            )
            for nome, testado, resistente, sensivel in resistencia_raw
        ]

        return IndicadoresCCIHOut(
            periodo_inicio=inicio,
            periodo_fim=fim,
            filtro_setor=self._nome_do_setor(setor_id),
            filtro_tipos_cultura=self._nomes_dos_tipos_cultura(tipo_cultura_ids),
            total_solicitacoes=total_exames,
            total_culturas_positivas=total_positivos,
            taxa_positividade=taxa_positividade,
            distribuicao_por_setor=distribuicao,
            perfil_microbiologico=perfil,
            taxa_resistencia=resistencia,
        )
