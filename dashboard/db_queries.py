"""
dashboard/db_queries.py
────────────────────────
Query functions ที่ใช้ร่วมกันระหว่าง dashboard.py และ Reminders page
ทุก function คืนค่าเป็น pd.DataFrame พร้อมใช้งานใน Streamlit
"""

import os, sys
import pandas as pd
from datetime import date, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")
DATABASE_URL_SYNC = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://") if DATABASE_URL else ""

# ─── Engine (Singleton) ───────────────────────────────────────────────────────
_engine = None

def get_engine():
    global _engine
    if _engine is None and DATABASE_URL_SYNC:
        _engine = create_engine(DATABASE_URL_SYNC, pool_pre_ping=True)
    return _engine


def is_db_available() -> bool:
    engine = get_engine()
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            # ตรวจทั้ง connection และว่า table 'cats' มีอยู่จริง
            conn.execute(text(
                "SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name='cats'"
            )).fetchone()
        return True
    except Exception:
        return False


def query_df(sql: str, params: dict = {}) -> pd.DataFrame:
    """รัน SQL และคืน DataFrame"""
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ─── Expense Queries ──────────────────────────────────────────────────────────
def get_expense_summary_by_month(months: int = 6) -> pd.DataFrame:
    """
    ค่าใช้จ่ายรายเดือน แยกหมวดหมู่ (6 เดือนย้อนหลัง)
    คืน columns: month (str), category, amount
    """
    sql = """
        SELECT
            TO_CHAR(expense_date, 'YYYY-MM') AS month,
            category,
            SUM(amount) AS amount
        FROM expenses
        WHERE expense_date >= CURRENT_DATE - (interval '1 month' * :months)
        GROUP BY 1, 2
        ORDER BY 1, 2
    """
    return query_df(sql, {"months": months})


def get_expense_kpi(year: int = None, month: int = None) -> dict:
    """KPI ค่าใช้จ่ายของเดือนปัจจุบัน"""
    today = date.today()
    y = year or today.year
    m = month or today.month
    sql = """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE EXTRACT(YEAR FROM expense_date)  = :y
          AND EXTRACT(MONTH FROM expense_date) = :m
        GROUP BY category
    """
    df = query_df(sql, {"y": y, "m": m})
    result = {"total": 0.0}
    for _, row in df.iterrows():
        result[row["category"]] = float(row["total"])
        result["total"] += float(row["total"])
    return result


# ─── Weight & Food Queries ────────────────────────────────────────────────────
def get_weight_food_trend(cat_id: str, days: int = 30) -> pd.DataFrame:
    """
    ข้อมูลน้ำหนักและอาหารรายวัน สำหรับ Dual-Axis Chart
    คืน columns: date, avg_weight_kg, total_food_g
    """
    if not cat_id:  # ป้องกัน empty string ไปยัง UUID column
        return pd.DataFrame(columns=["date", "avg_weight_kg", "total_food_g"])
    sql = """
        SELECT
            DATE(recorded_at AT TIME ZONE 'Asia/Bangkok') AS date,
            AVG(CASE WHEN activity_type = 'weight' THEN weight_kg END)      AS avg_weight_kg,
            SUM(CASE WHEN activity_type = 'eating' THEN food_amount_g END)  AS total_food_g
        FROM activities
        WHERE cat_id = :cat_id
          AND recorded_at >= NOW() - (interval '1 day' * :days)
        GROUP BY 1
        ORDER BY 1
    """
    df = query_df(sql, {"cat_id": cat_id, "days": days})
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
        df["avg_weight_kg"] = df["avg_weight_kg"].ffill()  # fill missing weight days
    return df


def get_latest_weight(cat_id: str) -> float | None:
    """น้ำหนักล่าสุดของแมว"""
    if not cat_id:  # ป้องกัน empty string ไปยัง UUID column
        return None
    sql = """
        SELECT weight_kg FROM activities
        WHERE cat_id = :cat_id AND activity_type = 'weight'
        ORDER BY recorded_at DESC LIMIT 1
    """
    df = query_df(sql, {"cat_id": cat_id})
    return float(df.iloc[0]["weight_kg"]) if not df.empty else None


# ─── Cat Queries ──────────────────────────────────────────────────────────────
def get_all_cats() -> pd.DataFrame:
    """รายชื่อแมวทั้งหมดที่ is_active = true"""
    return query_df("SELECT id::text, name, breed, gender, birth_date FROM cats WHERE is_active = true ORDER BY name")


# ─── Reminder Queries ─────────────────────────────────────────────────────────
def get_upcoming_reminders(within_days: int = 14) -> pd.DataFrame:
    """
    Reminders ที่ due_date อยู่ภายใน X วันข้างหน้า + Overdue
    คืน columns: id, cat_name, reminder_type, title, description,
                 due_date, is_recurring, recurrence_days, status, days_remaining
    """
    sql = """
        SELECT
            r.id::text,
            COALESCE(c.name, 'ทั้งบ้าน') AS cat_name,
            r.reminder_type,
            r.title,
            r.description,
            r.due_date,
            r.is_recurring,
            r.recurrence_days,
            r.status,
            (r.due_date - CURRENT_DATE)  AS days_remaining
        FROM reminders r
        LEFT JOIN cats c ON c.id = r.cat_id
        WHERE r.status = 'pending'
          AND r.due_date <= CURRENT_DATE + (interval '1 day' * :days)
        ORDER BY r.due_date ASC
    """
    df = query_df(sql, {"days": within_days})
    if not df.empty:
        df["due_date"] = pd.to_datetime(df["due_date"])
    return df


def get_reminder_history(limit: int = 20) -> pd.DataFrame:
    """ประวัติ Reminders ที่ดำเนินการแล้ว"""
    sql = """
        SELECT
            r.title,
            COALESCE(c.name, 'ทั้งบ้าน') AS cat_name,
            r.reminder_type,
            r.due_date,
            r.status,
            r.notified_at
        FROM reminders r
        LEFT JOIN cats c ON c.id = r.cat_id
        WHERE r.status != 'pending'
        ORDER BY r.updated_at DESC
        LIMIT :limit
    """
    return query_df(sql, {"limit": limit})


def update_reminder_status(reminder_id: str, status: str) -> bool:
    """อัปเดต status ของ Reminder"""
    engine = get_engine()
    if engine is None:
        return False
    try:
        sql = text("UPDATE reminders SET status = :status, updated_at = NOW() WHERE id = :id")
        with engine.begin() as conn:
            conn.execute(sql, {"status": status, "id": reminder_id})
        return True
    except Exception as e:
        print(f"[DB] update_reminder_status error: {e}")
        return False
