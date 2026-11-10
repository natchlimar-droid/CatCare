"""
🐱 Cat Care — Proactive LINE Notification Script
================================================
หน้าที่: Query ข้อมูล Reminders จาก DB แล้วส่งแจ้งเตือนเข้า LINE
รองรับ: LINE Notify Token และ LINE Messaging API (Webhook)

ตรรกะวันที่ (Date Logic):
- "tomorrow" reminders  → due_date == วันพรุ่งนี้ (แจ้งล่วงหน้า 1 วัน)
- "overdue" reminders   → due_date < วันนี้ และ status ยังเป็น pending
- "litter_change"       → ตรวจสอบทุกวันว่าครบกำหนดหรือยัง
สคริปต์นี้ออกแบบให้รัน via Cron Job หรือ APScheduler ทุกเช้า
"""

import os
import logging
import asyncio
from datetime import date, timedelta
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import httpx
from dotenv import load_dotenv

# ─── Config & Logging ────────────────────────────────────────────────────────
load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("catcare.notifier")

LINE_NOTIFY_TOKEN = os.getenv("LINE_NOTIFY_TOKEN", "")
LINE_MSG_CHANNEL_TOKEN = os.getenv("LINE_MESSAGING_CHANNEL_TOKEN", "")
LINE_MSG_USER_ID = os.getenv("LINE_MESSAGING_USER_ID", "")


# ─── Data Models (จำลองแทน SQLAlchemy ORM) ───────────────────────────────────
class ReminderType(str, Enum):
    VACCINE = "vaccine"
    VET_CHECKUP = "vet_checkup"
    LITTER_CHANGE = "litter_change"
    MEDICINE = "medicine"
    GROOMING = "grooming"
    CUSTOM = "custom"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    NOTIFIED = "notified"
    DONE = "done"
    SNOOZED = "snoozed"


REMINDER_EMOJI = {
    ReminderType.VACCINE: "💉",
    ReminderType.VET_CHECKUP: "🏥",
    ReminderType.LITTER_CHANGE: "🪣",
    ReminderType.MEDICINE: "💊",
    ReminderType.GROOMING: "✂️",
    ReminderType.CUSTOM: "📌",
}


@dataclass
class Reminder:
    id: str
    cat_name: Optional[str]          # None = ทั้งบ้าน
    reminder_type: ReminderType
    title: str
    description: Optional[str]
    due_date: date
    status: ReminderStatus = ReminderStatus.PENDING
    is_recurring: bool = False
    recurrence_days: Optional[int] = None


# ─── Mock Database ────────────────────────────────────────────────────────────
def get_mock_reminders() -> list[Reminder]:
    """
    จำลองข้อมูลจาก DB — ใน Production ให้แทนด้วย SQLAlchemy Query:

        session.query(Reminder).filter(
            Reminder.status == "pending",
            Reminder.due_date <= date.today() + timedelta(days=notify_before_days)
        ).all()
    """
    today = date.today()
    return [
        Reminder(
            id="r001",
            cat_name="น้องมิ้ว",
            reminder_type=ReminderType.VACCINE,
            title="ฉีดวัคซีนรวม (Booster)",
            description="วัคซีน FVRCP ครั้งที่ 2",
            due_date=today + timedelta(days=1),   # พรุ่งนี้
        ),
        Reminder(
            id="r002",
            cat_name=None,
            reminder_type=ReminderType.LITTER_CHANGE,
            title="เปลี่ยนทรายแมว",
            description="ทราย Unicharm Dual Power",
            due_date=today,                        # วันนี้
            is_recurring=True,
            recurrence_days=14,
        ),
        Reminder(
            id="r003",
            cat_name="น้องโมจิ",
            reminder_type=ReminderType.MEDICINE,
            title="ให้ยาถ่ายพยาธิ",
            description="Drontal ครั้งที่ 1",
            due_date=today - timedelta(days=2),   # เลยกำหนดแล้ว (overdue)
        ),
        Reminder(
            id="r004",
            cat_name="น้องมิ้ว",
            reminder_type=ReminderType.VET_CHECKUP,
            title="ตรวจสุขภาพประจำปี",
            description=None,
            due_date=today + timedelta(days=5),   # ยังไม่ถึงเวลา → ข้ามไป
        ),
    ]


