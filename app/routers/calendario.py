"""Rotas de consulta: dias uteis (consolidado) e feriados nacionais (repasse da BrasilAPI)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..brasilapi import ClienteBrasilAPI, get_cliente_brasilapi
from ..database import get_db
from ..schemas import DiasUteisResposta, FeriadoNacional, FeriadosNacionaisResposta
from ..services import PERIODO_MAXIMO_DIAS, calcular_dias_uteis

router = APIRouter(tags=["Calendario"])


@router.get(
    "/dias-uteis",
    response_model=DiasUteisResposta,
    summary="Contar dias uteis de um periodo",
    description=(
        "Consolida fins de semana, feriados nacionais (BrasilAPI) e feriados locais "
        "(banco proprio). Se a BrasilAPI estiver fora, responde 200 com `fonte_nacional` = "
        "`indisponivel` e um `aviso` (degradacao controlada, nao falha)."
    ),
)
def dias_uteis(
    inicio: date = Query(description="Primeiro dia do periodo (AAAA-MM-DD)"),
    fim: date = Query(description="Ultimo dia do periodo (AAAA-MM-DD)"),
    db: Session = Depends(get_db),
    cliente: ClienteBrasilAPI = Depends(get_cliente_brasilapi),
):
    if fim < inicio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "fim deve ser >= inicio")
    if (fim - inicio).days + 1 > PERIODO_MAXIMO_DIAS:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"periodo maximo de {PERIODO_MAXIMO_DIAS} dias",
        )
    return calcular_dias_uteis(db, cliente, inicio, fim)


@router.get(
    "/feriados-nacionais/{ano}",
    response_model=FeriadosNacionaisResposta,
    summary="Feriados nacionais do ano (via BrasilAPI)",
)
def feriados_nacionais(ano: int, cliente: ClienteBrasilAPI = Depends(get_cliente_brasilapi)):
    if not 1900 <= ano <= 2200:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "ano fora da faixa")
    lista, fonte = cliente.feriados(ano)
    return FeriadosNacionaisResposta(
        ano=ano,
        fonte=fonte,
        feriados=[FeriadoNacional(data=i["data"], nome=i["nome"]) for i in lista],
    )
