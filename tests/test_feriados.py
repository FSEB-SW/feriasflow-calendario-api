"""CRUD de feriados locais."""

NOVO = {"data": "2026-09-08", "nome": "Aniversario de Curitiba", "tipo": "municipal"}


def test_criar_e_obter(client):
    r = client.post("/feriados", json=NOVO)
    assert r.status_code == 201
    corpo = r.json()
    assert corpo["id"] == 1
    assert corpo["data"] == "2026-09-08"
    assert corpo["tipo"] == "municipal"

    r = client.get("/feriados/1")
    assert r.status_code == 200
    assert r.json()["nome"] == "Aniversario de Curitiba"


def test_listar_com_filtro_por_ano(client):
    client.post("/feriados", json=NOVO)
    client.post("/feriados", json={"data": "2027-09-08", "nome": "Aniversario de Curitiba"})

    assert len(client.get("/feriados").json()) == 2
    assert len(client.get("/feriados", params={"ano": 2026}).json()) == 1
    assert client.get("/feriados", params={"ano": 2030}).json() == []


def test_data_duplicada_retorna_409(client):
    assert client.post("/feriados", json=NOVO).status_code == 201
    r = client.post("/feriados", json={**NOVO, "nome": "Outro nome"})
    assert r.status_code == 409
    assert "2026-09-08" in r.json()["detail"]


def test_validacao_de_entrada_422(client):
    assert client.post("/feriados", json={"data": "08/09/2026", "nome": "X"}).status_code == 422
    assert client.post("/feriados", json={"data": "2026-09-08", "nome": "A"}).status_code == 422
    assert (
        client.post("/feriados", json={**NOVO, "tipo": "nacional"}).status_code == 422
    ), "tipo nacional nao e cadastravel: vem da BrasilAPI"


def test_atualizar_parcial(client):
    client.post("/feriados", json=NOVO)
    r = client.put("/feriados/1", json={"tipo": "empresa"})
    assert r.status_code == 200
    assert r.json() == {**NOVO, "id": 1, "tipo": "empresa"}

    assert client.put("/feriados/1", json={}).status_code == 422
    assert client.put("/feriados/99", json={"nome": "Nada"}).status_code == 404


def test_atualizar_para_data_ocupada_409(client):
    client.post("/feriados", json=NOVO)
    client.post("/feriados", json={"data": "2026-12-08", "nome": "Padroeira"})
    assert client.put("/feriados/2", json={"data": "2026-09-08"}).status_code == 409


def test_remover(client):
    client.post("/feriados", json=NOVO)
    assert client.delete("/feriados/1").status_code == 204
    assert client.get("/feriados/1").status_code == 404
    assert client.delete("/feriados/1").status_code == 404
