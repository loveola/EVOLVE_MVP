import os
from fastapi import HTTPException, status
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from dotenv import load_dotenv
from app.core.config import settings

load_dotenv()

Base = declarative_base()

def get_engine():
    db_url = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None)
    if not db_url:
        return None
    return create_engine(db_url, pool_pre_ping=True)

_engine = get_engine()
_SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine) if _engine else None

def get_db():
    if _SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is unavailable."
        )
    db: Session = _SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
