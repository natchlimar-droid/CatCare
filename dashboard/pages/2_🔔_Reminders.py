"""
🐱 Cat Care — Reminders Page
==============================
แสดงตาราง Upcoming Events + ประวัติ + จัดการสถานะ
"""

import streamlit as st
import pandas as pd
from datetime import date, timedelta
import sys, os

# ── Resolve paths: works from both `streamlit run dashboard/dashboard.py`
#    and direct `python pages/2_*.py` invocations
_pages_dir   = os.path.dirname(os.path.abspath(__file__))
_dash_dir    = os.path.dirname(_pages_dir)   # dashboard/
_project_dir = os.path.dirname(_dash_dir)    # CatCare/
for _p in (_dash_dir, _project_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db_queries import (
    is_db_available, get_upcoming_reminders,
    get_reminder_history, update_reminder_status,
)

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="🔔 Reminders | Cat Care", page_icon="🔔",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@400;600&family=Prompt:wght@600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Sarabun', sans-serif !important;
    background: linear-gradient(135deg, #FFF8F0 0%, #F7F1E3 100%) !important;
}
h1,h2,h3 { font-family: 'Prompt', sans-serif !important; color: #2C3E50 !important; }
.reminder-card {
    border-radius: 14px; padding: 1rem 1.2rem;
    margin-bottom: 0.7rem; border-left: 5px solid;
    background: #FFFAF4;
    box-shadow: 0 2px 12px rgba(255,159,67,0.10);
    display: flex; align-items: flex-start; gap: 1rem;
}
.card-overdue  { border-color: #FF6B9D; background: #FFF0F6; }
.card-today    { border-color: #FF9F43; background: #FFF8ED; }
.card-soon     { border-color: #FFD93D; background: #FFFDE7; }
.card-upcoming { border-color: #A8E6CF; background: #F0FFF8; }
.r-icon   { font-size: 2rem; flex-shrink: 0; margin-top: 2px; }
.r-body   { flex: 1; }
.r-title  { font-weight: 700; font-size: 0.98rem; color: #2C3E50; margin-bottom: 2px; }
.r-meta   { font-size: 0.8rem; color: #666; }
.r-badge  {
    display: inline-block; border-radius: 20px;
    padding: 2px 10px; font-size: 0.75rem; font-weight: 700;
    margin-left: 8px;
}
.badge-overdue  { background: #FF6B9D; color: white; }
.badge-today    { background: #FF9F43; color: white; }
.badge-soon     { background: #FFD93D; color: #5A4A00; }
.badge-upcoming { background: #A8E6CF; color: #1A5C3A; }
.stButton button {
    background: linear-gradient(135deg, #FF9F43, #FFB347) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 0.8rem !important; padding: 0.3rem 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Type Config ──────────────────────────────────────────────────────────────
TYPE_EMOJI = {
    "vaccine":     "💉",
    "vet_checkup": "🏥",
    "litter_change":"🪣",
    "medicine":    "💊",
    "grooming":    "✂️",
    "custom":      "📌",
}
TYPE_LABEL = {
    "vaccine": "วัคซีน", "vet_checkup": "ตรวจสุขภาพ",
    "litter_change": "เปลี่ยนทราย", "medicine": "ยา",
    "grooming": "ตัดขน/เล็บ", "custom": "อื่นๆ",
}


def get_card_class(days_remaining: int) -> tuple[str, str, str]:
    """คืน (card_class, badge_class, badge_text)"""
    if days_remaining < 0:
        return "card-overdue",  "badge-overdue",  f"🔴 เลย {abs(days_remaining)} วัน"
    elif days_remaining == 0:
        return "card-today",    "badge-today",    "🔔 วันนี้"
    elif days_remaining <= 3:
        return "card-soon",     "badge-soon",     f"⚠️ อีก {days_remaining} วัน"
    else:
        return "card-upcoming", "badge-upcoming", f"📅 อีก {days_remaining} วัน"


# ─── Mock data fallback ───────────────────────────────────────────────────────
def get_mock_upcoming() -> pd.DataFrame:
    today = date.today()
    return pd.DataFrame([
        {"id": "r001", "cat_name": "น้องสามสี", "reminder_type": "vaccine",
         "title": "ฉีดวัคซีนรวม (Booster)", "description": "FVRCP ครั้งที่ 2",
         "due_date": pd.Timestamp(today + timedelta(days=1)),
         "is_recurring": False, "recurrence_days": None, "status": "pending", "days_remaining": 1},
        {"id": "r002", "cat_name": "ทั้งบ้าน", "reminder_type": "litter_change",
         "title": "เปลี่ยนทรายแมว", "description": "Unicharm Dual Power",
         "due_date": pd.Timestamp(today),
         "is_recurring": True, "recurrence_days": 14, "status": "pending", "days_remaining": 0},
        {"id": "r003", "cat_name": "น้องสามสี", "reminder_type": "medicine",
         "title": "ยาถ่ายพยาธิ", "description": "Drontal ครั้งที่ 1",
         "due_date": pd.Timestamp(today - timedelta(days=2)),
         "is_recurring": False, "recurrence_days": None, "status": "pending", "days_remaining": -2},
        {"id": "r004", "cat_name": "น้องสามสี", "reminder_type": "grooming",
         "title": "ตัดเล็บ", "description": None,
         "due_date": pd.Timestamp(today + timedelta(days=7)),
         "is_recurring": True, "recurrence_days": 28, "status": "pending", "days_remaining": 7},
        {"id": "r005", "cat_name": "น้องสามสี", "reminder_type": "vet_checkup",
         "title": "ตรวจสุขภาพประจำปี", "description": "โรงพยาบาลสัตว์ใกล้บ้าน",
         "due_date": pd.Timestamp(today + timedelta(days=12)),
         "is_recurring": False, "recurrence_days": None, "status": "pending", "days_remaining": 12},
    ])


# ─── Header ───────────────────────────────────────────────────────────────────
st.title("🔔 ตารางนัดหมาย & กำหนดการ")

DB_LIVE = is_db_available()
if DB_LIVE:
    st.markdown('<span style="background:#d4edda;color:#155724;border-radius:20px;padding:3px 14px;font-size:0.82rem;font-weight:600">🟢 Live Database</span>', unsafe_allow_html=True)
else:
    st.markdown('<span style="background:#fff3cd;color:#856404;border-radius:20px;padding:3px 14px;font-size:0.82rem;font-weight:600">🟡 Demo Mode</span>', unsafe_allow_html=True)

st.markdown("---")

# ─── Sidebar Filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🐱 Cat Care")
    st.markdown("---")
    st.subheader("🔍 ตัวกรอง")
    within_days = st.slider("แสดงล่วงหน้ากี่วัน", 3, 30, 14)
    filter_type = st.multiselect(
        "ประเภท", list(TYPE_LABEL.values()),
        default=list(TYPE_LABEL.values())
    )
    st.markdown("---")
    st.caption("📅 " + date.today().strftime("%d/%m/%Y"))

# ─── Upcoming Reminders ───────────────────────────────────────────────────────
st.subheader("📅 กำหนดการที่ใกล้ถึง")

df = get_upcoming_reminders(within_days) if DB_LIVE else get_mock_upcoming()

# Filter by type
reverse_label = {v: k for k, v in TYPE_LABEL.items()}
selected_types = [reverse_label.get(t, t) for t in filter_type]
if not df.empty and selected_types:
    df = df[df["reminder_type"].isin(selected_types)]

# ── Summary Stats ──
if not df.empty:
    overdue = len(df[df["days_remaining"] < 0])
    today_count = len(df[df["days_remaining"] == 0])
    soon_count = len(df[(df["days_remaining"] > 0) & (df["days_remaining"] <= 3)])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🔴 เลยกำหนด",  overdue)
    c2.metric("🔔 วันนี้",    today_count)
    c3.metric("⚠️ ภายใน 3 วัน", soon_count)
    c4.metric("📋 ทั้งหมด",   len(df))
    st.markdown("<br>", unsafe_allow_html=True)

# ── Render Cards ──
if df.empty:
    st.success("✨ ไม่มีกำหนดการในช่วงนี้")
else:
    for _, row in df.iterrows():
        card_cls, badge_cls, badge_txt = get_card_class(int(row["days_remaining"]))
        emoji = TYPE_EMOJI.get(row["reminder_type"], "📌")
        type_label = TYPE_LABEL.get(row["reminder_type"], row["reminder_type"])
        due_str = row["due_date"].strftime("%d/%m/%Y") if pd.notna(row["due_date"]) else "—"
        recurring_txt = f" · 🔄 ทุก {int(row['recurrence_days'])} วัน" if row.get("is_recurring") and row.get("recurrence_days") else ""
        desc_txt = f"<br><span style='color:#888;font-size:0.8rem'>📝 {row['description']}</span>" if pd.notna(row.get("description")) and row["description"] else ""

        col_card, col_btn = st.columns([8, 1])
        with col_card:
            st.markdown(f"""<div class="reminder-card {card_cls}">
<div class="r-icon">{emoji}</div>
<div class="r-body">
<div class="r-title">
{row['title']}
<span class="r-badge {badge_cls}">{badge_txt}</span>
</div>
<div class="r-meta">
🐱 {row['cat_name']} &nbsp;·&nbsp; 🏷️ {type_label}
&nbsp;·&nbsp; 📅 {due_str}{recurring_txt}
</div>
{desc_txt}
</div>
</div>""", unsafe_allow_html=True)

        with col_btn:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ เสร็จ", key=f"done_{row['id']}"):
                if DB_LIVE:
                    update_reminder_status(str(row["id"]), "done")
                st.success("บันทึกแล้ว!")
                st.rerun()

st.markdown("---")

# ─── History ─────────────────────────────────────────────────────────────────
st.subheader("📂 ประวัติที่ดำเนินการแล้ว")

if DB_LIVE:
    hist_df = get_reminder_history(20)
else:
    hist_df = pd.DataFrame([
        {"title": "เปลี่ยนทรายแมว", "cat_name": "ทั้งบ้าน", "reminder_type": "litter_change",
         "due_date": pd.Timestamp(date.today() - timedelta(days=14)), "status": "done", "notified_at": None},
        {"title": "ฉีดวัคซีน (ครั้งที่ 1)", "cat_name": "น้องสามสี", "reminder_type": "vaccine",
         "due_date": pd.Timestamp(date.today() - timedelta(days=30)), "status": "done", "notified_at": pd.Timestamp(date.today() - timedelta(days=31))},
    ])

if hist_df.empty:
    st.info("ยังไม่มีประวัติ")
else:
    STATUS_MAP = {"done": "✅ เสร็จแล้ว", "notified": "🔔 แจ้งเตือนแล้ว", "snoozed": "💤 เลื่อน"}
    hist_df["สถานะ"] = hist_df["status"].map(STATUS_MAP).fillna(hist_df["status"])
    hist_df["ประเภท"] = hist_df["reminder_type"].map(TYPE_LABEL).fillna(hist_df["reminder_type"])
    hist_df["วันที่กำหนด"] = pd.to_datetime(hist_df["due_date"]).dt.strftime("%d/%m/%Y")

    display_cols = ["วันที่กำหนด", "title", "cat_name", "ประเภท", "สถานะ"]
    rename_map = {"title": "หัวข้อ", "cat_name": "แมว"}
    st.dataframe(
        hist_df[display_cols].rename(columns=rename_map),
        use_container_width=True, hide_index=True,
    )
