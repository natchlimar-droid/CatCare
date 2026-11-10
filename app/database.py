"""
app/database.py
───────────────
SQLAlchemy Engine + Session Factory
รองรับทั้ง:
  - SQLite     (sqlite3 / aiosqlite) → Standalone / Zero Setup
  - PostgreSQL (psycopg2 / asyncpg)  → Production / Dedicated DB
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ─── Connection Strings ───────────────────────────────────────────────────────
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./catcare.db")

if DATABASE_URL.startswith("sqlite"):
    DATABASE_URL_SYNC = DATABASE_URL
    DATABASE_URL_ASYNC = DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    sync_engine = create_engine(
        DATABASE_URL_SYNC,
        connect_args={"check_same_thread": False},
        echo=False
    )
    async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)
else:
    DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    DATABASE_URL_SYNC  = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")
    sync_engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True, echo=False)
    async_engine = create_async_engine(DATABASE_URL_ASYNC, pool_pre_ping=True, echo=False)

SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)


# ─── Base Model ───────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── Dependency: FastAPI Async Session ───────────────────────────────────────
async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ─── Helper: Streamlit Sync Session ──────────────────────────────────────────
def get_sync_db():
    """Context manager สำหรับ Streamlit / Script"""
    db = SyncSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection() -> bool:
    """ทดสอบการเชื่อมต่อ DB"""
    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