# ─── Date Logic Engine ────────────────────────────────────────────────────────
@dataclass
class NotifyCandidate:
    reminder: Reminder
    urgency_label: str  # "📅 พรุ่งนี้" / "🔴 เลยกำหนด" / "🔔 วันนี้"
    days_diff: int      # บวก = อนาคต, ลบ = เลยกำหนด


def evaluate_reminders(
    reminders: list[Reminder],
    notify_before_days: int = 1,
) -> list[NotifyCandidate]:
    """
    ─── ตรรกะวันที่ (Date Calculation Logic) ───────────────────────────────
    today       = วันนี้
    tomorrow    = today + 1 วัน

    เงื่อนไขที่จะส่งแจ้งเตือน:
    1. due_date == tomorrow               → แจ้งล่วงหน้า 1 วัน (label: "📅 พรุ่งนี้")
    2. due_date == today                  → ถึงกำหนดวันนี้แล้ว (label: "🔔 วันนี้")
    3. due_date < today AND pending       → เลยกำหนด ต้องเร่งดำเนินการ (label: "🔴 เลยกำหนด")

    เงื่อนไขที่ "ข้าม" (ไม่ส่ง):
    - due_date > tomorrow                 → ยังมีเวลาเหลือ ยังไม่ต้องแจ้ง
    - status != pending                   → ดำเนินการแล้ว หรือแจ้งไปแล้ว
    """
    today = date.today()
    candidates: list[NotifyCandidate] = []

    for r in reminders:
        # ข้ามรายการที่ไม่ใช่ pending
        if r.status != ReminderStatus.PENDING:
            log.debug(f"[SKIP] {r.title!r} — status: {r.status.value}")
            continue

        days_diff = (r.due_date - today).days  # บวก=อนาคต, 0=วันนี้, ลบ=เลยกำหนด

        if days_diff == 1:
            label = "📅 พรุ่งนี้"
        elif days_diff == 0:
            label = "🔔 วันนี้"
        elif days_diff < 0:
            label = "🔴 เลยกำหนด"
        else:
            # ยังไม่ถึงเวลาแจ้ง
            log.debug(f"[SKIP] {r.title!r} — due in {days_diff} days")
            continue

        candidates.append(NotifyCandidate(reminder=r, urgency_label=label, days_diff=days_diff))
        log.info(f"[QUEUE] {label} | {r.title} (due: {r.due_date})")

    return candidates


# ─── Message Builder ──────────────────────────────────────────────────────────
def build_line_message(candidates: list[NotifyCandidate]) -> str:
    """สร้างข้อความ LINE แบบ formatted สำหรับส่ง"""
    if not candidates:
        return ""

    lines = ["🐱 แจ้งเตือน Cat Care", "─" * 28]

    for c in candidates:
        r = c.reminder
        emoji = REMINDER_EMOJI.get(r.reminder_type, "📌")
        cat_label = f"[{r.cat_name}] " if r.cat_name else "[ทั้งบ้าน] "

        lines.append(f"{emoji} {cat_label}{r.title}")
        lines.append(f"   {c.urgency_label} | {r.due_date.strftime('%d/%m/%Y')}")
        if r.description:
            lines.append(f"   📝 {r.description}")
        lines.append("")

    lines.append("─" * 28)
    lines.append("🏠 Cat Care Automation")
    return "\n".join(lines)


# ─── LINE Sender ──────────────────────────────────────────────────────────────
async def send_line_notify(message: str, client: httpx.AsyncClient) -> bool:
    """ส่งผ่าน LINE Notify (ง่ายที่สุด — ส่งเข้า Group หรือ Chat ของตัวเอง)"""
    if not LINE_NOTIFY_TOKEN:
        log.warning("LINE_NOTIFY_TOKEN ไม่ได้ตั้งค่า — ข้าม LINE Notify")
        return False
    try:
        resp = await client.post(
            "https://notify-api.line.me/api/notify",
            headers={"Authorization": f"Bearer {LINE_NOTIFY_TOKEN}"},
            data={"message": f"\n{message}"},
            timeout=10.0,
        )
        resp.raise_for_status()
        log.info(f"✅ LINE Notify ส่งสำเร็จ (status: {resp.status_code})")
        return True
    except httpx.HTTPStatusError as e:
        log.error(f"❌ LINE Notify HTTP Error: {e.response.status_code} — {e.response.text}")
    except httpx.RequestError as e:
        log.error(f"❌ LINE Notify Network Error: {e}")
    return False


