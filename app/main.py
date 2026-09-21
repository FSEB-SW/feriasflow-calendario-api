"""FeriasFlow - Calendario API.

Servico secundario do MVP da Sprint 3 (Arquitetura de Software) da pos-graduacao em
Engenharia de Software da PUC-Rio. Responsabilidade unica: calendario de trabalho
(feriados locais + feriados nacionais da BrasilAPI + contagem de dias uteis).
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from .config import settings
from .database import Base, engine
from .routers import calendario, feriados, health

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="FeriasFlow - Calendario API",
    version=settings.versao,
    description=(
        "Servico de calendario do FeriasFlow: cadastro de feriados locais, consulta de "
        "feriados nacionais (BrasilAPI) e contagem de dias uteis de um periodo.\n\n"
        "MVP - Sprint Arquitetura de Software - Pos-graduacao em Engenharia de Software, PUC-Rio."
    ),
    lifespan=lifespan,
)

app.include_router(feriados.router)
app.include_router(calendario.router)
app.include_router(health.router)


@app.get("/", include_in_schema=False)
def raiz():
    return RedirectResponse(url="/docs")
