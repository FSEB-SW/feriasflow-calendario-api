"""Contagem de dias uteis: fins de semana + nacionais (BrasilAPI) + locais, com degradacao."""


def test_semana_com_feriado_nacional(client):
    # 20/04/2026 (seg) a 24/04/2026 (sex); 21/04 = Tiradentes
    r = client.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["dias_corridos"] == 5
    assert corpo["fins_de_semana"] == 0
    assert corpo["dias_uteis"] == 4
    assert corpo["fonte_nacional"] == "brasilapi"
    assert corpo["aviso"] is None
    assert corpo["feriados"] == [
        {"data": "2026-04-21", "nome": "Tiradentes", "origem": "nacional"}
    ]


def test_feriado_local_entra_na_conta(client):
    client.post("/feriados", json={"data": "2026-04-22", "nome": "Ponto facultativo", "tipo": "empresa"})
    r = client.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"})
    corpo = r.json()
    assert corpo["dias_uteis"] == 3
    assert [f["origem"] for f in corpo["feriados"]] == ["nacional", "empresa"]


def test_nacional_prevalece_sobre_local_na_mesma_data(client):
    client.post("/feriados", json={"data": "2026-04-21", "nome": "Duplicado local"})
    corpo = client.get("/dias-uteis", params={"inicio": "2026-04-21", "fim": "2026-04-21"}).json()
    assert corpo["dias_uteis"] == 0
    assert corpo["feriados"][0]["origem"] == "nacional"


def test_fins_de_semana_e_virada_de_ano(client):
    # 28/12/2026 (seg) a 03/01/2027 (dom): 7 corridos, 2 fds, 01/01 sexta feriado -> 4 uteis
    corpo = client.get("/dias-uteis", params={"inicio": "2026-12-28", "fim": "2027-01-03"}).json()
    assert corpo["dias_corridos"] == 7
    assert corpo["fins_de_semana"] == 2
    # 2027 nao esta na simulacao (lista vazia = 200 sem feriados), entao 01/01/2027 conta como util
    assert corpo["dias_uteis"] == 5


def test_segunda_chamada_vem_do_cache(client):
    client.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"})
    corpo = client.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"}).json()
    assert corpo["fonte_nacional"] == "cache"
    assert corpo["dias_uteis"] == 4


def test_brasilapi_fora_degrada_sem_falhar(client_brasilapi_fora):
    c = client_brasilapi_fora
    c.post("/feriados", json={"data": "2026-04-22", "nome": "Ponto facultativo", "tipo": "empresa"})
    r = c.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"})
    assert r.status_code == 200
    corpo = r.json()
    assert corpo["fonte_nacional"] == "indisponivel"
    assert "BrasilAPI indisponivel" in corpo["aviso"]
    assert corpo["dias_uteis"] == 4, "so o feriado local foi descontado"


def test_disjuntor_abre_apos_falhas(client_brasilapi_fora):
    c = client_brasilapi_fora
    for _ in range(3):
        c.get("/feriados-nacionais/2026")
    from app.brasilapi import get_cliente_brasilapi
    from app.main import app

    cliente = app.dependency_overrides[get_cliente_brasilapi]()
    assert cliente.circuito_aberto is True


def test_periodo_invalido_422(client):
    assert client.get("/dias-uteis", params={"inicio": "2026-04-24", "fim": "2026-04-20"}).status_code == 422
    assert client.get("/dias-uteis", params={"inicio": "2026-01-01", "fim": "2027-12-31"}).status_code == 422
    assert client.get("/dias-uteis", params={"inicio": "2026-01-01"}).status_code == 422


def test_feriados_nacionais_repassa_brasilapi(client):
    corpo = client.get("/feriados-nacionais/2026").json()
    assert corpo["fonte"] == "brasilapi"
    assert len(corpo["feriados"]) == 10
    assert corpo["feriados"][0] == {"data": "2026-01-01", "nome": "Confraternizacao mundial", "tipo": "nacional"}


def test_health_ok(client):
    corpo = client.get("/health").json()
    assert corpo["status"] == "ok"
    assert corpo["servico"] == "feriasflow-calendario-api"


def test_health_degradado(client_brasilapi_fora):
    corpo = client_brasilapi_fora.get("/health").json()
    assert corpo["status"] == "degradado"
    assert corpo["banco"] == "ok"
    assert corpo["brasilapi"] == "indisponivel"
