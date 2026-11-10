"""
dashboard/pages/0_🔐_Login.py
───────────────────────────────
หน้าเข้าสู่ระบบและสมัครสมาชิกสำหรับ Cat Care Dashboard
รองรับทั้ง Demo Login อัตโนมัติและ User Authentication จริง
"""

import os
import sys
import uuid
import streamlit as st
from datetime import datetime, timezone

# ── Ensure project root (CatCare/) is on sys.path ──
_pages_dir   = os.path.dirname(__file__)     # dashboard/pages/
_dash_dir    = os.path.dirname(_pages_dir)   # dashboard/
_project_dir = os.path.dirname(_dash_dir)    # CatCare/
for _p in (_dash_dir, _project_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from app.database import SyncSessionLocal
from app.models import User, Cat
from app.routers.auth import verify_password, hash_password

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="เข้าสู่ระบบ | Cat Care",
    page_icon="🔐",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ─── Warm Cozy CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Prompt:wght@600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Sarabun', sans-serif !important;
    background: linear-gradient(135deg, #FFF8F0 0%, #F7F1E3 100%) !important;
}
h1, h2, h3 { font-family: 'Prompt', sans-serif !important; color: #2C3E50 !important; }
.login-header {
    text-align: center;
    padding: 1.5rem 0 1rem;
}
.login-header h1 {
    font-size: 2.2rem;
    color: #FF9F43 !important;
    margin-bottom: 0.2rem;
}
.login-header p {
    color: #666;
    font-size: 0.95rem;
}
.user-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.06);
    border-left: 5px solid #FF9F43;
    margin-bottom: 1.2rem;
}
.stButton button {
    background: linear-gradient(135deg, #FF9F43, #FFB347) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    height: 44px;
}
.demo-box {
    background: #FFF9E6;
    border: 1px dashed #FFD93D;
    border-radius: 12px;
    padding: 12px 16px;
    margin-bottom: 1.2rem;
    font-size: 0.88rem;
    color: #665000;
}
</style>
""", unsafe_allow_html=True)

# ─── State Management ─────────────────────────────────────────────────────────
if "user" not in st.session_state:
    st.session_state["user"] = None

# Header
st.markdown("""<div class="login-header">
<h1>🐱 Cat Care</h1>
<p>ระบบจัดการสุขภาพและบันทึกกิจกรรมน้องแมว</p>
</div>""", unsafe_allow_html=True)

# ─── Already Logged In View ───────────────────────────────────────────────────
if st.session_state["user"] is not None:
    u = st.session_state["user"]
    st.markdown(f"""<div class="user-card">
<h3>👋 ยินดีต้อนรับ, {u['display_name']}!</h3>
<p style="margin: 4px 0; color:#555">👤 <b>ชื่อผู้ใช้:</b> {u['username']}</p>
<p style="margin: 4px 0; color:#555">📧 <b>อีเมล:</b> {u['email']}</p>
<p style="margin: 4px 0; color:#555">✨ <b>สถานะ:</b> เข้าสู่ระบบเรียบร้อยแล้ว (Session Active)</p>
</div>""", unsafe_allow_html=True)

    # ดึงแมวของ User คนนี้
    db = SyncSessionLocal()
    try:
        user_cats = db.query(Cat).filter(Cat.owner_id == uuid.UUID(u["id"])).all()
        if user_cats:
            st.markdown("#### 🐾 น้องแมวของคุณ:")
            cat_cols = st.columns(min(len(user_cats), 3))
            for i, cat in enumerate(user_cats):
                with cat_cols[i % 3]:
                    st.info(f"🐱 **{cat.name}**\n\nพันธุ์: {cat.breed or '—'}\n\nเพศ: {cat.gender}")
        else:
            st.caption("ยังไม่มีข้อมูลแมวที่ผูกกับบัญชีนี้")
    except Exception as e:
        pass
    finally:
        db.close()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 ไปที่ Analytics Dashboard", use_container_width=True):
            st.switch_page("dashboard.py")
    with col2:
        if st.button("🚪 ออกจากระบบ (Logout)", use_container_width=True):
            st.session_state["user"] = None
            st.rerun()

    st.stop()


# ─── Tabs: เข้าสู่ระบบ / สมัครสมาชิก ──────────────────────────────────────────
tab_login, tab_register = st.tabs(["🔐 เข้าสู่ระบบ (Login)", "📝 สมัครสมาชิก (Register)"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: เข้าสู่ระบบ
# ─────────────────────────────────────────────────────────────────────────────
with tab_login:
    st.markdown("""<div class="demo-box">
💡 <b>ข้อมูลทดสอบสำหรับ Portfolio / Showcase:</b><br>
ชื่อผู้ใช้: <code>demo_user</code> | รหัสผ่าน: <code>demo1234</code>
</div>""", unsafe_allow_html=True)

    # ปุ่มกรอก Demo ทันที
    if st.button("⚡ กดปุ่มนี้เพื่อกรอกข้อมูล Demo อัตโนมัติ", use_container_width=True):
        st.session_state["fill_username"] = "demo_user"
        st.session_state["fill_password"] = "demo1234"
        st.rerun()

    init_user = st.session_state.get("fill_username", "")
    init_pass = st.session_state.get("fill_password", "")

    with st.form("login_form"):
        username = st.text_input("ชื่อผู้ใช้ (Username):", value=init_user, placeholder="เช่น demo_user")
        password = st.text_input("รหัสผ่าน (Password):", value=init_pass, type="password", placeholder="กรอกรหัสผ่าน...")
        submit = st.form_submit_button("🐾 เข้าสู่ระบบ", use_container_width=True)

    if submit:
        if not username.strip() or not password:
            st.error("⚠️ กรุณากรอกทั้งชื่อผู้ใช้และรหัสผ่าน")
        else:
            db = SyncSessionLocal()
            try:
                db_user = db.query(User).filter(User.username == username.strip()).first()
                if not db_user or not verify_password(password, db_user.hashed_password):
                    st.error("❌ ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่อีกครั้ง")
                elif not db_user.is_active:
                    st.error("⛔ บัญชีนี้ถูกปิดการใช้งาน")
                else:
                    # อัปเดต last login
                    db_user.last_login = datetime.now(timezone.utc)
                    db.commit()

                    st.session_state["user"] = {
                        "id": str(db_user.id),
                        "username": db_user.username,
                        "display_name": db_user.display_name or db_user.username,
                        "email": db_user.email,
                    }
                    st.success(f"🎉 เข้าสู่ระบบสำเร็จ! ยินดีต้อนรับคุณ {db_user.display_name or db_user.username}")
                    st.rerun()
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล: {e}")
            finally:
                db.close()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: สมัครสมาชิกใหม่
# ─────────────────────────────────────────────────────────────────────────────
with tab_register:
    st.markdown("กรอกข้อมูลเพื่อสร้างบัญชีเจ้าของแมวใหม่:")
    with st.form("register_form"):
        r_username = st.text_input("ชื่อผู้ใช้ (Username):", placeholder="ภาษาอังกฤษ ตัวเลข หรือ _ (3 ตัวอักษรขึ้นไป)")
        r_email = st.text_input("อีเมล (Email):", placeholder="example@email.com")
        r_name = st.text_input("ชื่อที่แสดง (Display Name):", placeholder="เช่น คุณแม่น้องส้มซ่า")
        r_gender = st.selectbox("เพศ:", ["หญิง (Female)", "ชาย (Male)", "ไม่ระบุ (Other)"])
        r_pass1 = st.text_input("รหัสผ่าน (อย่างน้อย 8 ตัวอักษร):", type="password")
        r_pass2 = st.text_input("ยืนยันรหัสผ่าน:", type="password")
        reg_submit = st.form_submit_button("✨ สร้างบัญชีและเข้าสู่ระบบ", use_container_width=True)

    if reg_submit:
        r_username = r_username.strip().lower()
        r_email = r_email.strip().lower()

        if len(r_username) < 3:
            st.error("⚠️ ชื่อผู้ใช้ต้องมีอย่างน้อย 3 ตัวอักษร")
        elif "@" not in r_email or "." not in r_email:
            st.error("⚠️ รูปแบบอีเมลไม่ถูกต้อง")
        elif len(r_pass1) < 8:
            st.error("⚠️ รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
        elif r_pass1 != r_pass2:
            st.error("⚠️ รหัสผ่านทั้งสองช่องไม่ตรงกัน")
        else:
            db = SyncSessionLocal()
            try:
                # ตรวจว่า username หรือ email ซ้ำไหม
                exists = db.query(User).filter((User.username == r_username) | (User.email == r_email)).first()
                if exists:
                    st.error("❌ ชื่อผู้ใช้หรืออีเมลนี้มีผู้ใช้งานแล้ว")
                else:
                    new_user = User(
                        id=uuid.uuid4(),
                        username=r_username,
                        email=r_email,
                        hashed_password=hash_password(r_pass1),
                        display_name=r_name or r_username,
                        gender="female" if "หญิง" in r_gender else ("male" if "ชาย" in r_gender else None),
                        is_active=True,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(new_user)
                    db.commit()

                    st.session_state["user"] = {
                        "id": str(new_user.id),
                        "username": new_user.username,
                        "display_name": new_user.display_name,
                        "email": new_user.email,
                    }
                    st.success(f"🎉 สร้างบัญชีสำเร็จ! ยินดีต้อนรับคุณ {new_user.display_name}")
                    st.rerun()
            except Exception as e:
                db.rollback()
                st.error(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {e}")
            finally:
                db.close()

