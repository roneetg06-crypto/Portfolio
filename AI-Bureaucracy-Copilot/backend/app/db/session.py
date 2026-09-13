import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

try:
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=False,
    )
except Exception as exc:
    logger.error(f"[DATABASE] Error initializing SQLAlchemy engine: {exc}")
    engine = None

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) if engine else None


def get_db() -> Generator[Session, None, None]:
    """Dependency that provides an active SQLAlchemy database session."""
    if SessionLocal is None:
        raise RuntimeError("Database connection not configured or failed to initialize.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
