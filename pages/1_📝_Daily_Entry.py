"""
🐱 Cat Care — Daily Entry Page
================================
หน้าบันทึกข้อมูลประจำวัน
โทนสี: Warm Cozy (#FF9F43 / #F7F1E3 / #2C3E50)
"""

import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
import random

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="บันทึกประจำวัน | Cat Care",
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Warm Cozy CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Prompt:wght@400;600;700&display=swap');

/* ── Root Variables ── */
:root {
    --primary:   #FF9F43;
    --primary-lt:#FFF3E0;
    --cream:     #F7F1E3;
    --dark:      #2C3E50;
    --dark-lt:   #34495E;
    --green:     #A8E6CF;
    --red:       #FF6B9D;
    --yellow:    #FFD93D;
    --purple:    #C3A9D1;
    --card-bg:   #FFFAF4;
    --shadow:    0 4px 20px rgba(255,159,67,0.12);
    --radius:    16px;
}

/* ── Global ── */
html, body, [class*="css"], .stApp {
    font-family: 'Sarabun', sans-serif !important;
    background: linear-gradient(135deg, #FFF8F0 0%, #F7F1E3 100%) !important;
    color: var(--dark) !important;
}
.block-container { padding: 1.5rem 2rem 3rem 2rem !important; max-width: 900px; }
h1,h2,h3 { font-family: 'Prompt', sans-serif !important; color: var(--dark) !important; }
.stMarkdown hr { border-color: rgba(255,159,67,0.2); }

/* ── Cat Profile Header ── */
.cat-header {
    background: linear-gradient(135deg, var(--primary) 0%, #FFB347 100%);
    border-radius: var(--radius);
    padding: 1.5rem 2rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow);
}
.cat-avatar {
    width: 90px; height: 90px;
    border-radius: 50%;
    border: 4px solid rgba(255,255,255,0.6);
    font-size: 3rem;
    display: flex; align-items: center; justify-content: center;
    background: rgba(255,255,255,0.25);
    backdrop-filter: blur(8px);
    flex-shrink: 0;
}
.cat-info h2 { color: white !important; margin: 0; font-size: 1.6rem; }
.cat-info p  { color: rgba(255,255,255,0.88); margin: 0.2rem 0; font-size: 0.95rem; }
.cat-badge {
    display: inline-block;
    background: rgba(255,255,255,0.25);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.82rem;
    color: white;
    margin-right: 6px;
    margin-top: 6px;
}

/* ── Section Title ── */
.section-title {
    font-family: 'Prompt', sans-serif;
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--dark);
    margin: 1.4rem 0 0.8rem 0;
    display: flex; align-items: center; gap: 8px;
}
.section-title::after {
    content: '';
    flex: 1;
    height: 2px;
    background: linear-gradient(to right, var(--primary), transparent);
    border-radius: 2px;
    margin-left: 8px;
}

