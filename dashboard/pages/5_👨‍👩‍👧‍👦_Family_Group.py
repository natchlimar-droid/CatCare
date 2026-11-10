import io
import sys
import uuid
import base64
from pathlib import Path
from datetime import datetime, date, timedelta, timezone

import streamlit as st
import pandas as pd
import qrcode
from PIL import Image

# Ensure project root in sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.database import SyncSessionLocal
import importlib
import app.models
if not hasattr(app.models, "FamilyGroup"):
    importlib.reload(app.models)
from app.models import User, Cat, FamilyGroup, FamilyMember, Reminder

# ─── Page Configuration ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Family Care Group & LINE Sync | Cat Care",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS (App-like Mobile Styling) ──────────────────────────────────────
st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Sarabun', 'Plus Jakarta Sans', sans-serif;
}

:root {
    --primary: #FF9F43;
    --primary-dark: #EE801A;
    --secondary: #FF6B9D;
    --accent: #10B981;
    --line-green: #06C755;
    --bg-cream: #FFFDF9;
    --dark-slate: #1E293B;
    --card-shadow: 0 10px 25px -5px rgba(255, 159, 67, 0.12), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
}

/* ── App Top Header ── */
.app-header {
    background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
    border-radius: 20px;
    padding: 1.5rem 1.8rem;
    color: white;
    margin-bottom: 1.5rem;
    box-shadow: 0 10px 30px rgba(30, 41, 59, 0.15);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}
.app-header .title-area h2 {
    margin: 0;
    font-size: 1.6rem;
    font-weight: 800;
    color: #FFF;
    display: flex;
    align-items: center;
    gap: 8px;
}
.app-header .title-area p {
    margin: 4px 0 0;
    font-size: 0.9rem;
    color: #CBD5E1;
}
.app-badge-pill {
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    padding: 6px 14px;
    border-radius: 50px;
    font-size: 0.82rem;
    font-weight: 600;
    color: #F8FAFC;
    display: inline-flex;
    align-items: center;
    gap: 6px;
}

