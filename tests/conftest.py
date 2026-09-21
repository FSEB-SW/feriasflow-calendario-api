"""Fixtures: banco SQLite em memoria e BrasilAPI simulada (sem rede nos testes)."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.brasilapi import ClienteBrasilAPI, get_cliente_brasilapi
from app.database import Base, get_db
from app.main import app

# Feriados nacionais de 2026 no formato bruto da BrasilAPI
BRASILAPI_2026 = [
    {"date": "2026-01-01", "name": "Confraternizacao mundial", "type": "national"},
    {"date": "2026-04-03", "name": "Sexta-feira Santa", "type": "national"},
    {"date": "2026-04-21", "name": "Tiradentes", "type": "national"},
    {"date": "2026-05-01", "name": "Dia do trabalho", "type": "national"},
    {"date": "2026-09-07", "name": "Independencia do Brasil", "type": "national"},
    {"date": "2026-10-12", "name": "Nossa Senhora Aparecida", "type": "national"},
    {"date": "2026-11-02", "name": "Finados", "type": "national"},
    {"date": "2026-11-15", "name": "Proclamacao da Republica", "type": "national"},
    {"date": "2026-11-20", "name": "Dia da consciencia negra", "type": "national"},
    {"date": "2026-12-25", "name": "Natal", "type": "national"},
]


def _transporte(fora_do_ar: bool) -> httpx.MockTransport:
    def responder(request: httpx.Request) -> httpx.Response:
        if fora_do_ar:
            return httpx.Response(503, text="indisponivel")
        ano = int(request.url.path.rsplit("/", 1)[-1])
        dados = BRASILAPI_2026 if ano == 2026 else []
        return httpx.Response(200, content=json.dumps(dados))

    return httpx.MockTransport(responder)


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)


def _montar_client(engine, fora_do_ar: bool) -> TestClient:
    sessao = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _db():
        db = sessao()
        try:
            yield db
        finally:
            db.close()

    brasilapi = ClienteBrasilAPI(
        base_url="https://brasilapi.test/api", transport=_transporte(fora_do_ar)
    )
    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_cliente_brasilapi] = lambda: brasilapi
    return TestClient(app)


@pytest.fixture()
def client(engine):
    with _montar_client(engine, fora_do_ar=False) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def client_brasilapi_fora(engine):
    with _montar_client(engine, fora_do_ar=True) as c:
        yield c
    app.dependency_overrides.clear()
