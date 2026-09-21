"""Teste de contrato (lado do PRODUTOR).

O consumidor (feriasflow-api) descreve em `contratos/dias-uteis.schema.json` o que espera de
GET /dias-uteis. Aqui o produtor prova que a resposta real respeita esse contrato, inclusive
no modo degradado. Se alguem mudar o formato da resposta, este teste quebra ANTES de o
consumidor descobrir em producao (D2 - testes de contrato; D3 - feedback rapido).
"""
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

CONTRATO = json.loads(
    (Path(__file__).resolve().parents[1] / "contratos" / "dias-uteis.schema.json").read_text("utf-8")
)
validador = Draft202012Validator(CONTRATO, format_checker=FormatChecker())


def test_resposta_normal_respeita_o_contrato(client):
    client.post("/feriados", json={"data": "2026-04-22", "nome": "Ponto facultativo", "tipo": "empresa"})
    corpo = client.get("/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"}).json()
    erros = sorted(validador.iter_errors(corpo), key=lambda e: e.path)
    assert not erros, [e.message for e in erros]


def test_resposta_degradada_respeita_o_contrato(client_brasilapi_fora):
    corpo = client_brasilapi_fora.get(
        "/dias-uteis", params={"inicio": "2026-04-20", "fim": "2026-04-24"}
    ).json()
    erros = sorted(validador.iter_errors(corpo), key=lambda e: e.path)
    assert not erros, [e.message for e in erros]