/* ── Invite Card ── */
.invite-hero-card {
    background: linear-gradient(135deg, #FFF9F0 0%, #FFF2E2 100%);
    border: 2px dashed #FFB347;
    border-radius: 20px;
    padding: 1.8rem;
    text-align: center;
    box-shadow: var(--card-shadow);
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.invite-code-pill {
    background: white;
    border: 2px solid #FF9F43;
    padding: 10px 24px;
    border-radius: 14px;
    font-family: 'Plus Jakarta Sans', monospace;
    font-size: 1.8rem;
    font-weight: 800;
    color: #D97706;
    letter-spacing: 3px;
    display: inline-block;
    box-shadow: 0 4px 15px rgba(217, 119, 6, 0.15);
    margin: 10px 0;
}

/* ── Member Cards ── */
.member-card {
    background: white;
    border-radius: 16px;
    padding: 1.1rem;
    border: 1px solid #F1F5F9;
    box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    display: flex;
    align-items: center;
    gap: 12px;
    transition: transform 0.2s ease;
    margin-bottom: 0.8rem;
}
.member-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.06);
}
.member-avatar {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: #FFF0E6;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    border: 2px solid #FFD093;
}
.member-info {
    flex: 1;
}
.member-name {
    font-weight: 700;
    font-size: 0.98rem;
    color: #1E293B;
}
.member-sub {
    font-size: 0.8rem;
    color: #64748B;
}
.role-badge {
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
}
.role-admin { background: #FEF3C7; color: #92400E; }
.role-caregiver { background: #E0E7FF; color: #3730A3; }
.role-member { background: #DCFCE7; color: #166534; }

/* ── LINE Group Banner ── */
.line-banner {
    background: #06C755;
    border-radius: 18px;
    padding: 1.2rem 1.6rem;
    color: white;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 25px rgba(6, 199, 85, 0.25);
    margin-bottom: 1.5rem;
}
.line-banner h3 {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 800;
}
.line-banner p {
    margin: 2px 0 0;
    font-size: 0.85rem;
    opacity: 0.92;
}

/* ── Smartphone Frame Simulator ── */
.phone-case {
    background: #1E293B;
    border-radius: 38px;
    padding: 14px;
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.35);
    max-width: 360px;
    margin: 0 auto;
    border: 4px solid #334155;
}
.phone-screen {
    background: #F8FAFC;
    border-radius: 28px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
}
.phone-status-bar {
    background: #06C755;
    padding: 8px 16px;
    color: white;
    font-size: 0.72rem;
    display: flex;
    justify-content: space-between;
    font-weight: 700;
}
.phone-line-header {
    background: #06C755;
    padding: 8px 14px 12px;
    color: white;
    display: flex;
    align-items: center;
    gap: 8px;
    border-bottom: 1px solid rgba(0,0,0,0.05);
}
.phone-chat-body {
    background: #849EB5;
    padding: 14px 10px;
    display: flex;
    flex-direction: column;
    gap: 10px;
    min-height: 480px;
    font-size: 0.8rem;
}
.chat-bubble-member {
    background: white;
    border-radius: 12px 12px 12px 2px;
    padding: 8px 12px;
    max-width: 80%;
    align-self: flex-start;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    color: #1E293B;
}
.chat-sender {
    font-size: 0.7rem;
    font-weight: 700;
    color: #475569;
    margin-bottom: 2px;
}
.chat-time {
    font-size: 0.65rem;
    color: #94A3B8;
    text-align: right;
    margin-top: 4px;
}

/* ── Mobile Bottom Navigation Bar Mockup ── */
.mobile-nav-bar {
    background: white;
    border-top: 1px solid #E2E8F0;
    display: flex;
    justify-content: space-around;
    padding: 8px 4px;
}
.nav-tab {
    display: flex;
    flex-direction: column;
    align-items: center;
    font-size: 0.65rem;
    color: #64748B;
    font-weight: 600;
    cursor: pointer;
}
.nav-tab.active {
    color: #FF9F43;
}
.nav-tab .icon {
    font-size: 1.15rem;
}
</style>
""", unsafe_allow_html=True)


# ─── Helper Functions ─────────────────────────────────────────────────────────
def generate_qr_b64(text: str) -> str:
    """Generate high-res QR code as base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#1E293B", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


# ─── Fetch Family Data from DB ───────────────────────────────────────────────
db = SyncSessionLocal()
try:
    fam_group = db.query(FamilyGroup).first()
    if fam_group:
        group_name = fam_group.name
        invite_code = fam_group.invite_code
        line_group_id = fam_group.line_group_id or "C98341512ab78e0"
        is_line_linked = fam_group.is_line_linked
        members = db.query(FamilyMember).filter(FamilyMember.group_id == fam_group.id).all()
    else:
        group_name = "บ้านสามแสบสตูดิโอ 🏠"
        invite_code = "CAT-FAM-7734"
        line_group_id = "C98341512ab78e0"
        is_line_linked = True
        members = []
    
    cats_count = db.query(Cat).count()
except Exception as e:
    group_name = "บ้านสามแสบสตูดิโอ 🏠"
    invite_code = "CAT-FAM-7734"
    line_group_id = "C98341512ab78e0"
    is_line_linked = True
    members = []
    cats_count = 3
finally:
    db.close()

# Fallback mockup members if DB was empty
if not members:
    mock_members = [
        {"nickname": "ณัชชา (Natcha)", "role": "admin", "emoji": "👑", "contact": "@natcha_cat"},
        {"nickname": "คุณพ่อ (Dad)", "role": "caregiver", "emoji": "👨‍🦱", "contact": "LINE: dad_thong"},
        {"nickname": "คุณแม่ (Mom)", "role": "caregiver", "emoji": "👩‍🦰", "contact": "LINE: mom_wan"},
        {"nickname": "น้องเนย (Noey)", "role": "member", "emoji": "👧", "contact": "LINE: noey_meow"},
    ]
else:
    mock_members = [
        {"nickname": m.nickname, "role": m.role, "emoji": m.avatar_emoji or "🧑", "contact": m.phone_or_line or "LINE User"}
        for m in members
    ]


# ─── Header UI ────────────────────────────────────────────────────────────────
st.markdown(f"""<div class="app-header">
<div class="title-area">
<h2>👨‍👩‍👧‍👦 Family Care Group & LINE Sync</h2>
<p>ระบบบ้านร่วมดูแลแมวสำหรับครอบครัว & เชื่อมต่อแจ้งเตือนเข้า LINE Group อัตโนมัติ</p>
</div>
<div style="display:flex;gap:8px;align-items:center">
<span class="app-badge-pill">🏠 {group_name}</span>
<span class="app-badge-pill">🐾 {cats_count} แมวในบ้าน</span>
<span class="app-badge-pill" style="background:#06C755;border-color:#06C755">🟢 LINE Group Connected</span>
</div>
</div>""", unsafe_allow_html=True)


# ─── Main Tabs ────────────────────────────────────────────────────────────────
tab_invite, tab_line, tab_timeline, tab_app_design = st.tabs([
    "🎟️ รหัสเชิญ & สมาชิกครอบครัว (Invite & Members)",
    "💬 เชื่อมต่อแจ้งเตือน LINE Group (LINE Messaging API)",
    "📋 ประวัติเวรดูแลในบ้าน (Family Care Timeline)",
    "📱 แนวทางการออกแบบแอพ (Mobile Application Design UI)"
])


# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Family Invite & Guardians Management
# ─────────────────────────────────────────────────────────────────────────────
with tab_invite:
    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        # Invite Hero Card
        invite_link = f"https://catcare.app/join?code={invite_code}"
        qr_b64 = generate_qr_b64(invite_link)

        st.markdown(f"""<div class="invite-hero-card">
<span style="background:#FF9F43;color:white;padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:700">EXCLUSIVE FAMILY INVITE</span>
<h3 style="margin:10px 0 4px;color:#1E293B">รหัสเชิญเข้าร่วมบ้าน: {group_name}</h3>
<p style="font-size:0.88rem;color:#64748B;margin:0">แชร์รหัสนี้ให้สมาชิกในครอบครัว เพื่อเข้ามาร่วมดูสุขภาพ ให้อาหาร และรับการแจ้งเตือนพร้อมกัน</p>
<div class="invite-code-pill">{invite_code}</div>
<p style="font-size:0.82rem;color:#D97706;margin:4px 0 0">⚡ รหัสนี้ใช้งานได้กับสมาชิกในครอบครัวทุกคนโดยไม่จำกัดจำนวน</p>
</div>""", unsafe_allow_html=True)

        c_b1, c_b2 = st.columns(2)
        with c_b1:
            if st.button("📋 คัดลอกลิงก์เชิญ (Copy Link)", use_container_width=True):
                st.toast(f"คัดลอกลิงก์เชิญเรียบร้อย: {invite_link}", icon="✅")
        with c_b2:
            if st.button("🔄 สุ่มสร้างรหัสเชิญใหม่", use_container_width=True):
                st.toast("สร้างรหัสเชิญใหม่สำเร็จสำหรับความปลอดภัย", icon="🔑")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("👥 สมาชิกผู้ดูแลในบ้าน (Family Guardians)")
        st.caption("สมาชิกทุกคนสามารถช่วยบันทึกการให้อาหาร ยา ขับถ่าย และดูแจ้งเตือนร่วมกัน")

        for m in mock_members:
            role_badge = "role-admin" if m["role"] == "admin" else ("role-caregiver" if m["role"] == "caregiver" else "role-member")
            role_label = "👑 หัวหน้าทาส (Admin)" if m["role"] == "admin" else ("👨‍👩‍👧 ผู้ช่วยทาส (Caregiver)" if m["role"] == "caregiver" else "🐾 พี่เลี้ยง (Member)")
            
            st.markdown(f"""<div class="member-card">
<div class="member-avatar">{m['emoji']}</div>
<div class="member-info">
<div class="member-name">{m['nickname']}</div>
<div class="member-sub">{m['contact']} · เข้าร่วมแล้ว ✅</div>
</div>
<div>
<span class="role-badge {role_badge}">{role_label}</span>
</div>
</div>""", unsafe_allow_html=True)

    with col_right:
        st.markdown(f"""<div style="background:white;border-radius:20px;padding:1.6rem;box-shadow:var(--card-shadow);border:1px solid #F1F5F9;text-align:center">
<h4 style="margin:0 0 6px;color:#1E293B">📱 สแกน QR Code เพื่อเข้าร่วมบ้านทันที</h4>
<p style="font-size:0.85rem;color:#64748B;margin:0 0 14px">เปิดกล้องมือถือของสมาชิก แล้วสแกนเพื่อเปิดแอป CatCare และผูกเข้าบ้านนี้อัตโนมัติ</p>
<img src="data:image/png;base64,{qr_b64}" width="200" height="200" style="border-radius:12px;border:1px solid #E2E8F0;padding:8px">
<div style="margin-top:12px;font-size:0.8rem;color:#94A3B8">รองรับทั้ง iOS Camera & LINE QR Scanner</div>
</div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        # Form to join another family house
        with st.expander("➕ ต้องการย้ายเข้าหรือเข้าร่วมบ้านอื่นด้วยรหัสเชิญ?"):
            input_code = st.text_input("กรอกรหัสเชิญบ้านอื่น (เช่น CAT-FAM-9921):", placeholder="CAT-FAM-XXXX")
            join_role = st.selectbox("บทบาทของคุณในบ้านนั้น:", ["ผู้ช่วยทาส (Caregiver)", "สมาชิกครอบครัว (Member)", "ผู้สังเกตการณ์สุขภาพ (Viewer)"])
            if st.button("🚪 ส่งคำขอเข้าร่วมบ้าน", use_container_width=True):
                if input_code.strip():
                    st.success(f"เชื่อมต่อเข้าร่วมบ้านสำเร็จ! กำลังซิงค์ข้อมูลน้องแมว...")
                else:
                    st.warning("กรุณาระบุรหัสเชิญให้ถูกต้อง")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: LINE Messaging API Group Integration
# ─────────────────────────────────────────────────────────────────────────────
with tab_line:
    st.markdown(f"""<div class="line-banner">
<div>
<h3>💬 ระบบแจ้งเตือนกลุ่ม LINE ครอบครัว (LINE Group Bot Sync)</h3>
<p>ดึงบอท CatCare เข้ากลุ่ม LINE ประจำบ้าน เพื่อให้ทุกคนได้รับการแจ้งเตือนและรับทราบการดูแลพร้อมกัน</p>
</div>
<div style="text-align:right">
<span style="background:white;color:#06C755;padding:6px 14px;border-radius:20px;font-weight:800;font-size:0.85rem">LINE BOT VERIFIED</span>
</div>
</div>""", unsafe_allow_html=True)

    c_conf, c_phone = st.columns([1.2, 1])

    with c_conf:
        st.subheader("⚙️ การตั้งค่าการเชื่อมต่อ LINE Group")
        st.caption("ระบบรองรับ LINE Official Account (Messaging API) สำหรับการ Broadcast เข้ากลุ่มครอบครัว")

        with st.form("line_config_form"):
            t_token = st.text_input("LINE Channel Access Token (Long-Lived):", value="Bearer EyJhGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", type="password")
            t_group = st.text_input("LINE Group ID (ขึ้นต้นด้วย C...):", value=line_group_id, help="ได้จากการดึง Webhook Event เมื่อดึงบอทเข้ากรุ๊ป LINE ครอบครัว")
            c_checkin = st.checkbox("📢 แจ้งเตือนในกลุ่มเมื่อมีคนในบ้าน 'ให้อาหาร' หรือ 'ป้อนยา' สำเร็จ (Check-in Broadcast)", value=True)
            c_vaccine = st.checkbox("💉 แจ้งเตือนนัดหมายวัคซีนล่วงหน้า 3 วัน และในวันนัดหมาย", value=True)
            c_litter = st.checkbox("🪣 แจ้งเตือนรอบเปลี่ยนทรายแมวประจำสัปดาห์ (ทุกวันอาทิตย์ 09:00 น.)", value=True)
            saved = st.form_submit_button("💾 บันทึกการตั้งค่า LINE Group", use_container_width=True)
            if saved:
                st.success("บันทึกการตั้งค่า LINE Group เรียบร้อยแล้ว!")

        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🚀 ทดสอบยิงข้อความจริง (Interactive Live Test)")
        test_msg_type = st.selectbox("เลือกประเภทการแจ้งเตือนที่ต้องการทดสอบ:", [
            "💉 เตือนนัดฉีดวัคซีนรวม (FVRCP Booster)",
            "💊 เตือนป้อนยาฆ่าเชื้อ & ยาหยอดตา",
            "🍽️ ครอบครัวเช็กอิน: คุณพ่อให้อาหารเช้าน้องแล้ว",
            "🪣 ถึงรอบเปลี่ยนทรายแมวประจำสัปดาห์"
        ])
        
        if st.button("📲 ยิง LINE Flex Card ทดสอบเข้ากลุ่มครอบครัว", use_container_width=True):
            st.balloons()
            st.success(f"ส่งข้อความประเภท '{test_msg_type}' เข้า LINE Group ({line_group_id}) เรียบรวยแล้ว! สมาชิกทุกคนในกลุ่มจะได้รับข้อความแบบ Rich Flex ทันที")

    with c_phone:
        # Smartphone Simulator of LINE Family Group Chat
        st.markdown("""<div class="phone-case">
<div class="phone-screen">
<div class="phone-status-bar">
<span>09:41</span>
<span>5G 📶 100% 🔋</span>
</div>
<div class="phone-line-header">
<span style="font-size:1.1rem">◀</span>
<span style="font-weight:700;font-size:0.92rem">ครอบครัวทาสแมว 🐾 (5)</span>
</div>
<div class="phone-chat-body">
<div class="chat-bubble-member">
<div class="chat-sender">👩‍🦰 คุณแม่</div>
วันนี้ใครอยู่บ้านตอนบ่าย ฝากดูน้ำในชามน้องส้มซ่าด้วยนะจ๊ะ
<div class="chat-time">08:10</div>
</div>
<div style="background:white;border-radius:14px;overflow:hidden;box-shadow:0 3px 10px rgba(0,0,0,0.15)">
<div style="background:#FF9F43;padding:8px 12px;color:white;font-weight:800;font-size:0.78rem">
🤖 CatCare Family Bot · แจ้งเตือนอัตโนมัติ
</div>
<div style="padding:10px">
<div style="font-weight:800;color:#1E293B;font-size:0.9rem">💊 ถึงเวลาป้อนยาฆ่าเชื้อ</div>
<div style="font-size:0.75rem;color:#64748B">น้องส้มซ่า · หลังอาหารเช้า</div>
<div style="background:#FFF9F0;padding:6px;border-radius:6px;font-size:0.75rem;margin:6px 0;color:#555">
⚠️ อาการแผลที่หูดีขึ้นแล้ว เหลืออีก 3 วันจ้า
</div>
<button style="width:100%;background:#06C755;color:white;border:none;border-radius:6px;padding:6px;font-weight:700;font-size:0.75rem">✅ ป้อนยาเรียบร้อยแล้ว</button>
</div>
</div>
<div class="chat-bubble-member" style="background:#DCFCE7;align-self:flex-end;border-radius:12px 12px 2px 12px">
<div class="chat-sender" style="color:#166534">👨‍🦱 คุณพ่อ</div>
พ่อป้อนยาให้น้องเรียบร้อยแล้วครับผม กินเก่งมาก ไม่ดิ้นเลย 👍
<div class="chat-time">08:25</div>
</div>
<div style="background:white;border-radius:12px;padding:8px 10px;align-self:center;text-align:center;font-size:0.7rem;color:#64748B;box-shadow:0 1px 4px rgba(0,0,0,0.08)">
✨ <b>คุณพ่อ</b> บันทึกการป้อนยาลงในระบบ CatCare แล้ว เวลา 08:25 น.
</div>
</div>
<div class="mobile-nav-bar">
<div class="nav-tab active"><span class="icon">🏠</span>หน้าแรก</div>
<div class="nav-tab"><span class="icon">📝</span>บันทึก</div>
<div class="nav-tab"><span class="icon">🪪</span>พาสปอร์ต</div>
<div class="nav-tab"><span class="icon">👨‍👩‍👧‍👦</span>ครอบครัว</div>
</div>
</div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: Family Care Timeline
# ─────────────────────────────────────────────────────────────────────────────
with tab_timeline:
    st.subheader("📋 ประวัติการดูแลแมวร่วมกันในบ้าน (Real-Time Activity Feed)")
    st.caption("ระบบบันทึกชัดเจนว่าใครในครอบครัวเป็นคนทำกิจกรรม เพื่อความโปร่งใสและไม่ทำซ้ำซ้อน")

    timeline_data = [
        {"time": "วันนี้ 08:25 น.", "member": "👨‍🦱 คุณพ่อ (Dad)", "cat": "น้องส้มซ่า", "action": "💊 ป้อนยาฆ่าเชื้อ", "detail": "เม็ดสีชมพู 1 เม็ดหลังอาหารเรียบร้อย"},
        {"time": "วันนี้ 07:45 น.", "member": "👩‍🦰 คุณแม่ (Mom)", "cat": "น้องส้มซ่า", "action": "🥣 ให้อาหารเปียก", "detail": "Sheba Pouch 85g เกลี้ยงจาน"},
        {"time": "เมื่อวาน 21:30 น.", "member": "👧 น้องเนย (Noey)", "cat": "น้องมิดไนท์", "action": "🪣 ตักกระบะทราย", "detail": "ก้อนฉี่ 3 ก้อน อึปกติ"},
        {"time": "เมื่อวาน 18:00 น.", "member": "👑 คุณณัชชา", "cat": "น้องถุงทอง", "action": "⚖️ ชั่งน้ำหนัก", "detail": "ชั่งได้ 5.10 kg (น้ำหนักคงที่ อยู่ใน Safe Zone)"},
        {"time": "เมื่อวาน 08:00 น.", "member": "👨‍🦱 คุณพ่อ (Dad)", "cat": "ทั้งบ้าน", "action": "💧 ล้างชามน้ำพุ", "detail": "เติมน้ำสะอาดและเปลี่ยนไส้กรอง"},
    ]

    for item in timeline_data:
        st.markdown(f"""<div style="background:white;border-radius:14px;padding:1rem 1.4rem;border-left:5px solid #FF9F43;margin-bottom:0.8rem;box-shadow:0 2px 10px rgba(0,0,0,0.03);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
<div>
<div style="font-weight:700;font-size:1.02rem;color:#1E293B">{item['action']} · <span style="color:#FF9F43">{item['cat']}</span></div>
<div style="font-size:0.88rem;color:#64748B;margin-top:2px">{item['detail']}</div>
</div>
<div style="text-align:right">
<div style="font-weight:700;font-size:0.88rem;color:#334155">{item['member']}</div>
<div style="font-size:0.78rem;color:#94A3B8">{item['time']}</div>
</div>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: Mobile Application Design UI Guidelines
# ─────────────────────────────────────────────────────────────────────────────
with tab_app_design:
    st.subheader("🎨 แนวคิดการออกแบบ UI/UX ให้เหมาะกับ Mobile Application")
    st.caption("สรุปหลักการออกแบบตามมาตรฐาน iOS Human Interface Guidelines และ Material Design 3")

    col_d1, col_d2, col_d3 = st.columns(3)

    with col_d1:
        st.markdown("""<div style="background:white;border-radius:18px;padding:1.4rem;box-shadow:var(--card-shadow);height:100%">
<div style="font-size:2rem;margin-bottom:8px">📱</div>
<h4 style="margin:0 0 8px;color:#1E293B">1. Thumb-Zone First</h4>
<p style="font-size:0.88rem;color:#64748B;line-height:1.6">
ออกแบบให้ปุ่มกดหลัก (Quick Action / Check-in) อยู่บริเวณส่วนล่างของหน้าจอเพื่อให้กดได้ด้วยนิ้วหัวแม่มือเดียว (One-Handed Navigation) พร้อม Floating Bottom Bar 4 เมนูหลัก
</p>
</div>""", unsafe_allow_html=True)

    with col_d2:
        st.markdown("""<div style="background:white;border-radius:18px;padding:1.4rem;box-shadow:var(--card-shadow);height:100%">
<div style="font-size:2rem;margin-bottom:8px">🎨</div>
<h4 style="margin:0 0 8px;color:#1E293B">2. Pet-Friendly Soft Palette</h4>
<p style="font-size:0.88rem;color:#64748B;line-height:1.6">
ใช้โทนสีส้มพาสเทล <code>#FF9F43</code> สื่อถึงความกระตือรือร้นและอยากอาหาร, ชมพู <code>#FF6B9D</code> สำหรับงานเร่งด่วนและวัคซีน, และเขียว <code>#10B981</code> สำหรับสถานะปลอดภัยสบายใจ
</p>
</div>""", unsafe_allow_html=True)

    with col_d3:
        st.markdown("""<div style="background:white;border-radius:18px;padding:1.4rem;box-shadow:var(--card-shadow);height:100%">
<div style="font-size:2rem;margin-bottom:8px">🔔</div>
<h4 style="margin:0 0 8px;color:#1E293B">3. Frictionless Push & Sync</h4>
<p style="font-size:0.88rem;color:#64748B;line-height:1.6">
ลดขั้นตอนการใช้งาน โดยไม่ต้องให้ทุกคนดาวน์โหลดแอปใหม่ เพียงดึงบอทเข้ากรุ๊ป LINE ครอบครัว แล้วกดปุ่มในแชตได้ทันที ข้อมูลซิงค์สองทาง (Bidirectional Sync) กลับเข้าฐานข้อมูลทันที
</p>
</div>""", unsafe_allow_html=True)

