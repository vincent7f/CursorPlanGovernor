from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from server.config import get_db_url
from server.db.models import Base

_engine = None
_SessionLocal = None


def get_engine(db_url: str | None = None):
    global _engine
    url = db_url or get_db_url()
    if _engine is None or str(_engine.url) != url:
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)
    return _engine


def get_session_factory(db_url: str | None = None) -> sessionmaker[Session]:
    global _SessionLocal
    engine = get_engine(db_url)
    if _SessionLocal is None or _SessionLocal.kw["bind"] is not engine:
        _SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return _SessionLocal


def init_db(db_url: str | None = None) -> None:
    engine = get_engine(db_url)
    Base.metadata.create_all(engine)


def reset_engine() -> None:
    """Reset cached engine/session factory (for tests)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
