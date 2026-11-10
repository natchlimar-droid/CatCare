"""
app/routers/auth.py
===================
FastAPI Auth Router — Register / Login / Me
ใช้ JWT (python-jose) + bcrypt (passlib)
"""
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
import bcrypt
from dotenv import load_dotenv
import os

from app.database import get_async_db

load_dotenv()

# ── Config ────────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv("JWT_SECRET_KEY", "catcare-super-secret-change-in-production")
ALGORITHM    = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24h

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Schemas ───────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username:     str
    email:        EmailStr
    password:     str
    display_name: Optional[str] = None
    gender:       Optional[str] = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        import re
        if len(v) < 3:
            raise ValueError("ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError("ชื่อผู้ใช้ใช้ได้เฉพาะ a-z, 0-9, _")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user_id:      str
    username:     str
    display_name: Optional[str]


class UserOut(BaseModel):
    id:           str
    username:     str
    email:        str
    display_name: Optional[str]
    gender:       Optional[str]
    created_at:   datetime


class CatCreateRequest(BaseModel):
    name:       str
    breed:      Optional[str] = None
    gender:     str = "female"
    birth_date: Optional[str] = None
    color:      Optional[str] = None
    weight_kg:  Optional[float] = None   # สำหรับบันทึก activity ครั้งแรก


# ── Helpers ───────────────────────────────────────────────────────────────────
def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode('utf-8'), hashed.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token ไม่ถูกต้องหรือหมดอายุ",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(text(
        "SELECT id::text, username, email, display_name, gender FROM users WHERE id = :uid AND is_active = true"
    ), {"uid": uuid.UUID(user_id)})
    row = result.fetchone()
    if row is None:
        raise credentials_exception
    return dict(row._mapping)


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_async_db)):
    # ตรวจ duplicate
    dup = await db.execute(text(
        "SELECT id FROM users WHERE username = :u OR email = :e"
    ), {"u": body.username, "e": body.email})
    if dup.fetchone():
        raise HTTPException(status_code=409, detail="ชื่อผู้ใช้หรืออีเมลนี้ถูกใช้แล้ว")

    user_id = str(uuid.uuid4())
    await db.execute(text("""
        INSERT INTO users (id, username, email, hashed_password, display_name, gender)
        VALUES (:id, :username, :email, :hashed_password, :display_name, :gender)
    """), {
        "id":              uuid.UUID(user_id),
        "username":        body.username,
        "email":           body.email,
        "hashed_password": hash_password(body.password),
        "display_name":    body.display_name or body.username,
        "gender":          body.gender,
    })
    await db.commit()

    token = create_access_token({"sub": user_id})
    return TokenResponse(
        access_token=token,
        user_id=user_id,
        username=body.username,
        display_name=body.display_name or body.username,
    )


@router.post("/login", response_model=TokenResponse)
async def login(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text(
        "SELECT id::text, username, email, hashed_password, display_name FROM users WHERE username = :u AND is_active = true"
    ), {"u": form.username.lower()})
    row = result.fetchone()

    if not row or not verify_password(form.password, row.hashed_password):
        raise HTTPException(status_code=401, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    # อัปเดต last_login
    await db.execute(text(
        "UPDATE users SET last_login = now() WHERE id = :id"
    ), {"id": uuid.UUID(row.id)})
    await db.commit()

    token = create_access_token({"sub": row.id})
    return TokenResponse(
        access_token=token,
        user_id=row.id,
        username=row.username,
        display_name=row.display_name,
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: dict = Depends(get_current_user), db: AsyncSession = Depends(get_async_db)):
    result = await db.execute(text(
        "SELECT id::text, username, email, display_name, gender, created_at FROM users WHERE id = :id"
    ), {"id": uuid.UUID(current_user["id"])})
    row = result.fetchone()
    return dict(row._mapping)


@router.post("/check-username")
async def check_username(body: dict, db: AsyncSession = Depends(get_async_db)):
    """ตรวจว่าชื่อผู้ใช้ว่างอยู่ไหม (real-time validation)"""
    username = body.get("username", "").lower()
    result = await db.execute(text("SELECT 1 FROM users WHERE username = :u"), {"u": username})
    available = result.fetchone() is None
    return {"username": username, "available": available}
