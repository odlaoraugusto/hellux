"""
Helpers compartilhados entre os testes do fluxo de Exame unificado
(Fase 1) - evita duplicar "cria paciente/material/tipo de cultura/etc.
ou reaproveita se já existir" em test_exames.py, test_ccih.py,
test_dashboard.py e test_relatorios.py.
"""


def _criar_ou_reaproveitar(client, endpoint: str, nome: str, payload: dict | None = None):
    resposta = client.post(endpoint, json=payload or {"nome": nome})
    if resposta.status_code == 201:
        return resposta.json()["data"]

    itens = client.get(endpoint).json()["data"]["items"]
    return next(i for i in itens if i["nome"] == nome)


def criar_paciente(client, prontuario="p1", nome="Paciente Teste"):
    resposta = client.post("/api/pacientes", json={"nome": nome, "prontuario": prontuario})
    return resposta.json()["data"]


def criar_material(client, nome="Hemocultura"):
    return _criar_ou_reaproveitar(client, "/api/materiais", nome)


def criar_setor(client, nome="UTI"):
    return _criar_ou_reaproveitar(client, "/api/setores", nome)


def criar_tipo_cultura(client, nome="Cultura Geral"):
    return _criar_ou_reaproveitar(client, "/api/tipos-cultura", nome)


def criar_microrganismo(client, nome="Klebsiella pneumoniae", **extra):
    payload = {"nome": nome, **extra}
    resposta = client.post("/api/microrganismos", json=payload)
    if resposta.status_code == 201:
        return resposta.json()["data"]
    itens = client.get("/api/microrganismos", params={"termo": nome}).json()["data"]["items"]
    return next(m for m in itens if m["nome"] == nome)


def criar_antimicrobiano(client, nome="Meropenem", **extra):
    payload = {"nome": nome, **extra}
    resposta = client.post("/api/antimicrobianos", json=payload)
    if resposta.status_code == 201:
        return resposta.json()["data"]
    itens = client.get("/api/antimicrobianos", params={"termo": nome}).json()["data"]["items"]
    return next(a for a in itens if a["nome"] == nome)


def criar_exame(client, prontuario="p1", nome="Paciente Teste", **extra):
    material = criar_material(client)
    tipo_cultura = criar_tipo_cultura(client)
    payload = {
        "paciente_prontuario": prontuario,
        "paciente_nome": nome,
        "material_id": material["id"],
        "tipo_cultura_id": tipo_cultura["id"],
        **extra,
    }
    return client.post("/api/exames", json=payload)
