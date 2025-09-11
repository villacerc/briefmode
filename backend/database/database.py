from typing import Any, Generator

from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# TODO: refactor for other environments
# Database setup
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/briefmode"
engine = create_engine(
    DATABASE_URL,
    pool_size=10,        # number of persistent connections
    max_overflow=20,     # how many "extra" connections beyond pool_size
    pool_timeout=30,     # seconds to wait before giving up
    pool_pre_ping=True   # makes dead connections auto-reconnect
)
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    expire_on_commit=False, 
    bind=engine
)

class Base(DeclarativeBase):
    pass

def get_db() -> Generator[Session, Any, None]:
    """
    Provides a database session to path operations.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(bind=engine)

def drop_tables():
    Base.metadata.drop_all(bind=engine)