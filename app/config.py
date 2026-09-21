"""Configuracao por variaveis de ambiente (12-factor: config fora do codigo)."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/calendario.db")
    brasilapi_url: str = os.getenv("BRASILAPI_URL", "https://brasilapi.com.br/api")
    brasilapi_timeout: float = float(os.getenv("BRASILAPI_TIMEOUT", "5"))
    brasilapi_cache_ttl: int = int(os.getenv("BRASILAPI_CACHE_TTL", "86400"))
    brasilapi_falhas_para_abrir: int = int(os.getenv("BRASILAPI_FALHAS_PARA_ABRIR", "3"))
    brasilapi_tempo_aberto: int = int(os.getenv("BRASILAPI_TEMPO_ABERTO", "60"))
    versao: str = "1.0.0"


settings = Settings()
