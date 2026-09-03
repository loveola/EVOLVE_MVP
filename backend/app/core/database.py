import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

def get_engine():
    db_url = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    if not db_url:
        return None
    return create_engine(db_url, pool_pre_ping=True)

_engine = get_engine()
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine) if _engine else None

def get_db():
    if _SessionLocal is None:
        yield None
        return
    db: Session = _SessionLocal()
    try:
        yield db
    finally:
        db.close()
