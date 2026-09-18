"""
Testes do endpoint `/api/ccih/matriz-sensibilidade` (Fase 1.5).

Endpoint aditivo - agrupa antibiograma por (macro_grupo do setor,
grupo_fenotipico do microrganismo, antimicrobiano), com os três
percentuais S/I/R. Ver app/repositories/ccih_repository.py e
app/services/ccih_service.py.
"""
from tests.helpers import criar_antimicrobiano, criar_exame, criar_microrganismo, criar_setor


def _item_por_chave(itens, macro_grupo, grupo_fenotipico, antimicrobiano):
    return next(
        i
        for i in itens
        if i["macro_grupo"] == macro_grupo
        and i["grupo_fenotipico"] == grupo_fenotipico
        and i["antimicrobiano"] == antimicrobiano
    )


def test_matriz_estrutura_basica(authenticated_client):
    response = authenticated_client.get("/api/ccih/matriz-sensibilidade")
    assert response.status_code == 200
    body = response.json()["data"]
    for campo in ("periodo_inicio", "periodo_fim", "itens"):
        assert campo in body


def test_matriz_agrupa_por_macro_setor_fenotipo_e_calcula_percentuais_sir(authenticated_client):
    """
    2 macro-setores x 2 famílias fenotípicas, com resultado S/I/R
    misto num dos grupos - confere que a matriz agrupa certo e calcula
    os TRÊS percentuais (o indicador antigo `taxa_resistencia` só tinha
    S/R).
    """
    setor_uti = criar_setor(authenticated_client, "UTI Adulto", macro_grupo="UTI")
    setor_enf = criar_setor(authenticated_client, "Enfermaria Clínica", macro_grupo="Enfermaria")

    aureus = criar_microrganismo(
        authenticated_client, "Staphylococcus aureus", grupo_fenotipico="S_AUREUS"
    )
    ecoli = criar_microrganismo(
        authenticated_client, "Escherichia coli", grupo_fenotipico="BGN_F"
    )

    oxacilina = criar_antimicrobiano(authenticated_client, "Oxacilina")
    meropenem = criar_antimicrobiano(authenticated_client, "Meropenem")

    # UTI / S_AUREUS / Oxacilina: 1 sensível, 1 intermediário, 1 resistente.
    for i, resultado in enumerate(("SENSIVEL", "INTERMEDIARIO", "RESISTENTE")):
        criar_exame(
            authenticated_client,
            prontuario=f"matriz-uti-{i}",
            setor_id=setor_uti["id"],
            status="POSITIVO",
            isolados=[
                {
                    "microrganismo_id": aureus["id"],
                    "antibiograma": [
                        {"antimicrobiano_id": oxacilina["id"], "resultado": resultado}
                    ],
                }
            ],
        )

    # Enfermaria / BGN_F / Meropenem: 2 sensíveis.
    for i in range(2):
        criar_exame(
            authenticated_client,
            prontuario=f"matriz-enf-{i}",
            setor_id=setor_enf["id"],
            status="POSITIVO",
            isolados=[
                {
                    "microrganismo_id": ecoli["id"],
                    "antibiograma": [
                        {"antimicrobiano_id": meropenem["id"], "resultado": "SENSIVEL"}
                    ],
                }
            ],
        )

    body = authenticated_client.get("/api/ccih/matriz-sensibilidade").json()["data"]
    itens = body["itens"]

    item_uti = _item_por_chave(itens, "UTI", "S_AUREUS", "Oxacilina")
    assert item_uti["total_testado"] == 3
    assert item_uti["sensivel"] == 1
    assert item_uti["intermediario"] == 1
    assert item_uti["resistente"] == 1
    assert item_uti["percentual_sensivel"] == 33.3
    assert item_uti["percentual_intermediario"] == 33.3
    assert item_uti["percentual_resistente"] == 33.3

    item_enf = _item_por_chave(itens, "Enfermaria", "BGN_F", "Meropenem")
    assert item_enf["total_testado"] == 2
    assert item_enf["sensivel"] == 2
    assert item_enf["percentual_sensivel"] == 100.0
    assert item_enf["intermediario"] == 0
    assert item_enf["resistente"] == 0


def test_matriz_setor_sem_macro_grupo_cai_em_nao_classificado(authenticated_client):
    setor = criar_setor(authenticated_client, "Setor Sem Classificação")
    microrganismo = criar_microrganismo(
        authenticated_client, "Candida albicans matriz", grupo_fenotipico="LEVEDURAS"
    )
    antimicrobiano = criar_antimicrobiano(authenticated_client, "Fluconazol matriz")

    criar_exame(
        authenticated_client,
        prontuario="matriz-sem-macro",
        setor_id=setor["id"],
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": microrganismo["id"],
                "antibiograma": [
                    {"antimicrobiano_id": antimicrobiano["id"], "resultado": "SENSIVEL"}
                ],
            }
        ],
    )

    body = authenticated_client.get("/api/ccih/matriz-sensibilidade").json()["data"]
    item = _item_por_chave(body["itens"], "Não classificado", "LEVEDURAS", "Fluconazol matriz")
    assert item["total_testado"] == 1


def test_matriz_exclui_isolado_com_dispensa_tecnica_do_antibiograma(authenticated_client):
    """
    `ExameIsolado.nao_realizado_tecnico=True` dispensa aquele isolado
    específico da exigência de antibiograma - mesmo que (indevidamente)
    exista um resultado lançado para ele, a matriz precisa ignorá-lo.
    """
    setor = criar_setor(authenticated_client, "UTI Neonatal", macro_grupo="UTI")
    aureus = criar_microrganismo(
        authenticated_client, "Staphylococcus aureus dispensa", grupo_fenotipico="S_AUREUS"
    )
    oxacilina = criar_antimicrobiano(authenticated_client, "Oxacilina dispensa")

    # Isolado normal, entra na contagem.
    criar_exame(
        authenticated_client,
        prontuario="dispensa-1",
        setor_id=setor["id"],
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": aureus["id"],
                "antibiograma": [
                    {"antimicrobiano_id": oxacilina["id"], "resultado": "SENSIVEL"}
                ],
            }
        ],
    )
    # Isolado dispensado tecnicamente - precisa ser excluído mesmo tendo
    # um resultado de antibiograma associado.
    criar_exame(
        authenticated_client,
        prontuario="dispensa-2",
        setor_id=setor["id"],
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": aureus["id"],
                "nao_realizado_tecnico": True,
                "motivo_dispensa_tsa": "Sem protocolo BrCAST padronizado para esta espécie.",
                "antibiograma": [
                    {"antimicrobiano_id": oxacilina["id"], "resultado": "RESISTENTE"}
                ],
            }
        ],
    )

    body = authenticated_client.get("/api/ccih/matriz-sensibilidade").json()["data"]
    item = _item_por_chave(body["itens"], "UTI", "S_AUREUS", "Oxacilina dispensa")
    assert item["total_testado"] == 1
    assert item["sensivel"] == 1
    assert item["resistente"] == 0
