"""Observabilidade minima: estado do servico e das dependencias."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..brasilapi import ClienteBrasilAPI, get_cliente_brasilapi
from ..config import settings
from ..database import get_db
from ..schemas import HealthResposta

router = APIRouter(tags=["Operacao"])


@router.get("/health", response_model=HealthResposta, summary="Saude do servico")
def health(
    db: Session = Depends(get_db), cliente: ClienteBrasilAPI = Depends(get_cliente_brasilapi)
):
    try:
        db.execute(text("SELECT 1"))
        banco = "ok"
    except Exception:  # noqa: BLE001 - qualquer erro de banco e "erro" para o health
        banco = "erro"
    brasilapi = "ok" if cliente.disponivel() else "indisponivel"
    estado = "ok" if banco == "ok" and brasilapi == "ok" else "degradado"
    return HealthResposta(
        status=estado,
        servico="feriasflow-calendario-api",
        versao=settings.versao,
        banco=banco,
        brasilapi=brasilapi,
    )
