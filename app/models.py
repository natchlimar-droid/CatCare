"""
app/models.py
SQLAlchemy ORM Models สำหรับทุก Table (Cats, Activities, Expenses, Reminders, Users)
รองรับทั้ง SQLite (Local/Mockup) และ PostgreSQL (Production)
"""

import uuid
from datetime import date, datetime
from sqlalchemy import (
    String, Float, Boolean, Integer, Date, Time,
    DateTime, Text, Numeric, ForeignKey, func, Uuid
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


# ─── users ─────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id:              Mapped[uuid.UUID]       = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username:        Mapped[str]             = mapped_column(String(50), unique=True, nullable=False, index=True)
    email:           Mapped[str]             = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]             = mapped_column(String(255), nullable=False)
    display_name:    Mapped[str | None]      = mapped_column(String(100))
    gender:          Mapped[str | None]      = mapped_column(String(10))
    is_active:       Mapped[bool]            = mapped_column(Boolean, default=True)
    created_at:      Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login:      Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    cats: Mapped[list["Cat"]] = relationship("Cat", back_populates="owner", cascade="all, delete")


# ─── cats ─────────────────────────────────────────────────────────────────────
class Cat(Base):
    __tablename__ = "cats"

    id:                Mapped[uuid.UUID]       = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id:          Mapped[uuid.UUID | None]= mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    name:              Mapped[str]             = mapped_column(String(100), nullable=False)
    breed:             Mapped[str | None]      = mapped_column(String(100))
    gender:            Mapped[str]             = mapped_column(String(10), nullable=False)        # male / female
    birth_date:        Mapped[date | None]     = mapped_column(Date)
    color:             Mapped[str | None]      = mapped_column(String(50))
    profile_image_url: Mapped[str | None]      = mapped_column(Text)
    is_active:         Mapped[bool]            = mapped_column(Boolean, default=True)
    created_at:        Mapped[datetime]        = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner:      Mapped["User | None"]        = relationship("User", back_populates="cats")
    activities: Mapped[list["Activity"]]     = relationship("Activity", back_populates="cat", cascade="all, delete")
    expenses:   Mapped[list["Expense"]]      = relationship("Expense",  back_populates="cat", cascade="all, delete")
    reminders:  Mapped[list["Reminder"]]     = relationship("Reminder", back_populates="cat", cascade="all, delete")


# ─── activities ───────────────────────────────────────────────────────────────
class Activity(Base):
    __tablename__ = "activities"

    id:            Mapped[uuid.UUID]    = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:        Mapped[uuid.UUID]    = mapped_column(Uuid(as_uuid=True), ForeignKey("cats.id", ondelete="CASCADE"), nullable=False)
    activity_type: Mapped[str]          = mapped_column(String(30), nullable=False)   # eating / weight / litter / drinking
    recorded_at:   Mapped[datetime]     = mapped_column(DateTime(timezone=True), nullable=False)
    weight_kg:     Mapped[float | None] = mapped_column(Float)
    food_brand:    Mapped[str | None]   = mapped_column(String(100))
    food_type:     Mapped[str | None]   = mapped_column(String(20))                  # wet / dry / treat
    food_amount_g: Mapped[float | None] = mapped_column(Float)
    litter_type:   Mapped[str | None]   = mapped_column(String(50))                  # urine / feces
    notes:         Mapped[str | None]   = mapped_column(Text)
    created_at:    Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())

    cat: Mapped["Cat"] = relationship("Cat", back_populates="activities")


# ─── expenses ─────────────────────────────────────────────────────────────────
class Expense(Base):
    __tablename__ = "expenses"

    id:                Mapped[uuid.UUID]        = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:            Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    category:          Mapped[str]              = mapped_column(String(30), nullable=False)   # food / vet / medicine / toy / litter / other
    amount:            Mapped[float]            = mapped_column(Numeric(10, 2), nullable=False)
    description:       Mapped[str | None]       = mapped_column(String(255))
    receipt_image_url: Mapped[str | None]       = mapped_column(Text)
    expense_date:      Mapped[date]             = mapped_column(Date, nullable=False)
    created_at:        Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    cat: Mapped["Cat | None"] = relationship("Cat", back_populates="expenses")


# ─── reminders ────────────────────────────────────────────────────────────────
class Reminder(Base):
    __tablename__ = "reminders"

    id:                 Mapped[uuid.UUID]        = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cat_id:             Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("cats.id", ondelete="SET NULL"), nullable=True)
    reminder_type:      Mapped[str]              = mapped_column(String(30), nullable=False)
    title:              Mapped[str]              = mapped_column(String(200), nullable=False)
    description:        Mapped[str | None]       = mapped_column(Text)
    due_date:           Mapped[date]             = mapped_column(Date, nullable=False)
    due_time:           Mapped[str | None]       = mapped_column(Time)
    is_recurring:       Mapped[bool]             = mapped_column(Boolean, default=False)
    recurrence_days:    Mapped[int | None]       = mapped_column(Integer)
    notify_before_days: Mapped[int]              = mapped_column(Integer, default=3)
    status:             Mapped[str]              = mapped_column(String(20), default="pending")   # pending / notified / done / snoozed
    notified_at:        Mapped[datetime | None]  = mapped_column(DateTime(timezone=True))
    created_at:         Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at:         Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    cat: Mapped["Cat | None"] = relationship("Cat", back_populates="reminders")


# ─── family_groups ─────────────────────────────────────────────────────────────
class FamilyGroup(Base):
    __tablename__ = "family_groups"

    id:             Mapped[uuid.UUID]        = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name:           Mapped[str]              = mapped_column(String(100), nullable=False)        # เช่น บ้านสามแสบสตูดิโอ
    invite_code:    Mapped[str]              = mapped_column(String(20), unique=True, nullable=False, index=True) # เช่น CAT-FAM-8821
    created_by_id:  Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    line_group_id:  Mapped[str | None]       = mapped_column(String(100))                         # LINE groupId e.g. C123456789...
    is_line_linked: Mapped[bool]             = mapped_column(Boolean, default=False)
    created_at:     Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    members:        Mapped[list["FamilyMember"]] = relationship("FamilyMember", back_populates="group", cascade="all, delete")


# ─── family_members ────────────────────────────────────────────────────────────
class FamilyMember(Base):
    __tablename__ = "family_members"

    id:             Mapped[uuid.UUID]        = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    group_id:       Mapped[uuid.UUID]        = mapped_column(Uuid(as_uuid=True), ForeignKey("family_groups.id", ondelete="CASCADE"), nullable=False)
    user_id:        Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    nickname:       Mapped[str]              = mapped_column(String(50), nullable=False)          # เช่น คุณแม่, คุณพ่อ, น้องนนท์
    role:           Mapped[str]              = mapped_column(String(30), default="member")        # admin (หัวหน้าทาส) / member (ผู้ช่วยทาส) / viewer (สังเกตการณ์)
    avatar_emoji:   Mapped[str]              = mapped_column(String(10), default="🧑‍🦰")
    phone_or_line:  Mapped[str | None]       = mapped_column(String(100))
    joined_at:      Mapped[datetime]         = mapped_column(DateTime(timezone=True), server_default=func.now())

    group:          Mapped["FamilyGroup"]    = relationship("FamilyGroup", back_populates="members")

