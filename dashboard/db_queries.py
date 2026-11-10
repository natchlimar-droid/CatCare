"""
dashboard/db_queries.py
────────────────────────
Query functions ที่ใช้ร่วมกันระหว่าง dashboard.py และ Reminders page
รองรับทั้ง SQLite (Local/Standalone) และ PostgreSQL (Production)
ทุก function คืนค่าเป็น pd.DataFrame พร้อมใช้งานใน Streamlit
"""

import os
import sys

# Ensure project root (CatCare/) is on sys.path so 'app' can always be imported
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import uuid
import pandas as pd
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import text
from app.database import sync_engine, SyncSessionLocal
from app.models import Cat, Activity, Expense, Reminder

def _to_uuid(val):
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except Exception:
        return val


def get_engine():
    return sync_engine


def is_db_available() -> bool:
    """ตรวจสอบว่าต่อ DB ได้และมีตาราง cats หรือไม่"""
    try:
        with sync_engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM cats LIMIT 1"))
        return True
    except Exception:
        return False


def query_df(sql: str, params: dict = {}) -> pd.DataFrame:
    """รัน raw SQL และคืน DataFrame"""
    try:
        with sync_engine.connect() as conn:
            return pd.read_sql(text(sql), conn, params=params)
    except Exception as e:
        print(f"[DB] query_df error: {e}")
        return pd.DataFrame()


# ─── Expense Queries ──────────────────────────────────────────────────────────
def get_expense_summary_by_month(months: int = 6) -> pd.DataFrame:
    """ค่าใช้จ่ายรายเดือน แยกหมวดหมู่ (6 เดือนย้อนหลัง)"""
    cutoff = date.today() - timedelta(days=months * 30)
    db = SyncSessionLocal()
    try:
        expenses = (
            db.query(Expense)
            .filter(Expense.expense_date >= cutoff)
            .order_by(Expense.expense_date.asc())
            .all()
        )
        if not expenses:
            return pd.DataFrame(columns=["month", "category", "amount"])

        records = [
            {
                "month": e.expense_date.strftime("%Y-%m"),
                "category": e.category,
                "amount": float(e.amount),
            }
            for e in expenses
        ]
        df = pd.DataFrame(records)
        df_grouped = df.groupby(["month", "category"], as_index=False)["amount"].sum()
        return df_grouped.sort_values(by=["month", "category"])
    except Exception as e:
        print(f"[DB] get_expense_summary_by_month error: {e}")
        return pd.DataFrame(columns=["month", "category", "amount"])
    finally:
        db.close()


def get_expense_kpi(year: int = None, month: int = None) -> dict:
    """KPI ค่าใช้จ่ายของเดือนปัจจุบัน"""
    today = date.today()
    y = year or today.year
    m = month or today.month

    db = SyncSessionLocal()
    result = {"total": 0.0}
    try:
        expenses = db.query(Expense).all()
        for e in expenses:
            if e.expense_date.year == y and e.expense_date.month == m:
                catg = e.category
                amt = float(e.amount)
                result[catg] = result.get(catg, 0.0) + amt
                result["total"] += amt
        return result
    except Exception as e:
        print(f"[DB] get_expense_kpi error: {e}")
        return result
    finally:
        db.close()


