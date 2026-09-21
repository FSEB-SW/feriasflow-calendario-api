"""Cliente da API externa (BrasilAPI) com cache por ano e disjuntor simples.

BrasilAPI: https://brasilapi.com.br/docs#tag/Feriados-Nacionais
GET /feriados/v1/{ano} -> [{"date": "2026-01-01", "name": "...", "type": "national"}]
Publica, gratuita, sem cadastro.

Resiliencia (D2 - Sam Newman): timeout curto, cache que continua servindo depois de vencido
se a fonte cair, e disjuntor que para de bater na API por um tempo apos N falhas seguidas.
"""
import logging
import time
from datetime import date

import httpx

from .config import settings

log = logging.getLogger("calendario.brasilapi")

Fonte = str  # "brasilapi" | "cache" | "indisponivel"


class ClienteBrasilAPI:
    def __init__(
        self,
        base_url: str = settings.brasilapi_url,
        timeout: float = settings.brasilapi_timeout,
        cache_ttl: int = settings.brasilapi_cache_ttl,
        falhas_para_abrir: int = settings.brasilapi_falhas_para_abrir,
        tempo_aberto: int = settings.brasilapi_tempo_aberto,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self.falhas_para_abrir = falhas_para_abrir
        self.tempo_aberto = tempo_aberto
        self._http = httpx.Client(timeout=timeout, transport=transport)
        self._cache: dict[int, tuple[float, list[dict]]] = {}
        self._falhas = 0
        self._aberto_ate = 0.0

    @property
    def circuito_aberto(self) -> bool:
        return time.monotonic() < self._aberto_ate

    def feriados(self, ano: int) -> tuple[list[dict], Fonte]:
        """Retorna (lista normalizada, fonte). Nunca levanta excecao: degrada com aviso."""
        agora = time.monotonic()
        em_cache = self._cache.get(ano)
        if em_cache and agora - em_cache[0] < self.cache_ttl:
            return em_cache[1], "cache"

        if self.circuito_aberto:
            log.warning("circuito aberto; BrasilAPI nao consultada para %s", ano)
            return (em_cache[1], "cache") if em_cache else ([], "indisponivel")

        try:
            resposta = self._http.get(f"{self.base_url}/feriados/v1/{ano}")
            resposta.raise_for_status()
            dados = self._normalizar(resposta.json())
        except (httpx.HTTPError, ValueError) as exc:
            self._registrar_falha()
            log.error("falha na BrasilAPI (%s): %s", ano, exc)
            return (em_cache[1], "cache") if em_cache else ([], "indisponivel")

        self._falhas = 0
        self._cache[ano] = (agora, dados)
        return dados, "brasilapi"

    def disponivel(self) -> bool:
        """Sonda leve para o /health: consulta o ano corrente sem alterar o disjuntor."""
        try:
            resposta = self._http.get(
                f"{self.base_url}/feriados/v1/{date.today().year}", timeout=3
            )
            return resposta.status_code == 200
        except httpx.HTTPError:
            return False

    def _registrar_falha(self) -> None:
        self._falhas += 1
        if self._falhas >= self.falhas_para_abrir:
            self._aberto_ate = time.monotonic() + self.tempo_aberto
            self._falhas = 0
            log.warning("disjuntor aberto por %ss", self.tempo_aberto)

    @staticmethod
    def _normalizar(bruto: list[dict]) -> list[dict]:
        return [
            {"data": date.fromisoformat(item["date"]), "nome": item["name"]}
            for item in bruto
            if "date" in item and "name" in item
        ]


cliente = ClienteBrasilAPI()


def get_cliente_brasilapi() -> ClienteBrasilAPI:
    """Dependencia FastAPI (permite substituir o cliente nos testes)."""
    return cliente
