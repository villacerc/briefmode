from typing import Any, Generator

from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

# Database setup
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/briefmode"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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