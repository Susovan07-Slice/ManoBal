from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
from core.config import settings, logger

def create_db_engine(db_url: str):
    connect_args = {}
    engine_kwargs = {"pool_pre_ping": True}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    elif db_url.startswith("postgresql"):
        engine_kwargs["pool_size"] = 10
        engine_kwargs["max_overflow"] = 20
    return create_engine(db_url, connect_args=connect_args, **engine_kwargs)

try:
    engine = create_db_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        pass
    logger.info(f"Database engine successfully connected: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
except Exception as e:
    fallback_url = "sqlite:///./personnel_welfare.db"
    logger.warning(f"Primary database connection failed ({e}). Gracefully falling back to local SQLite: {fallback_url}")
    engine = create_db_engine(fallback_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for yielding database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