/* ── Quick Action Buttons ── */
.action-btn {
    background: var(--card-bg);
    border: 2px solid transparent;
    border-radius: var(--radius);
    padding: 1.4rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.25s ease;
    box-shadow: var(--shadow);
    height: 100%;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center; gap: 0.5rem;
}
.action-btn:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 28px rgba(255,159,67,0.22);
    border-color: var(--primary);
}
.action-btn .btn-icon  { font-size: 2.6rem; }
.action-btn .btn-label { font-weight: 600; font-size: 0.95rem; color: var(--dark); }
.action-btn .btn-sub   { font-size: 0.78rem; color: #888; }
.btn-food   { border-top: 4px solid #FF9F43; }
.btn-expense{ border-top: 4px solid #FF6B9D; }
.btn-weight { border-top: 4px solid #A8E6CF; }

/* ── Reminder Cards ── */
.reminder-scroll {
    display: flex; gap: 1rem;
    overflow-x: auto; padding-bottom: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: #FFD093 transparent;
}
.reminder-card {
    min-width: 220px; max-width: 220px;
    border-radius: var(--radius);
    padding: 1.1rem 1.2rem;
    flex-shrink: 0;
    box-shadow: 0 3px 14px rgba(0,0,0,0.07);
    position: relative;
}
.reminder-card .r-icon  { font-size: 1.8rem; margin-bottom: 0.4rem; }
.reminder-card .r-title { font-weight: 700; font-size: 0.9rem; color: var(--dark); margin-bottom: 0.2rem; }
.reminder-card .r-sub   { font-size: 0.78rem; color: #666; }
.reminder-card .r-badge {
    position: absolute; top: 10px; right: 12px;
    border-radius: 20px; padding: 2px 10px;
    font-size: 0.72rem; font-weight: 600;
}
.card-yellow { background: #FFFDE7; border-left: 4px solid #FFD93D; }
.card-red    { background: #FFF0F4; border-left: 4px solid #FF6B9D; }
.card-green  { background: #F0FFF8; border-left: 4px solid #A8E6CF; }
.badge-yellow{ background: #FFD93D; color: #5A4A00; }
.badge-red   { background: #FF6B9D; color: white; }
.badge-green { background: #A8E6CF; color: #1A5C3A; }

/* ── Recent Log Table ── */
.log-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 6px;
}
.log-table th {
    background: #2C3E50;
    color: white;
    padding: 10px 14px;
    font-size: 0.82rem;
    font-weight: 600;
    text-align: left;
}
.log-table th:first-child { border-radius: 10px 0 0 10px; }
.log-table th:last-child  { border-radius: 0 10px 10px 0; }
.log-table td {
    background: var(--card-bg);
    padding: 10px 14px;
    font-size: 0.85rem;
    color: var(--dark);
}
.log-table tr td:first-child { border-radius: 10px 0 0 10px; }
.log-table tr td:last-child  { border-radius: 0 10px 10px 0; }
.log-table tr:hover td { background: #FFF3E0; }
.type-chip {
    display: inline-block; border-radius: 12px;
    padding: 2px 10px; font-size: 0.75rem; font-weight: 600;
}

/* ── Dialog / Form Styling ── */
[data-testid="stForm"] {
    background: var(--card-bg);
    border-radius: var(--radius);
    padding: 1rem;
    border: 1px solid rgba(255,159,67,0.2);
}
.stButton button {
    background: linear-gradient(135deg, var(--primary), #FFB347) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    padding: 0.5rem 1.5rem !important;
    transition: all 0.2s !important;
}
.stButton button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(255,159,67,0.4) !important;
}
div[data-testid="stMetricValue"] { color: var(--primary) !important; font-size: 1.6rem !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: var(--cream) !important; }
</style>
""", unsafe_allow_html=True)

# ─── Session State ─────────────────────────────────────────────────────────────
if "log_entries" not in st.session_state:
    now = datetime.now()
    st.session_state.log_entries = [
        {"เวลา": (now - timedelta(hours=6)).strftime("%d/%m %H:%M"), "ประเภท": "🍽️ กินอาหาร",  "รายละเอียด": "Sheba Wet 85g",        "แมว": "น้องสามสี"},
        {"เวลา": (now - timedelta(hours=5)).strftime("%d/%m %H:%M"), "ประเภท": "⚖️ น้ำหนัก",   "รายละเอียด": "4.35 kg",              "แมว": "น้องสามสี"},
        {"เวลา": (now - timedelta(hours=4)).strftime("%d/%m %H:%M"), "ประเภท": "💩 ขับถ่าย",   "รายละเอียด": "ปกติ (ปัสสาวะ)",       "แมว": "น้องสามสี"},
        {"เวลา": (now - timedelta(hours=2)).strftime("%d/%m %H:%M"), "ประเภท": "🍽️ กินอาหาร",  "รายละเอียด": "Royal Canin Dry 50g",  "แมว": "น้องสามสี"},
        {"เวลา": (now - timedelta(hours=1)).strftime("%d/%m %H:%M"), "ประเภท": "💸 ค่าใช้จ่าย", "รายละเอียด": "ค่าอาหาร ฿320",        "แมว": "น้องสามสี"},
    ]

# ─── Dialogs ──────────────────────────────────────────────────────────────────
@st.dialog("🍽️ บันทึกการกินอาหาร")
def dialog_eating():
    st.markdown("กรอกข้อมูลมื้ออาหารของน้อง")
    with st.form("form_eating"):
        col1, col2 = st.columns(2)
        with col1:
            food_brand = st.text_input("ยี่ห้ออาหาร", placeholder="เช่น Sheba, Royal Canin")
        with col2:
            food_type = st.selectbox("ประเภทอาหาร", ["🥣 อาหารเปียก (Wet)", "🌾 อาหารแห้ง (Dry)", "🍬 ขนม (Treat)"])
        food_amount = st.slider("ปริมาณอาหาร (กรัม)", 10, 300, 85, step=5)
        meal_time = st.time_input("เวลาที่กิน", datetime.now().time())
        notes = st.text_area("หมายเหตุ", placeholder="เช่น กินหมดจาน / กินแค่ครึ่งถ้วย", height=70)
        submitted = st.form_submit_button("✅ บันทึก", use_container_width=True)
        if submitted:
            entry = {
                "เวลา": datetime.now().strftime("%d/%m %H:%M"),
                "ประเภท": "🍽️ กินอาหาร",
                "รายละเอียด": f"{food_brand or 'ไม่ระบุ'} {food_amount}g",
                "แมว": "น้องสามสี",
            }
            st.session_state.log_entries.insert(0, entry)
            st.success(f"บันทึกแล้ว! {food_brand} {food_amount}g")
            st.rerun()


@st.dialog("💸 บันทึกค่าใช้จ่าย")
def dialog_expense():
    st.markdown("กรอกรายการค่าใช้จ่ายสำหรับน้องแมว")
    with st.form("form_expense"):
        categories = {
            "🍽️ ค่าอาหาร": "food",
            "🏥 ค่าหมอ": "vet",
            "🪣 ค่าทราย": "litter",
            "💊 ค่ายา": "medicine",
            "🎾 ค่าของเล่น": "toy",
            "📦 อื่นๆ": "other",
        }
        col1, col2 = st.columns(2)
        with col1:
            category = st.selectbox("หมวดหมู่", list(categories.keys()))
        with col2:
            amount = st.number_input("จำนวนเงิน (บาท)", min_value=0.0, step=10.0, format="%.2f")
        description = st.text_input("รายละเอียด", placeholder="เช่น ตรวจสุขภาพประจำปี")
        expense_date = st.date_input("วันที่", date.today())
        submitted = st.form_submit_button("✅ บันทึก", use_container_width=True)
        if submitted:
            if amount <= 0:
                st.error("กรุณากรอกจำนวนเงิน")
            else:
                entry = {
                    "เวลา": datetime.now().strftime("%d/%m %H:%M"),
                    "ประเภท": "💸 ค่าใช้จ่าย",
                    "รายละเอียด": f"{category} ฿{amount:,.0f}",
                    "แมว": "น้องสามสี",
                }
                st.session_state.log_entries.insert(0, entry)
                st.success(f"บันทึกแล้ว! {category} ฿{amount:,.2f}")
                st.rerun()


@st.dialog("⚖️ บันทึกน้ำหนัก / การขับถ่าย")
def dialog_weight_litter():
    st.markdown("บันทึกน้ำหนักตัวหรือสถานะการขับถ่าย")
    tab1, tab2 = st.tabs(["⚖️ น้ำหนักตัว", "💩 การขับถ่าย"])
    with tab1:
        with st.form("form_weight"):
            weight = st.number_input("น้ำหนัก (kg)", min_value=0.5, max_value=15.0,
                                     value=4.35, step=0.05, format="%.2f")
            notes = st.text_input("หมายเหตุ", placeholder="เช่น ชั่งเช้าก่อนอาหาร")
            submitted = st.form_submit_button("✅ บันทึกน้ำหนัก", use_container_width=True)
            if submitted:
                entry = {
                    "เวลา": datetime.now().strftime("%d/%m %H:%M"),
                    "ประเภท": "⚖️ น้ำหนัก",
                    "รายละเอียด": f"{weight:.2f} kg",
                    "แมว": "น้องสามสี",
                }
                st.session_state.log_entries.insert(0, entry)
                st.success(f"บันทึกน้ำหนัก {weight:.2f} kg แล้ว!")
                st.rerun()
    with tab2:
        with st.form("form_litter"):
            litter_type = st.radio("ประเภท", ["🚽 ปัสสาวะ (Urine)", "💩 อุจจาระ (Feces)", "ทั้งคู่"])
            litter_notes = st.text_area("สังเกตพฤติกรรม", placeholder="เช่น ปกติดี / มีเลือด / ถ่ายยาก", height=80)
            submitted2 = st.form_submit_button("✅ บันทึกการขับถ่าย", use_container_width=True)
            if submitted2:
                entry = {
                    "เวลา": datetime.now().strftime("%d/%m %H:%M"),
                    "ประเภท": "💩 ขับถ่าย",
                    "รายละเอียด": litter_type.split(" ")[1],
                    "แมว": "น้องสามสี",
                }
                st.session_state.log_entries.insert(0, entry)
                st.success("บันทึกการขับถ่ายแล้ว!")
                st.rerun()


# ════════════════════════════════════════════════════════
#  UI START
# ════════════════════════════════════════════════════════

# ─── Cat Profile Header ───────────────────────────────────────────────────────
today_str = date.today().strftime("%A, %d %B %Y")
st.markdown(f"""
<div class="cat-header">
    <div class="cat-avatar">🐱</div>
    <div class="cat-info">
        <h2>น้องสามสี 🐾</h2>
        <p>Mixed Breed · เพศเมีย · 2 ปี 3 เดือน</p>
        <div>
            <span class="cat-badge">⚖️ 4.35 kg</span>
            <span class="cat-badge">📅 {date.today().strftime("%d/%m/%Y")}</span>
            <span class="cat-badge">💉 วัคซีนครบ</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─── Quick Action Buttons ─────────────────────────────────────────────────────
st.markdown('<div class="section-title">⚡ บันทึกด่วน</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="action-btn btn-food">
        <div class="btn-icon">🍽️</div>
        <div class="btn-label">บันทึกการกิน</div>
        <div class="btn-sub">อาหาร / ขนม / น้ำ</div>
    </div>""", unsafe_allow_html=True)
    if st.button("➕ กินอาหาร", key="btn_eat", use_container_width=True):
        dialog_eating()

with col2:
    st.markdown("""
    <div class="action-btn btn-expense">
        <div class="btn-icon">💸</div>
        <div class="btn-label">บันทึกค่าใช้จ่าย</div>
        <div class="btn-sub">อาหาร / หมอ / ทราย</div>
    </div>""", unsafe_allow_html=True)
    if st.button("➕ ค่าใช้จ่าย", key="btn_expense", use_container_width=True):
        dialog_expense()

with col3:
    st.markdown("""
    <div class="action-btn btn-weight">
        <div class="btn-icon">⚖️</div>
        <div class="btn-label">น้ำหนัก / ขับถ่าย</div>
        <div class="btn-sub">ชั่งน้ำหนัก / เช็กกระบะ</div>
    </div>""", unsafe_allow_html=True)
    if st.button("➕ น้ำหนัก / 💩", key="btn_weight", use_container_width=True):
        dialog_weight_litter()

# ─── Upcoming Reminders ───────────────────────────────────────────────────────
st.markdown('<div class="section-title">🔔 กำหนดการเร็วๆ นี้</div>', unsafe_allow_html=True)
st.markdown("""
<div class="reminder-scroll">

    <div class="reminder-card card-yellow">
        <div class="r-icon">🪣</div>
        <span class="r-badge badge-yellow">อีก 2 วัน</span>
        <div class="r-title">เปลี่ยนทรายแมว</div>
        <div class="r-sub">17 ก.ค. 2569 · ทั้งบ้าน</div>
        <div class="r-sub" style="margin-top:4px">Unicharm Dual Power</div>
    </div>

    <div class="reminder-card card-red">
        <div class="r-icon">💉</div>
        <span class="r-badge badge-red">20 ก.ค.</span>
        <div class="r-title">นัดฉีดวัคซีนรวม</div>
        <div class="r-sub">20 ก.ค. 2569 · น้องสามสี</div>
        <div class="r-sub" style="margin-top:4px">FVRCP Booster ครั้งที่ 2</div>
    </div>

    <div class="reminder-card card-green">
        <div class="r-icon">💊</div>
        <span class="r-badge badge-green">อีก 7 วัน</span>
        <div class="r-title">ยาถ่ายพยาธิ</div>
        <div class="r-sub">22 ก.ค. 2569 · น้องสามสี</div>
        <div class="r-sub" style="margin-top:4px">Drontal ครั้งที่ 1</div>
    </div>

    <div class="reminder-card card-yellow">
        <div class="r-icon">✂️</div>
        <span class="r-badge badge-yellow">อีก 10 วัน</span>
        <div class="r-title">ตัดเล็บ</div>
        <div class="r-sub">25 ก.ค. 2569 · น้องสามสี</div>
        <div class="r-sub" style="margin-top:4px">ทุก 4 สัปดาห์</div>
    </div>

</div>
""", unsafe_allow_html=True)

# ─── Recent Log ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">📋 ประวัติการบันทึกล่าสุด</div>', unsafe_allow_html=True)

TYPE_COLORS = {
    "🍽️ กินอาหาร":  ("background:#FFF3E0;color:#E65100", "🍽️"),
    "⚖️ น้ำหนัก":   ("background:#E8F5E9;color:#1B5E20", "⚖️"),
    "💩 ขับถ่าย":   ("background:#FFF9C4;color:#F57F17", "💩"),
    "💸 ค่าใช้จ่าย":("background:#FCE4EC;color:#880E4F", "💸"),
}

recent = st.session_state.log_entries[:5]

rows_html = ""
for entry in recent:
    t = entry["ประเภท"]
    style, _ = TYPE_COLORS.get(t, ("background:#f5f5f5;color:#333", "📌"))
    rows_html += f"""
    <tr>
        <td><b>{entry['เวลา']}</b></td>
        <td><span class="type-chip" style="{style}">{t}</span></td>
        <td>{entry['รายละเอียด']}</td>
        <td>{entry['แมว']}</td>
    </tr>"""

st.markdown(f"""
<table class="log-table">
    <thead>
        <tr>
            <th>🕐 เวลา</th>
            <th>ประเภท</th>
            <th>รายละเอียด</th>
            <th>แมว</th>
        </tr>
    </thead>
    <tbody>{rows_html}</tbody>
</table>
""", unsafe_allow_html=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.caption("🐾 Cat Care · ข้อมูลถูกบันทึกเฉพาะ Session นี้ — เชื่อมต่อ Database จริงก่อน Production")
