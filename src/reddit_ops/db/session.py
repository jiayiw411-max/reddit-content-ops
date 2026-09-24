from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from ..config import DATA_DIR
from .models import Base

DB_PATH = DATA_DIR / "reddit_ops.db"
# connect_args timeout 是 sqlite3 驱动等锁的时间;WAL 模式让"网页开着的同时跑
# CLI 命令"这种正常并发场景不再互相报 database is locked。
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, connect_args={"timeout": 15})


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)


def get_session() -> Session:
    return SessionLocal()