async def send_line_messaging_api(message: str, client: httpx.AsyncClient) -> bool:
    """ส่งผ่าน LINE Messaging API (Push Message) — รองรับ Rich Message ในอนาคต"""
    if not LINE_MSG_CHANNEL_TOKEN or not LINE_MSG_USER_ID:
        log.warning("LINE_MESSAGING_* ไม่ได้ตั้งค่า — ข้าม Messaging API")
        return False
    try:
        payload = {
            "to": LINE_MSG_USER_ID,
            "messages": [{"type": "text", "text": message}],
        }
        resp = await client.post(
            "https://api.line.me/v2/bot/message/push",
            headers={
                "Authorization": f"Bearer {LINE_MSG_CHANNEL_TOKEN}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10.0,
        )
        resp.raise_for_status()
        log.info(f"✅ LINE Messaging API ส่งสำเร็จ (status: {resp.status_code})")
        return True
    except httpx.HTTPStatusError as e:
        log.error(f"❌ Messaging API HTTP Error: {e.response.status_code} — {e.response.text}")
    except httpx.RequestError as e:
        log.error(f"❌ Messaging API Network Error: {e}")
    return False


async def mark_as_notified(reminder_id: str) -> None:
    """
    อัปเดต status = 'notified' ใน DB
    ใน Production ให้แทนด้วย:
        session.query(Reminder).filter_by(id=reminder_id).update({"status": "notified"})
        session.commit()
    """
    log.info(f"[DB] Marked reminder {reminder_id!r} → notified")


# ─── Main Runner ──────────────────────────────────────────────────────────────
async def run_notification_job() -> None:
    """
    จุดเริ่มต้นของ Automation Job
    เรียงลำดับการทำงาน:
    1. ดึงข้อมูล Reminders จาก DB
    2. คัดกรองตาม Date Logic
    3. สร้างข้อความ
    4. ส่ง LINE (Notify + Messaging API)
    5. อัปเดต status ใน DB
    """
    log.info("=" * 50)
    log.info("🚀 เริ่มต้น Cat Care Notification Job")
    log.info(f"📅 วันนี้: {date.today().strftime('%d/%m/%Y')}")
    log.info("=" * 50)

    # Step 1: Query DB
    all_reminders = get_mock_reminders()
    log.info(f"📋 Reminders ทั้งหมดใน DB: {len(all_reminders)} รายการ")

    # Step 2: คัดกรองตาม Date Logic
    candidates = evaluate_reminders(all_reminders, notify_before_days=1)

    if not candidates:
        log.info("✨ ไม่มี Reminder ที่ต้องแจ้งเตือนวันนี้")
        return

    log.info(f"🔔 พบ {len(candidates)} รายการที่ต้องแจ้งเตือน")

    # Step 3: สร้างข้อความ
    message = build_line_message(candidates)
    log.info(f"\n{'─'*40}\n{message}\n{'─'*40}")

    # Step 4: ส่ง LINE
    async with httpx.AsyncClient() as client:
        notify_ok = await send_line_notify(message, client)
        msg_ok = await send_line_messaging_api(message, client)

    # Step 5: อัปเดต DB ถ้าส่งสำเร็จอย่างน้อย 1 ช่องทาง
    if notify_ok or msg_ok:
        for c in candidates:
            await mark_as_notified(c.reminder.id)
    else:
        log.error("⚠️ ไม่สามารถส่ง LINE ได้ทุกช่องทาง — ไม่อัปเดต DB")

    log.info("✅ Notification Job เสร็จสิ้น")


if __name__ == "__main__":
    asyncio.run(run_notification_job())
