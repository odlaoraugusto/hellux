"""
Service do Dashboard (Sprint 8).

Monta o resumo exibido na tela inicial a partir de consultas agregadas
sobre Exames. Os "alertas" seguem o espírito da "IA silenciosa" descrita
no planejamento do projeto: o sistema entrega informação pronta, sem
exigir que o usuário faça perguntas.

Os nomes dos campos de saída (`culturas_hoje`, `liberados_hoje`, etc.)
foram mantidos por compatibilidade mesmo após a Fase 1 (fluxo de Exame
unificado) trocar a fonte de dados por baixo - o contrato da API não
muda, só o que alimenta cada número.

Os campos `*_mes` (dashboard redesenhado) são calculados sobre o mês
corrente (dia 1 até hoje), usando `Exame.created_at` como referência
temporal - o mesmo campo já usado por `culturas_hoje`, pra manter os
dois consistentes entre si (ver `DashboardRepository._filtro_mes_corrente`).
"""
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import (
    AlertaOut,
    ContagemCatalogoOut,
    ContagemDiariaOut,
    ContagemStatusOut,
    ResumoDashboardOut,
    TopMicrorganismoOut,
)


class DashboardService:
    def __init__(self, db: Session):
        self.repository = DashboardRepository(db)

    def resumo(self) -> ResumoDashboardOut:
        exames_hoje = self.repository.contar_exames_criados_hoje()
        aguardando_atualizacao = self.repository.contar_exames_em_andamento()
        prazo_vencido = self.repository.contar_exames_com_prazo_vencido()
        finalizados_hoje = self.repository.contar_exames_finalizados_hoje()
        top = self.repository.top_microrganismos()
        aguardando_finalizacao = self.repository.exames_positivos_aguardando_finalizacao()

        top_microrganismos = [
            TopMicrorganismoOut(nome=nome, quantidade=quantidade) for nome, quantidade in top
        ]

        total_exames_mes = self.repository.contar_exames_mes()
        positivos_mes = self.repository.contar_exames_positivos_mes()
        taxa_positividade_mes = (
            round((positivos_mes / total_exames_mes) * 100, 1) if total_exames_mes > 0 else 0.0
        )
        por_tipo_cultura = [
            ContagemCatalogoOut(nome=nome, quantidade=quantidade)
            for nome, quantidade in self.repository.exames_por_tipo_cultura_mes()
        ]
        por_material = [
            ContagemCatalogoOut(nome=nome, quantidade=quantidade)
            for nome, quantidade in self.repository.exames_por_material_mes()
        ]
        por_setor = [
            ContagemCatalogoOut(nome=nome, quantidade=quantidade)
            for nome, quantidade in self.repository.exames_por_setor_mes()
        ]
        tendencia_7_dias = [
            ContagemDiariaOut(data=dia, quantidade=quantidade)
            for dia, quantidade in self.repository.exames_por_dia(7)
        ]

        coletas_30_dias = [
            ContagemDiariaOut(data=dia, quantidade=quantidade)
            for dia, quantidade in self.repository.exames_por_dia(30, por_data_coleta=True)
        ]
        distribuicao_status = [
            ContagemStatusOut(status=status, quantidade=quantidade)
            for status, quantidade in self.repository.distribuicao_por_status()
        ]

        alertas: list[AlertaOut] = []

        if prazo_vencido > 0:
            alertas.append(
                AlertaOut(
                    tipo="prazo",
                    mensagem=(
                        f"Existem {prazo_vencido} exame(s) com prazo de "
                        f"liberação vencido."
                    ),
                )
            )

        if aguardando_finalizacao > 0:
            alertas.append(
                AlertaOut(
                    tipo="info",
                    mensagem=(
                        f"Há {aguardando_finalizacao} exame(s) positivo(s) aguardando "
                        f"finalização."
                    ),
                )
            )

        if top_microrganismos:
            mais_frequente = top_microrganismos[0]
            alertas.append(
                AlertaOut(
                    tipo="resistencia",
                    mensagem=(
                        f"{mais_frequente.nome} foi o microrganismo mais isolado nos "
                        f"últimos 30 dias ({mais_frequente.quantidade} ocorrência(s))."
                    ),
                )
            )

        return ResumoDashboardOut(
            culturas_hoje=exames_hoje,
            aguardando_atualizacao=aguardando_atualizacao,
            prazo_vencido=prazo_vencido,
            liberados_hoje=finalizados_hoje,
            top_microrganismos=top_microrganismos,
            alertas=alertas,
            total_exames_mes=total_exames_mes,
            taxa_positividade_mes=taxa_positividade_mes,
            por_tipo_cultura=por_tipo_cultura,
            por_material=por_material,
            por_setor=por_setor,
            tendencia_7_dias=tendencia_7_dias,
            total_exames_mes_anterior=self.repository.contar_exames_mes_anterior(),
            coletas_30_dias=coletas_30_dias,
            distribuicao_status=distribuicao_status,
        )
