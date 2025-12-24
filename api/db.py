from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite DB file lives in api/ directory
DB_PATH = Path(__file__).parent / "pkrimg.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# `check_same_thread=False` lets FastAPI use the connection across threads
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    """Create tables if they don't exist."""
    from . import models  # noqa: F401 (ensures models are imported/registered)

    Base.metadata.create_all(bind=engine)

from contextlib import contextmanager

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
