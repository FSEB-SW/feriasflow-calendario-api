"""Contratos de entrada e saida (Pydantic). O que entra e validado; o que sai e documentado."""
from datetime import date
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TipoFeriado(str, Enum):
    municipal = "municipal"
    estadual = "estadual"
    empresa = "empresa"


class FeriadoBase(BaseModel):
    data: date = Field(description="Data do feriado (AAAA-MM-DD)", examples=["2026-09-08"])
    nome: str = Field(min_length=2, max_length=120, examples=["Aniversario de Curitiba"])
    tipo: TipoFeriado = Field(default=TipoFeriado.municipal)


class FeriadoCriar(FeriadoBase):
    pass


class FeriadoAtualizar(BaseModel):
    data: date | None = None
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    tipo: TipoFeriado | None = None


class FeriadoResposta(FeriadoBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class FeriadoNacional(BaseModel):
    data: date
    nome: str
    tipo: Literal["nacional"] = "nacional"


class FeriadosNacionaisResposta(BaseModel):
    ano: int
    fonte: Literal["brasilapi", "cache", "indisponivel"]
    feriados: list[FeriadoNacional]


class FeriadoNoPeriodo(BaseModel):
    data: date
    nome: str
    origem: Literal["nacional", "municipal", "estadual", "empresa"]


class DiasUteisResposta(BaseModel):
    inicio: date
    fim: date
    dias_corridos: int
    dias_uteis: int
    fins_de_semana: int
    feriados: list[FeriadoNoPeriodo]
    fonte_nacional: Literal["brasilapi", "cache", "indisponivel"]
    aviso: str | None = None


class HealthResposta(BaseModel):
    status: Literal["ok", "degradado"]
    servico: str
    versao: str
    banco: Literal["ok", "erro"]
    brasilapi: Literal["ok", "indisponivel"]
