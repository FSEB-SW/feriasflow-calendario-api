"""Modelo persistido: o agregado deste servico e o Feriado local."""
from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _agora() -> datetime:
    return datetime.now(timezone.utc)


class Feriado(Base):
    __tablename__ = "feriados"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), nullable=False, default="municipal")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=_agora, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime, default=_agora, onupdate=_agora, nullable=False
    )
