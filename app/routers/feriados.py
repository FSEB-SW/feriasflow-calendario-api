"""CRUD do agregado Feriado local (as 4 rotas obrigatorias da API secundaria)."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Feriado
from ..schemas import FeriadoAtualizar, FeriadoCriar, FeriadoResposta

router = APIRouter(prefix="/feriados", tags=["Feriados locais"])


def _obter(db: Session, feriado_id: int) -> Feriado:
    feriado = db.get(Feriado, feriado_id)
    if not feriado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Feriado nao encontrado")
    return feriado


def _garantir_data_livre(db: Session, data: date, ignorar_id: int | None = None) -> None:
    existente = db.scalar(select(Feriado).where(Feriado.data == data))
    if existente and existente.id != ignorar_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ja existe feriado em {data.isoformat()}: {existente.nome}",
        )


@router.get("", response_model=list[FeriadoResposta], summary="Listar feriados locais")
def listar(
    ano: int | None = Query(default=None, ge=1900, le=2200, description="Filtrar por ano"),
    db: Session = Depends(get_db),
):
    consulta = select(Feriado).order_by(Feriado.data)
    if ano is not None:
        consulta = consulta.where(
            Feriado.data >= date(ano, 1, 1), Feriado.data <= date(ano, 12, 31)
        )
    return db.scalars(consulta).all()


@router.get("/{feriado_id}", response_model=FeriadoResposta, summary="Obter um feriado")
def obter(feriado_id: int, db: Session = Depends(get_db)):
    return _obter(db, feriado_id)


@router.post(
    "",
    response_model=FeriadoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Cadastrar feriado local",
)
def criar(dados: FeriadoCriar, db: Session = Depends(get_db)):
    _garantir_data_livre(db, dados.data)
    feriado = Feriado(data=dados.data, nome=dados.nome, tipo=dados.tipo.value)
    db.add(feriado)
    db.commit()
    db.refresh(feriado)
    return feriado


@router.put("/{feriado_id}", response_model=FeriadoResposta, summary="Atualizar feriado local")
def atualizar(feriado_id: int, dados: FeriadoAtualizar, db: Session = Depends(get_db)):
    feriado = _obter(db, feriado_id)
    alteracoes = dados.model_dump(exclude_unset=True)
    if not alteracoes:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Nenhum campo informado")
    if "data" in alteracoes:
        _garantir_data_livre(db, alteracoes["data"], ignorar_id=feriado.id)
    for campo, valor in alteracoes.items():
        setattr(feriado, campo, valor.value if hasattr(valor, "value") else valor)
    db.commit()
    db.refresh(feriado)
    return feriado


@router.delete(
    "/{feriado_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover feriado local"
)
def remover(feriado_id: int, db: Session = Depends(get_db)):
    feriado = _obter(db, feriado_id)
    db.delete(feriado)
    db.commit()
