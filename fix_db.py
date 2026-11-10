import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://catcare_user:catcare2024@127.0.0.1:5432/catcare_db")
DATABASE_URL_ASYNC = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

async def test_db():
    engine = create_async_engine(DATABASE_URL_ASYNC)
    async with engine.begin() as conn:
        print("✅ เชื่อมต่อ Database ได้สำเร็จ!")
        
        # เช็คตาราง users
        result = await conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"))
        has_users = result.scalar()
        if has_users:
            print("✅ พบตาราง 'users' ในระบบแล้ว")
        else:
            print("❌ ไม่พบตาราง 'users' -- กำลังสร้างตาราง...")
            await conn.execute(text("""
                CREATE TABLE users (
                    id UUID PRIMARY KEY,
                    username VARCHAR(50) NOT NULL UNIQUE,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    hashed_password VARCHAR(255) NOT NULL,
                    display_name VARCHAR(100),
                    gender VARCHAR(10),
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
                    last_login TIMESTAMP WITH TIME ZONE
                );
            """))
            print("✅ สร้างตาราง 'users' สำเร็จ!")
            
        # เช็คคอลัมน์ owner_id ใน cats
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name='cats' AND column_name='owner_id'
        """))
        if result.fetchone():
            print("✅ พบคอลัมน์ 'owner_id' ในตาราง 'cats' แล้ว")
        else:
            print("❌ ไม่พบคอลัมน์ 'owner_id' ในตาราง 'cats' -- กำลังเพิ่มคอลัมน์...")
            await conn.execute(text("""
                ALTER TABLE cats ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE CASCADE;
            """))
            print("✅ เพิ่มคอลัมน์ 'owner_id' สำเร็จ!")

    await engine.dispose()
    print("🎉 การตรวจสอบและแก้ไข Database เสร็จสมบูรณ์! กลับไปหน้าเว็บแล้วลองใหม่ได้เลยครับ")

if __name__ == "__main__":
    asyncio.run(test_db())
