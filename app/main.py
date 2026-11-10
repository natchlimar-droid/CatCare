"""
app/main.py — FastAPI Entry Point + APScheduler
================================================
รับผิดชอบ:
1. สร้าง FastAPI app และ mount routers
2. ตั้ง APScheduler รัน line_notifier.py ทุกเช้าตามเวลาที่กำหนดใน .env
3. Lifespan: start scheduler เมื่อ app เริ่ม / stop เมื่อ shutdown
4. Mount ui/ เป็น static files
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

load_dotenv()

# ── Import notifier job ────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from automation.line_notifier import run_notification_job

# ── Import routers ─────────────────────────────────────────────────────────────
from app.routers.auth import router as auth_router
from app.routers.cats import router as cats_router

log = logging.getLogger("catcare.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

CRON_HOUR   = int(os.getenv("NOTIFIER_CRON_HOUR",   "7"))
CRON_MINUTE = int(os.getenv("NOTIFIER_CRON_MINUTE", "0"))


# ─── APScheduler Setup ────────────────────────────────────────────────────────
scheduler = AsyncIOScheduler(timezone="Asia/Bangkok")


def setup_scheduler():
    scheduler.add_job(
        run_notification_job,
        trigger=CronTrigger(hour=CRON_HOUR, minute=CRON_MINUTE),
        id="line_notifier_daily",
        name="Daily LINE Notification",
        replace_existing=True,
        misfire_grace_time=300,
    )
    log.info(f"Scheduler set: daily at {CRON_HOUR:02d}:{CRON_MINUTE:02d} (Asia/Bangkok)")


from sqlalchemy import text
from app.database import async_engine

# ─── Lifespan ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Cat Care API starting...")

    # --- AUTO FIX DB (สร้างตาราง users อัตโนมัติถ้าไม่มี) ---
    try:
        async with async_engine.begin() as conn:
            has_users = await conn.scalar(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"))
            if not has_users:
                log.info("⏳ กำลังสร้างตาราง 'users' อัตโนมัติ...")
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
                log.info("✅ สร้างตาราง 'users' เสร็จสิ้น!")
            
            res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='cats' AND column_name='owner_id'"))
            if not res.fetchone():
                log.info("⏳ กำลังเพิ่มคอลัมน์ 'owner_id' ให้ตาราง 'cats'...")
                await conn.execute(text("ALTER TABLE cats ADD COLUMN owner_id UUID REFERENCES users(id) ON DELETE CASCADE;"))
                log.info("✅ เพิ่มคอลัมน์สำเร็จ!")
    except Exception as e:
        log.error(f"❌ DB Auto Fix failed: {e}")
    # ------------------------------------------------------

    setup_scheduler()
    scheduler.start()
    log.info(f"Scheduler started — Jobs: {[j.id for j in scheduler.get_jobs()]}")
    yield
    scheduler.shutdown(wait=False)
    log.info("Scheduler stopped")


# ─── FastAPI App ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Cat Care API",
    description="Backend API สำหรับ Cat Care Operations & Analytics",
    version="1.0.0",
    lifespan=lifespan,
)

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error(f"Global Error: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"detail": f"Backend Error: {str(exc)}"}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(cats_router)

# ─── Static UI files ──────────────────────────────────────────────────────────
_ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui")
if os.path.isdir(_ui_dir):
    app.mount("/ui", StaticFiles(directory=_ui_dir, html=True), name="ui")


# ─── Routes ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return RedirectResponse(url="/ui/login.html")


@app.get("/health", tags=["Health"])
async def health():
    jobs = [{"id": j.id, "next_run": str(j.next_run_time)} for j in scheduler.get_jobs()]
    return {"status": "healthy", "scheduler_jobs": jobs}


@app.post("/admin/trigger-notification", tags=["Admin"])
async def trigger_notification_now():
    asyncio.create_task(run_notification_job())
    return {"status": "triggered", "message": "Notification job running..."}


# ─── Run ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