# ─── Weight & Food Queries ────────────────────────────────────────────────────
def get_weight_food_trend(cat_id: str, days: int = 30) -> pd.DataFrame:
    """ข้อมูลน้ำหนักและอาหารรายวัน สำหรับ Dual-Axis Chart"""
    if not cat_id:
        return pd.DataFrame(columns=["date", "avg_weight_kg", "total_food_g"])

    uid = _to_uuid(cat_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    db = SyncSessionLocal()
    try:
        activities = (
            db.query(Activity)
            .filter(
                Activity.cat_id == uid,
                Activity.recorded_at >= cutoff
            )
            .order_by(Activity.recorded_at.asc())
            .all()
        )
        if not activities:
            return pd.DataFrame(columns=["date", "avg_weight_kg", "total_food_g"])

        records = []
        for a in activities:
            rec_date = a.recorded_at.strftime("%Y-%m-%d") if isinstance(a.recorded_at, datetime) else str(a.recorded_at)[:10]
            records.append({
                "date": rec_date,
                "weight_kg": float(a.weight_kg) if a.weight_kg is not None else None,
                "food_amount_g": float(a.food_amount_g) if a.food_amount_g is not None else 0.0,
            })

        df = pd.DataFrame(records)
        df_grouped = df.groupby("date").agg(
            avg_weight_kg=("weight_kg", "mean"),
            total_food_g=("food_amount_g", "sum")
        ).reset_index()

        df_grouped["date"] = pd.to_datetime(df_grouped["date"])
        df_grouped["avg_weight_kg"] = df_grouped["avg_weight_kg"].ffill()
        return df_grouped
    except Exception as e:
        print(f"[DB] get_weight_food_trend error: {e}")
        return pd.DataFrame(columns=["date", "avg_weight_kg", "total_food_g"])
    finally:
        db.close()


def get_latest_weight(cat_id: str) -> float | None:
    """น้ำหนักล่าสุดของแมว"""
    if not cat_id:
        return None
    uid = _to_uuid(cat_id)
    db = SyncSessionLocal()
    try:
        latest = (
            db.query(Activity)
            .filter(Activity.cat_id == uid, Activity.activity_type == "weight")
            .order_by(Activity.recorded_at.desc())
            .first()
        )
        return float(latest.weight_kg) if latest and latest.weight_kg is not None else None
    except Exception as e:
        print(f"[DB] get_latest_weight error: {e}")
        return None
    finally:
        db.close()


# ─── Cat Queries ──────────────────────────────────────────────────────────────
def get_all_cats() -> pd.DataFrame:
    """รายชื่อแมวทั้งหมดที่ is_active = true"""
    db = SyncSessionLocal()
    try:
        cats = db.query(Cat).filter(Cat.is_active == True).order_by(Cat.name.asc()).all()
        records = [
            {
                "id": str(c.id),
                "name": c.name,
                "breed": c.breed or "",
                "gender": c.gender or "",
                "birth_date": c.birth_date,
            }
            for c in cats
        ]
        return pd.DataFrame(records)
    except Exception as e:
        print(f"[DB] get_all_cats error: {e}")
        return pd.DataFrame(columns=["id", "name", "breed", "gender", "birth_date"])
    finally:
        db.close()


# ─── Reminder Queries ─────────────────────────────────────────────────────────
def get_upcoming_reminders(within_days: int = 14) -> pd.DataFrame:
    """Reminders ที่ due_date อยู่ภายใน X วันข้างหน้า + Overdue"""
    target_date = date.today() + timedelta(days=within_days)
    db = SyncSessionLocal()
    try:
        reminders = (
            db.query(Reminder, Cat)
            .outerjoin(Cat, Reminder.cat_id == Cat.id)
            .filter(
                Reminder.status == "pending",
                Reminder.due_date <= target_date
            )
            .order_by(Reminder.due_date.asc())
            .all()
        )
        records = []
        today = date.today()
        for r, c in reminders:
            days_rem = (r.due_date - today).days if r.due_date else 0
            records.append({
                "id": str(r.id),
                "cat_name": c.name if c else "ทั้งบ้าน",
                "reminder_type": r.reminder_type,
                "title": r.title,
                "description": r.description or "",
                "due_date": r.due_date,
                "is_recurring": r.is_recurring,
                "recurrence_days": r.recurrence_days,
                "status": r.status,
                "days_remaining": days_rem,
            })
        df = pd.DataFrame(records)
        if not df.empty:
            df["due_date"] = pd.to_datetime(df["due_date"])
        return df
    except Exception as e:
        print(f"[DB] get_upcoming_reminders error: {e}")
        return pd.DataFrame()
    finally:
        db.close()


def get_reminder_history(limit: int = 20) -> pd.DataFrame:
    """ประวัติ Reminders ที่ดำเนินการแล้ว"""
    db = SyncSessionLocal()
    try:
        reminders = (
            db.query(Reminder, Cat)
            .outerjoin(Cat, Reminder.cat_id == Cat.id)
            .filter(Reminder.status != "pending")
            .order_by(Reminder.updated_at.desc())
            .limit(limit)
            .all()
        )
        records = []
        for r, c in reminders:
            records.append({
                "title": r.title,
                "cat_name": c.name if c else "ทั้งบ้าน",
                "reminder_type": r.reminder_type,
                "due_date": r.due_date,
                "status": r.status,
                "notified_at": r.notified_at,
            })
        return pd.DataFrame(records)
    except Exception as e:
        print(f"[DB] get_reminder_history error: {e}")
        return pd.DataFrame()
    finally:
        db.close()


def update_reminder_status(reminder_id: str, status: str) -> bool:
    """อัปเดต status ของ Reminder"""
    db = SyncSessionLocal()
    try:
        r = db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if r:
            r.status = status
            r.updated_at = datetime.now(timezone.utc)
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        print(f"[DB] update_reminder_status error: {e}")
        return False
    finally:
        db.close()
