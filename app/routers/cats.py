"""
app/routers/cats.py
====================
CRUD endpoints สำหรับแมว + activities + expenses + reminders
ทุก endpoint ต้องการ JWT token
"""
import uuid
from datetime import date, datetime, time
from typing import Optional, List

import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_db
from app.routers.auth import get_current_user

router = APIRouter(prefix="/cats", tags=["Cats"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class CatCreate(BaseModel):
    name:       str
    breed:      Optional[str] = None
    gender:     str = "female"
    birth_date: Optional[date] = None   # Pydantic will parse YYYY-MM-DD
    color:      Optional[str] = None
    weight_kg:  Optional[float] = None


class CatOut(BaseModel):
    id:         str
    name:       str
    breed:      Optional[str]
    gender:     str
    birth_date: Optional[str]
    color:      Optional[str]
    is_active:  bool
    created_at: datetime


class ActivityCreate(BaseModel):
    activity_type:  str
    recorded_at:    datetime
    weight_kg:      Optional[float] = None
    food_brand:     Optional[str]  = None
    food_type:      Optional[str]  = None
    food_amount_g:  Optional[float] = None
    litter_type:    Optional[str]  = None
    notes:          Optional[str]  = None


class ExpenseCreate(BaseModel):
    category:     str
    amount:       float
    description:  Optional[str] = None
    expense_date: date


class ReminderCreate(BaseModel):
    reminder_type:      str
    title:              str
    description:        Optional[str] = None
    due_date:           date
    due_time:           Optional[time] = None
    is_recurring:       bool = False
    recurrence_days:    Optional[int] = None
    notify_before_days: int = 3


# ── Helpers ───────────────────────────────────────────────────────────────────
async def get_cat_or_404(cat_id: str, owner_id: str, db: AsyncSession) -> dict:
    result = await db.execute(text(
        "SELECT id::text, name, breed, gender, birth_date::text, color, is_active, created_at "
        "FROM cats WHERE id = :id AND owner_id = :owner AND is_active = true"
    ), {"id": uuid.UUID(cat_id), "owner": uuid.UUID(owner_id)})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="ไม่พบแมว")
    return dict(row._mapping)


# ── Cat CRUD ──────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[CatOut])
async def list_cats(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    result = await db.execute(text(
        "SELECT id::text, name, breed, gender, birth_date::text, color, is_active, created_at "
        "FROM cats WHERE owner_id = :owner AND is_active = true ORDER BY name"
    ), {"owner": uuid.UUID(current_user["id"])})
    return [dict(r._mapping) for r in result.fetchall()]


@router.post("/", response_model=CatOut, status_code=201)
async def create_cat(
    body: CatCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    cat_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO cats (id, name, breed, gender, birth_date, color, owner_id)
        VALUES (:id, :name, :breed, :gender, :birth_date, :color, :owner_id)
    """), {
        "id":         uuid.UUID(cat_id),
        "name":       body.name,
        "breed":      body.breed,
        "gender":     body.gender,
        "birth_date": body.birth_date,
        "color":      body.color,
        "owner_id":   uuid.UUID(current_user["id"])
    })

    # บันทึกน้ำหนักเริ่มต้น
    if body.weight_kg:
        await db.execute(text("""
            INSERT INTO activities (id, cat_id, activity_type, recorded_at, weight_kg)
            VALUES (:id, :cat_id, 'weight', now(), :weight_kg)
        """), {"id": uuid.uuid4(), "cat_id": uuid.UUID(cat_id), "weight_kg": body.weight_kg})

    await db.commit()
    return await get_cat_or_404(cat_id, current_user["id"], db)


@router.get("/{cat_id}", response_model=CatOut)
async def get_cat(
    cat_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    return await get_cat_or_404(cat_id, current_user["id"], db)


@router.delete("/{cat_id}", status_code=204)
async def delete_cat(
    cat_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    await db.execute(text(
        "UPDATE cats SET is_active = false WHERE id = :id"
    ), {"id": uuid.UUID(cat_id)})
    await db.commit()


# ── Activities ────────────────────────────────────────────────────────────────
@router.post("/{cat_id}/activities", status_code=201)
async def add_activity(
    cat_id: str,
    body: ActivityCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    act_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO activities
            (id, cat_id, activity_type, recorded_at, weight_kg, food_brand, food_type,
             food_amount_g, litter_type, notes)
        VALUES
            (:id, :cat_id, CAST(:activity_type AS VARCHAR), :recorded_at, 
             CAST(:weight_kg AS FLOAT), CAST(:food_brand AS VARCHAR), CAST(:food_type AS VARCHAR),
             CAST(:food_amount_g AS FLOAT), CAST(:litter_type AS VARCHAR), CAST(:notes AS TEXT))
    """), {
        "id":            uuid.UUID(act_id),
        "cat_id":        uuid.UUID(cat_id),
        "activity_type": body.activity_type,
        "recorded_at":   body.recorded_at,
        "weight_kg":     body.weight_kg,
        "food_brand":    body.food_brand,
        "food_type":     body.food_type,
        "food_amount_g": body.food_amount_g,
        "litter_type":   body.litter_type,
        "notes":         body.notes,
    })
    await db.commit()
    return {"id": act_id, "status": "created"}


@router.get("/{cat_id}/activities")
async def list_activities(
    cat_id: str,
    limit: int = 50,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    result = await db.execute(text("""
        SELECT id::text, activity_type, recorded_at, weight_kg, food_brand,
               food_type, food_amount_g, litter_type, notes
        FROM activities WHERE cat_id = :cat_id
        ORDER BY recorded_at DESC LIMIT :limit
    """), {"cat_id": uuid.UUID(cat_id), "limit": limit})
    return [dict(r._mapping) for r in result.fetchall()]


# ── Expenses ──────────────────────────────────────────────────────────────────
@router.post("/{cat_id}/expenses", status_code=201)
async def add_expense(
    cat_id: str,
    body: ExpenseCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    exp_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO expenses (id, cat_id, category, amount, description, expense_date)
        VALUES (:id, :cat_id, CAST(:category AS VARCHAR), CAST(:amount AS NUMERIC), CAST(:description AS VARCHAR), :expense_date)
    """), {
        "id":           uuid.UUID(exp_id),
        "cat_id":       uuid.UUID(cat_id),
        "category":     body.category,
        "amount":       body.amount,
        "description":  body.description,
        "expense_date": body.expense_date,
    })
    await db.commit()
    return {"id": exp_id, "status": "created"}


# ── Reminders ─────────────────────────────────────────────────────────────────
@router.post("/{cat_id}/reminders", status_code=201)
async def add_reminder(
    cat_id: str,
    body: ReminderCreate,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    rem_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO reminders
            (id, cat_id, reminder_type, title, description, due_date, due_time,
             is_recurring, recurrence_days, notify_before_days)
        VALUES
            (:id, :cat_id, CAST(:reminder_type AS VARCHAR), CAST(:title AS VARCHAR), CAST(:description AS VARCHAR), 
             :due_date, :due_time,
             CAST(:is_recurring AS BOOLEAN), CAST(:recurrence_days AS INTEGER), CAST(:notify_before_days AS INTEGER))
    """), {
        "id":                 uuid.UUID(rem_id),
        "cat_id":             uuid.UUID(cat_id),
        "reminder_type":      body.reminder_type,
        "title":              body.title,
        "description":        body.description,
        "due_date":           body.due_date,
        "due_time":           body.due_time,
        "is_recurring":       body.is_recurring,
        "recurrence_days":    body.recurrence_days,
        "notify_before_days": body.notify_before_days,
    })
    await db.commit()
    return {"id": rem_id, "status": "created"}


@router.get("/{cat_id}/reminders")
async def list_reminders(
    cat_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    await get_cat_or_404(cat_id, current_user["id"], db)
    result = await db.execute(text("""
        SELECT id::text, reminder_type, title, description, due_date::text,
               is_recurring, recurrence_days, notify_before_days, status,
               (due_date - CURRENT_DATE) AS days_remaining
        FROM reminders WHERE cat_id = :cat_id AND status = 'pending'
        ORDER BY due_date ASC
    """), {"cat_id": uuid.UUID(cat_id)})
    return [dict(r._mapping) for r in result.fetchall()]


# ── Dashboard Summary ─────────────────────────────────────────────────────────
@router.get("/{cat_id}/summary")
async def cat_summary(
    cat_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """ข้อมูลรวมสำหรับ Dashboard: น้ำหนักล่าสุด, ค่าใช้จ่ายเดือนนี้, นัดหมายถัดไป"""
    await get_cat_or_404(cat_id, current_user["id"], db)

    # น้ำหนักล่าสุด
    w = await db.execute(text(
        "SELECT weight_kg, recorded_at FROM activities "
        "WHERE cat_id = :id AND activity_type = 'weight' ORDER BY recorded_at DESC LIMIT 1"
    ), {"id": uuid.UUID(cat_id)})
    weight_row = w.fetchone()

    # ค่าใช้จ่ายเดือนนี้
    e = await db.execute(text(
        "SELECT COALESCE(SUM(amount),0) AS total FROM expenses "
        "WHERE cat_id = :id AND EXTRACT(YEAR FROM expense_date) = EXTRACT(YEAR FROM CURRENT_DATE) "
        "AND EXTRACT(MONTH FROM expense_date) = EXTRACT(MONTH FROM CURRENT_DATE)"
    ), {"id": uuid.UUID(cat_id)})
    expense_total = float((e.fetchone() or (0,))[0])

    # นัดหมายถัดไป
    r = await db.execute(text(
        "SELECT title, due_date::text, (due_date - CURRENT_DATE) AS days_remaining "
        "FROM reminders WHERE cat_id = :id AND status = 'pending' "
        "ORDER BY due_date ASC LIMIT 1"
    ), {"id": uuid.UUID(cat_id)})
    next_reminder = r.fetchone()

    return {
        "latest_weight":     {"kg": weight_row.weight_kg, "recorded_at": str(weight_row.recorded_at)} if weight_row else None,
        "expense_this_month": expense_total,
        "next_reminder":     dict(next_reminder._mapping) if next_reminder else None,
    }
