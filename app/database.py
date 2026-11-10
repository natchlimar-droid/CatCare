"""
app/database.py
───────────────
SQLAlchemy Engine + Session Factory
รองรับทั้ง:
  - Sync  (psycopg2)  → ใช้กับ Alembic และ Streamlit
  - Async (asyncpg)   → ใช้กับ FastAPI endpoints
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

# ─── Connection Strings ───────────────────────────────────────────────────────
DATABASE_URL       = os.getenv("DATABASE_URL", "postgresql://catcare_user:password@localhost:5432/catcare_db")
DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
DATABASE_URL_SYNC  = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://")

# ─── Sync Engine (Alembic + Streamlit) ───────────────────────────────────────
sync_engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True, echo=False)
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)

# ─── Async Engine (FastAPI) ───────────────────────────────────────────────────
async_engine = create_async_engine(DATABASE_URL_ASYNC, pool_pre_ping=True, echo=False)
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
    except Exception as e:
        print(f"[DB] Connection failed: {e}")
        return False
