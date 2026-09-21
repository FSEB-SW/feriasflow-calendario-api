"""Engine e sessao SQLAlchemy. Banco proprio do servico (SQLite por padrao)."""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

_url = settings.database_url
if _url.startswith("sqlite:///") and ":memory:" not in _url:
    _caminho = _url.replace("sqlite:///", "", 1)
    os.makedirs(os.path.dirname(_caminho) or ".", exist_ok=True)

engine = create_engine(
    _url,
    connect_args={"check_same_thread": False} if _url.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependencia FastAPI: uma sessao por requisicao."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
