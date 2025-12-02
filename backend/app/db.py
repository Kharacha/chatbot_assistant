# backend/app/db.py

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from pgvector.psycopg2 import register_vector
from .config import settings


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


# Create engine using your Supabase DATABASE_URL
# pool_pre_ping=True is important when using Supabase's Session Pooler (pgbouncer)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 👈 this makes SQLAlchemy check stale connections
)


# Register pgvector with psycopg2 connections
@event.listens_for(engine, "connect")
def connect(dbapi_connection, connection_record):
    # arrays=True is optional; use it later if you store arrays of vectors
    register_vector(dbapi_connection)


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """FastAPI dependency that yields a DB session."""
    from sqlalchemy.orm import Session

    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
