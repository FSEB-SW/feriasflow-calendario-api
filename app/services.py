"""Regra de negocio do servico: consolidar feriados e contar dias uteis."""
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .brasilapi import ClienteBrasilAPI
from .models import Feriado
from .schemas import DiasUteisResposta, FeriadoNoPeriodo

PERIODO_MAXIMO_DIAS = 366


def calcular_dias_uteis(
    db: Session, cliente: ClienteBrasilAPI, inicio: date, fim: date
) -> DiasUteisResposta:
    feriados: dict[date, FeriadoNoPeriodo] = {}

    # 1) nacionais (fonte externa), ano a ano
    fontes: list[str] = []
    for ano in range(inicio.year, fim.year + 1):
        lista, fonte = cliente.feriados(ano)
        fontes.append(fonte)
        for item in lista:
            if inicio <= item["data"] <= fim:
                feriados[item["data"]] = FeriadoNoPeriodo(
                    data=item["data"], nome=item["nome"], origem="nacional"
                )

    # 2) locais (banco proprio) - nao sobrescrevem um nacional na mesma data
    locais = db.scalars(
        select(Feriado).where(Feriado.data >= inicio, Feriado.data <= fim)
    ).all()
    for f in locais:
        feriados.setdefault(
            f.data, FeriadoNoPeriodo(data=f.data, nome=f.nome, origem=f.tipo)
        )

    # 3) contagem
    dias_corridos = (fim - inicio).days + 1
    fins_de_semana = 0
    dias_uteis = 0
    dia = inicio
    while dia <= fim:
        if dia.weekday() >= 5:
            fins_de_semana += 1
        elif dia not in feriados:
            dias_uteis += 1
        dia += timedelta(days=1)

    if "indisponivel" in fontes:
        fonte_nacional = "indisponivel"
        aviso = (
            "BrasilAPI indisponivel: feriados nacionais NAO foram considerados; "
            "contagem feita apenas com feriados locais."
        )
    elif "brasilapi" in fontes:
        fonte_nacional, aviso = "brasilapi", None
    else:
        fonte_nacional, aviso = "cache", None

    return DiasUteisResposta(
        inicio=inicio,
        fim=fim,
        dias_corridos=dias_corridos,
        dias_uteis=dias_uteis,
        fins_de_semana=fins_de_semana,
        feriados=sorted(feriados.values(), key=lambda f: f.data),
        fonte_nacional=fonte_nacional,
        aviso=aviso,
    )
