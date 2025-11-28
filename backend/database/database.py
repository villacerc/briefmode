from typing import Any, Generator

from sqlalchemy.orm import Session, DeclarativeBase
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import AsyncGenerator

# TODO: refactor for other environments
# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/briefmode"
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,        # number of persistent connections
    max_overflow=20,     # how many "extra" connections beyond pool_size
    pool_timeout=30,     # seconds to wait before giving up
    pool_pre_ping=True   # makes dead connections auto-reconnect
)
AsyncSessionLocal  = sessionmaker(
    class_=AsyncSession,
    expire_on_commit=False, 
    bind=engine
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def drop_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)