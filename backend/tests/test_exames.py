"""
Testes do fluxo de Exame unificado (Fase 1).

`Exame` é agora a entidade "dona" de todo o fluxo (resolve o paciente
por prontuário, cria se não existir, e grava pedido + resultado +
isolados + antibiograma numa única chamada) - substitui os antigos
módulos Solicitações/Microbiologia/Antibiogramas (removidos nesta
mesma fase, ver alembic/versions/0014_multi_tenant_exame.py).
"""
from tests.helpers import criar_antimicrobiano, criar_exame, criar_microrganismo, criar_paciente


def test_criar_exame_com_sucesso(authenticated_client):
    response = criar_exame(authenticated_client)

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "AGUARDANDO_TRIAGEM"
    assert body["data_coleta"] is not None
    assert body["material"]["nome"] == "Hemocultura"
    assert body["paciente"]["prontuario"] == "p1"


def test_criar_exame_cria_paciente_automaticamente_por_prontuario(authenticated_client):
    response = criar_exame(authenticated_client, prontuario="novo-123", nome="Fulano de Tal")

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["paciente"]["prontuario"] == "novo-123"
    assert body["paciente"]["nome"] == "Fulano de Tal"

    listagem = authenticated_client.get("/api/pacientes?termo=novo-123").json()["data"]
    assert listagem["total"] == 1


def test_criar_exame_reaproveita_paciente_existente_sem_sobrescrever_nome(authenticated_client):
    paciente = criar_paciente(authenticated_client, prontuario="p-existente", nome="Nome Original")

    response = criar_exame(
        authenticated_client, prontuario="p-existente", nome="Nome Digitado Errado"
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["paciente"]["id"] == paciente["id"]
    assert body["paciente"]["nome"] == "Nome Original"

    listagem = authenticated_client.get("/api/pacientes?termo=p-existente").json()["data"]
    assert listagem["total"] == 1


def test_nao_permite_exame_sem_prontuario(authenticated_client):
    from tests.helpers import criar_material, criar_tipo_cultura

    material = criar_material(authenticated_client)
    tipo_cultura = criar_tipo_cultura(authenticated_client)

    response = authenticated_client.post(
        "/api/exames",
        json={
            "paciente_nome": "Fulano",
            "material_id": material["id"],
            "tipo_cultura_id": tipo_cultura["id"],
        },
    )

    assert response.status_code == 422


def test_criar_exame_positivo_com_isolado(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client, nome="Klebsiella pneumoniae")

    response = criar_exame(
        authenticated_client,
        status="POSITIVO_PARCIAL",
        isolados=[{"microrganismo_id": microrganismo["id"]}],
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["status"] == "POSITIVO_PARCIAL"
    assert len(body["isolados"]) == 1
    assert body["isolados"][0]["microrganismo"]["nome"] == "Klebsiella pneumoniae"
    assert body["isolados"][0]["mecanismo_resistencia"] == "NENHUM"


def test_nao_permite_isolado_em_exame_nao_positivo(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client)

    response = criar_exame(
        authenticated_client,
        status="NEGATIVO",
        isolados=[{"microrganismo_id": microrganismo["id"]}],
    )

    assert response.status_code == 422


def test_isolado_com_mecanismo_de_resistencia_e_antibiograma(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client, nome="Staphylococcus aureus")
    antimicrobiano = criar_antimicrobiano(authenticated_client, nome="Oxacilina")

    response = criar_exame(
        authenticated_client,
        status="POSITIVO",
        isolados=[
            {
                "microrganismo_id": microrganismo["id"],
                "mecanismo_resistencia": "MRSA",
                "antibiograma": [
                    {"antimicrobiano_id": antimicrobiano["id"], "resultado": "RESISTENTE"}
                ],
            }
        ],
    )

    assert response.status_code == 201
    isolado = response.json()["data"]["isolados"][0]
    assert isolado["mecanismo_resistencia"] == "MRSA"
    assert isolado["antibiograma"][0]["resultado"] == "RESISTENTE"
    assert isolado["antibiograma"][0]["antimicrobiano"]["nome"] == "Oxacilina"


def test_isolado_nao_realizado_tecnico_exige_motivo(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client)

    response = criar_exame(
        authenticated_client,
        status="POSITIVO_PARCIAL",
        isolados=[{"microrganismo_id": microrganismo["id"], "nao_realizado_tecnico": True}],
    )

    assert response.status_code == 422


def test_isolado_nao_realizado_tecnico_com_motivo(authenticated_client):
    microrganismo = criar_microrganismo(authenticated_client)

    response = criar_exame(
        authenticated_client,
        status="POSITIVO_PARCIAL",
        isolados=[
            {
                "microrganismo_id": microrganismo["id"],
                "nao_realizado_tecnico": True,
                "motivo_dispensa_tsa": "Sem protocolo BrCAST para este microrganismo.",
            }
        ],
    )

    assert response.status_code == 201
    isolado = response.json()["data"]["isolados"][0]
    assert isolado["nao_realizado_tecnico"] is True
    assert isolado["motivo_dispensa_tsa"]


def test_listar_exames(authenticated_client):
    criar_exame(authenticated_client, prontuario="l1")
    criar_exame(authenticated_client, prontuario="l2")

    response = authenticated_client.get("/api/exames")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] == 2
    assert len(body["items"]) == 2


def test_listar_exames_filtra_por_status(authenticated_client):
    criar_exame(authenticated_client, prontuario="f1", status="NEGATIVO")
    criar_exame(authenticated_client, prontuario="f2")

    response = authenticated_client.get("/api/exames", params={"status": "NEGATIVO"})

    body = response.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["status"] == "NEGATIVO"


def test_listar_exames_filtra_por_multiplos_status(authenticated_client):
    criar_exame(authenticated_client, prontuario="m1", status="NEGATIVO")
    criar_exame(authenticated_client, prontuario="m2", status="POSITIVO")
    criar_exame(authenticated_client, prontuario="m3")  # AGUARDANDO_TRIAGEM

    response = authenticated_client.get(
        "/api/exames", params=[("status", "NEGATIVO"), ("status", "POSITIVO")]
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] == 2
    status_retornados = {item["status"] for item in body["items"]}
    assert status_retornados == {"NEGATIVO", "POSITIVO"}


def test_obter_exame_especifico(authenticated_client):
    criado = criar_exame(authenticated_client).json()["data"]

    response = authenticated_client.get(f"/api/exames/{criado['id']}")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == criado["id"]


def test_atualizar_exame_status(authenticated_client):
    criado = criar_exame(authenticated_client).json()["data"]

    response = authenticated_client.put(
        f"/api/exames/{criado['id']}", json={"status": "NEGATIVO"}
    )

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "NEGATIVO"


def test_remover_exame(authenticated_client):
    criado = criar_exame(authenticated_client).json()["data"]

    delete_response = authenticated_client.delete(f"/api/exames/{criado['id']}")
    get_response = authenticated_client.get(f"/api/exames/{criado['id']}")

    assert delete_response.status_code == 200
    assert get_response.status_code == 404
