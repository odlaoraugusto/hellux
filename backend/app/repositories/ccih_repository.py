"""
Repository do módulo CCIH.

Todas as consultas aqui são agregações sobre Exames, Microrganismos e
Antimicrobianos já existentes - a CCIH não introduz nenhuma tabela nova,
apenas uma nova forma de olhar para os dados que o laboratório já
produz no dia a dia.

O período é sempre calculado pela data da coleta (`Exame.data_coleta`,
sempre preenchida no fluxo unificado - não precisa mais de fallback).

Fase 1 (fluxo de Exame unificado): reescrito sobre `Exame`/`ExameIsolado`/
`ExameAntibiograma`. O antigo filtro fixo por `GrupoCulturaEnum.VIGILANCIA`
vira uma comparação pelo NOME do `TipoCultura` (agora um catálogo livre
por tenant, não mais um enum fixo) - a migration da Fase 1 semeia um
`TipoCultura` chamado "VIGILANCIA" para o tenant migrado, preservando o
comportamento atual; tenants novos que nomearem seu tipo de vigilância de
forma diferente precisam usar exatamente esse nome por enquanto
(limitação conhecida, documentada no relatório da Fase 1).
"""
from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.antimicrobiano import Antimicrobiano
from app.models.exame import (
    STATUS_POSITIVO,
    Exame,
    ExameAntibiograma,
    ExameIsolado,
    ResultadoSIREnum,
    StatusExameEnum,
)
from app.models.microrganismo import Microrganismo
from app.models.setor import Setor
from app.models.tipo_cultura import TipoCultura

SETOR_NAO_INFORMADO = "Não informado"
NOME_TIPO_CULTURA_VIGILANCIA = "vigilancia"

# `func.date(...)` funciona tanto no Postgres quanto no SQLite (usado
# pela suíte de testes) - um `cast(col, Date)` puro não é confiável no
# SQLite, que não tem afinidade de tipo DATE de verdade (cai em NUMERIC
# e zera o valor). Mesmo padrão já usado em dashboard_repository.py.
DATA_REFERENCIA = func.date(Exame.data_coleta)


