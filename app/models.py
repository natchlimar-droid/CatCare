"""
app/models/__init__.py + models/*.py (รวมในไฟล์เดียวเพื่อความสะดวก)
SQLAlchemy ORM Models สำหรับทุก Table
"""

import uuid
from datetime import date, datetime
from sqlalchemy import (
    String, Float, Boolean, Integer, Date, Time,
    DateTime, Text, Numeric, ForeignKey, func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ─── cats ─────────────────────────────────────────────────────────────────────
class Cat(Base):
    __tablename__ = "cats"

    id:               Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:             Mapped[str]       = mapped_column(String(100), nullable=False)
    breed:            Mapped[str | None]= mapped_column(String(100))
    gender:           Mapped[str]       = mapped_column(String(10), nullable=False)        # male / female
    birth_date:       Mapped[date | None]= mapped_column(Date)
    color:            Mapped[str | None]= mapped_column(String(50))
    profile_image_url:Mapped[str | None]= mapped_column(Text)
    is_active:        Mapped[bool]      = mapped_column(Boolean, default=True)
    created_at:       Mapped[datetime]  = mapped_column(DateTime(timezone=True), server_default=func.now())

    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="cat", cascade="all, delete")
    expenses:   Mapped[list["Expense"]]  = relationship("Expense",  back_populates="cat", cascade="all, delete")
    reminders:  Mapped[list["Reminder"]] = relationship("Reminder", back_populates="cat", cascade="all, delete")


# ─── activities ───────────────────────────────────────────────────────────────
class Activity(Base):
    __tablename__ = "activities"

    id:            Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:        Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), ForeignKey("cats.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str]        = mapped_column(String(30), nullable=False)   # eating / weight / litter / drinking
    recorded_at:   Mapped[datetime]   = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg:     Mapped[float|None] = mapped_column(Float)
    food_brand:    Mapped[str|None]   = mapped_column(String(100))
    food_type:     Mapped[str|None]   = mapped_column(String(20))                  # wet / dry / treat
    food_amount_g: Mapped[float|None] = mapped_column(Float)
    litter_type:   Mapped[str|None]   = mapped_column(String(50))                  # urine / feces
    notes:         Mapped[str|None]   = mapped_column(Text)
    created_at:    Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    cat: Mapped["Cat"] = relationship("Cat", back_populates="activities")


# ─── expenses ─────────────────────────────────────────────────────────────────
class Expense(Base):
    __tablename__ = "expenses"

    id:               Mapped[uuid.UUID]  = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:           Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    category:         Mapped[str]        = mapped_column(String(30), nullable=False)   # food / vet / medicine / toy / litter / other
    amount:           Mapped[float]      = mapped_column(Numeric(10, 2), nullable=False)
    description:      Mapped[str|None]   = mapped_column(String(255))
    receipt_image_url:Mapped[str|None]   = mapped_column(Text)
    expense_date:     Mapped[date]       = mapped_column(Date, nullable=False)
    created_at:       Mapped[datetime]   = mapped_column(DateTime(timezone=True), server_default=func.now())

    cat: Mapped["Cat | None"] = relationship("Cat", back_populates="expenses")


# ─── reminders ────────────────────────────────────────────────────────────────
class Reminder(Base):
    __tablename__ = "reminders"

    id:                 Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:             Mapped[uuid.UUID|None] = mapped_column(UUID(as_uuid=True), ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    reminder_type:      Mapped[str]          = mapped_column(String(30), nullable=False)
    title:              Mapped[str]          = mapped_column(String(200), nullable=False)
    description:        Mapped[str|None]     = mapped_column(Text)
    due_date:           Mapped[date]         = mapped_column(Date, nullable=False)
    due_time:           Mapped[str|None]     = mapped_column(Time)
    is_recurring:       Mapped[bool]         = mapped_column(Boolean, default=False)
    recurrence_days:    Mapped[int|None]     = mapped_column(Integer)
    notify_before_days: Mapped[int]          = mapped_column(Integer, default=3)
    status:             Mapped[str]          = mapped_column(String(20), default="pending")   # pending / notified / done / snoozed
    notified_at:        Mapped[datetime|None]= mapped_column(DateTime(timezone=True))
    created_at:         Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:         Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat | None"] = relationship("Cat", back_populates="reminders")
