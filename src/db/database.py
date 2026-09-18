from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from src.config import DATABASE_URL
from src.db.models import Base

# Configure SQLite connect_args if using SQLite
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Creates all database tables defined in Base and applies schema auto-migrations."""
    Base.metadata.create_all(bind=engine)

    # SQLite auto-migration for newly added columns
    with engine.connect() as conn:
        try:
            res = conn.execute(text("PRAGMA table_info(audit_log)")).fetchall()
            cols = [row[1] for row in res]
            if "metrics_json" not in cols:
                conn.execute(text("ALTER TABLE audit_log ADD COLUMN metrics_json TEXT"))
                conn.commit()
        except Exception:
            pass

        try:
            res = conn.execute(text("PRAGMA table_info(deletion_certificates)")).fetchall()
            cols = [row[1] for row in res]
            if "issuer_public_key_pem" not in cols:
                conn.execute(text("ALTER TABLE deletion_certificates ADD COLUMN issuer_public_key_pem TEXT"))
                conn.commit()
        except Exception:
            pass


def drop_db() -> None:
    """Drops all database tables."""
    Base.metadata.drop_all(bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Context manager for database sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Dependency generator for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