class CCIHRepository:
    def __init__(self, db: Session):
        self.db = db

    def _filtro_vigilancia(self, stmt, apenas_vigilancia: bool | None):
        """
        `apenas_vigilancia=True` -> só exames cujo tipo de cultura é
        "vigilância"; `False` -> todos, EXCETO vigilância; `None` -> sem
        filtro nenhum por tipo de cultura.
        """
        if apenas_vigilancia is None:
            return stmt
        stmt = stmt.join(TipoCultura, TipoCultura.id == Exame.tipo_cultura_id)
        if apenas_vigilancia:
            return stmt.where(func.lower(TipoCultura.nome) == NOME_TIPO_CULTURA_VIGILANCIA)
        return stmt.where(func.lower(TipoCultura.nome) != NOME_TIPO_CULTURA_VIGILANCIA)

    def total_exames(
        self,
        inicio: date,
        fim: date,
        setor_id=None,
        apenas_vigilancia: bool | None = None,
    ) -> int:
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True),
            DATA_REFERENCIA >= inicio,
            DATA_REFERENCIA <= fim,
        )
        if setor_id:
            stmt = stmt.where(Exame.setor_id == setor_id)
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        return self.db.scalar(stmt) or 0

    def total_exames_por_status(
        self,
        inicio: date,
        fim: date,
        apenas_positivos: bool = False,
        setor_id=None,
        apenas_vigilancia: bool | None = None,
    ) -> int:
        stmt = select(func.count(Exame.id)).where(
            Exame.is_active.is_(True),
            DATA_REFERENCIA >= inicio,
            DATA_REFERENCIA <= fim,
        )
        if apenas_positivos:
            stmt = stmt.where(Exame.status.in_(STATUS_POSITIVO))
        else:
            stmt = stmt.where(Exame.status != StatusExameEnum.AGUARDANDO_TRIAGEM)
        if setor_id:
            stmt = stmt.where(Exame.setor_id == setor_id)
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        return self.db.scalar(stmt) or 0

    def distribuicao_por_setor(
        self,
        inicio: date,
        fim: date,
        setor_id=None,
        apenas_vigilancia: bool | None = None,
    ) -> list[tuple[str, int]]:
        nome_setor = func.coalesce(Setor.nome, SETOR_NAO_INFORMADO)
        stmt = (
            select(nome_setor, func.count(Exame.id))
            .select_from(Exame)
            .outerjoin(Setor, Setor.id == Exame.setor_id)
            .where(
                Exame.is_active.is_(True),
                Exame.status.in_(STATUS_POSITIVO),
                DATA_REFERENCIA >= inicio,
                DATA_REFERENCIA <= fim,
            )
            .group_by(nome_setor)
            .order_by(func.count(Exame.id).desc())
        )
        if setor_id:
            stmt = stmt.where(Exame.setor_id == setor_id)
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        return list(self.db.execute(stmt).all())

    def perfil_microbiologico(
        self,
        inicio: date,
        fim: date,
        setor_id=None,
        apenas_vigilancia: bool | None = None,
    ) -> list[tuple[str, int]]:
        stmt = (
            select(Microrganismo.nome, func.count(ExameIsolado.id))
            .select_from(ExameIsolado)
            .join(Microrganismo, Microrganismo.id == ExameIsolado.microrganismo_id)
            .join(Exame, Exame.id == ExameIsolado.exame_id)
            .where(
                Exame.is_active.is_(True),
                Exame.status.in_(STATUS_POSITIVO),
                DATA_REFERENCIA >= inicio,
                DATA_REFERENCIA <= fim,
            )
            .group_by(Microrganismo.nome)
            .order_by(func.count(ExameIsolado.id).desc())
        )
        if setor_id:
            stmt = stmt.where(Exame.setor_id == setor_id)
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        return list(self.db.execute(stmt).all())

    def taxa_resistencia(
        self,
        inicio: date,
        fim: date,
        setor_id=None,
        apenas_vigilancia: bool | None = None,
    ) -> list[tuple[str, int, int, int]]:
        total_testado = func.count(ExameAntibiograma.id)
        total_resistente = func.sum(
            case((ExameAntibiograma.resultado == ResultadoSIREnum.RESISTENTE, 1), else_=0)
        )
        total_sensivel = func.sum(
            case((ExameAntibiograma.resultado == ResultadoSIREnum.SENSIVEL, 1), else_=0)
        )
        stmt = (
            select(Antimicrobiano.nome, total_testado, total_resistente, total_sensivel)
            .select_from(ExameAntibiograma)
            .join(Antimicrobiano, Antimicrobiano.id == ExameAntibiograma.antimicrobiano_id)
            .join(ExameIsolado, ExameIsolado.id == ExameAntibiograma.isolado_id)
            .join(Exame, Exame.id == ExameIsolado.exame_id)
            .where(
                Exame.is_active.is_(True),
                # Exclui contaminação (bug de dado corrigido na Fase 1.5 -
                # a regra "não contar contaminação" já é intenção do
                # módulo, só nunca tinha sido aplicada neste indicador).
                Exame.status != StatusExameEnum.CONTAMINACAO,
                DATA_REFERENCIA >= inicio,
                DATA_REFERENCIA <= fim,
            )
            .group_by(Antimicrobiano.nome)
            .order_by(total_testado.desc())
        )
        if setor_id:
            stmt = stmt.where(Exame.setor_id == setor_id)
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        resultado = self.db.execute(stmt).all()
        return [
            (nome, testado, resistente or 0, sensivel or 0)
            for nome, testado, resistente, sensivel in resultado
        ]

    def matriz_sensibilidade(
        self,
        inicio: date,
        fim: date,
        apenas_vigilancia: bool | None = None,
    ) -> list[tuple[str, str, str, int, int, int, int]]:
        """
        Matriz de Sensibilidade CCIH (Fase 1.5): agrupa os resultados de
        antibiograma por `(macro_grupo do setor, grupo_fenotipico do
        microrganismo, antimicrobiano)`, com os três percentuais (S/I/R -
        o indicador antigo `taxa_resistencia` só tinha S/R).

        Regras de exclusão (além do período): `Exame.status ==
        CONTAMINACAO` e `ExameIsolado.nao_realizado_tecnico == True`
        (dispensa técnica do antibiograma daquele isolado específico).
        """
        macro_grupo = func.coalesce(Setor.macro_grupo, "Não classificado")
        total_testado = func.count(ExameAntibiograma.id)
        total_sensivel = func.sum(
            case((ExameAntibiograma.resultado == ResultadoSIREnum.SENSIVEL, 1), else_=0)
        )
        total_intermediario = func.sum(
            case((ExameAntibiograma.resultado == ResultadoSIREnum.INTERMEDIARIO, 1), else_=0)
        )
        total_resistente = func.sum(
            case((ExameAntibiograma.resultado == ResultadoSIREnum.RESISTENTE, 1), else_=0)
        )

        stmt = (
            select(
                macro_grupo,
                Microrganismo.grupo_fenotipico,
                Antimicrobiano.nome,
                total_testado,
                total_sensivel,
                total_intermediario,
                total_resistente,
            )
            .select_from(ExameAntibiograma)
            .join(Antimicrobiano, Antimicrobiano.id == ExameAntibiograma.antimicrobiano_id)
            .join(ExameIsolado, ExameIsolado.id == ExameAntibiograma.isolado_id)
            .join(Microrganismo, Microrganismo.id == ExameIsolado.microrganismo_id)
            .join(Exame, Exame.id == ExameIsolado.exame_id)
            .outerjoin(Setor, Setor.id == Exame.setor_id)
            .where(
                Exame.is_active.is_(True),
                Exame.status != StatusExameEnum.CONTAMINACAO,
                ExameIsolado.nao_realizado_tecnico.is_(False),
                DATA_REFERENCIA >= inicio,
                DATA_REFERENCIA <= fim,
            )
            .group_by(macro_grupo, Microrganismo.grupo_fenotipico, Antimicrobiano.nome)
            .order_by(macro_grupo, Microrganismo.grupo_fenotipico, Antimicrobiano.nome)
        )
        stmt = self._filtro_vigilancia(stmt, apenas_vigilancia)
        resultado = self.db.execute(stmt).all()
        return [
            (macro, grupo_fenotipico, nome, testado, sensivel or 0, intermediario or 0, resistente or 0)
            for macro, grupo_fenotipico, nome, testado, sensivel, intermediario, resistente in resultado
        ]
