"""
dashboard/pages/4_🏥_Smart_Health_AI.py
───────────────────────────────────────
ระบบวิเคราะห์สุขภาพขั้นสูง & เวรดูแลในครอบครัว (Advanced Health AI & Family Care)
1. Smart Litter & Renal Health AI — วิเคราะห์ก้อนฉี่และระบบทางเดินปัสสาวะ เตือนความเสี่ยงโรคไต/นิ่วล่วงหน้า
2. Multi-Guardian Family Sync — ระบบเวรดูแลสัตว์เลี้ยงในครอบครัว ป้องกันการให้อาหารหรือป้อนยาซ้ำซ้อน
3. LINE Interactive Flex Message Simulator — จำลองการ์ดแจ้งเตือนแบบกด Action ได้บน LINE
"""

import os
import sys
from datetime import datetime, date, timedelta, timezone
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Ensure project root (CatCare/) is on sys.path ──
_pages_dir   = os.path.dirname(__file__)
_dash_dir    = os.path.dirname(_pages_dir)
_project_dir = os.path.dirname(_dash_dir)
for _p in (_dash_dir, _project_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db_queries import get_all_cats, is_db_available, get_latest_weight

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Health AI & Family Care | Cat Care",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Prompt:wght@600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Sarabun', sans-serif !important;
}
h1, h2, h3 { font-family: 'Prompt', sans-serif !important; color: #2C3E50 !important; }
.health-card {
    background: white;
    border-radius: 16px;
    padding: 1.4rem;
    box-shadow: 0 4px 18px rgba(0,0,0,0.06);
    margin-bottom: 1.2rem;
    border-top: 4px solid #FF9F43;
}
.status-badge-good {
    background: #E8F8F5;
    color: #117A65;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
    border: 1px solid #A3E4D7;
}
.status-badge-warn {
    background: #FEF9E7;
    color: #B7950B;
    padding: 6px 16px;
    border-radius: 20px;
    font-weight: 700;
    font-size: 0.9rem;
    border: 1px solid #F9E79F;
}
.checkin-card {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 14px;
    padding: 1.2rem;
    text-align: center;
}
.stButton button {
    border-radius: 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🏥 Smart Health AI & Multi-Guardian Care")
st.caption("ระบบปัญญาประดิษฐ์คัดกรองความเสี่ยงโรคไต/นิ่ว และระบบเวรดูแลในบ้านแบบ Real-Time")

# Tabs
tab_renal, tab_family, tab_line = st.tabs([
    "🪣 Smart Litter & Renal Health AI (ตรวจสุขภาพไต/นิ่ว)",
    "👨‍👩‍👧‍👦 Multi-Guardian Family Sync (เวรดูแลในบ้าน)",
    "💬 Interactive LINE Flex Preview (จำลองการ์ด LINE)"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Smart Litter & Renal Health AI
# ─────────────────────────────────────────────────────────────────────────────
with tab_renal:
    st.subheader("🪣 Smart Litter & Feline Renal Alert System")
    st.caption("วิเคราะห์พฤติกรรมการปัสสาวะ ขนาดก้อนฉี่ และความถี่ เพื่อคัดกรองความเสี่ยงโรคไตและโรคทางเดินปัสสาวะอักเสบ (FLUTD)")

    col_r1, col_r2 = st.columns([1.2, 1])

    with col_r1:
        st.markdown("""<div class="health-card">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
<h4 style="margin:0;color:#2C3E50">🩺 ดัชนีความเสี่ยงทางเดินปัสสาวะ (Renal Risk Index)</h4>
<span class="status-badge-good">🟢 ปกติ สุขภาพดีเยี่ยม (Low Risk)</span>
</div>
<p style="font-size:0.92rem;color:#555;margin:4px 0">
• <b>ความถี่การเข้ากระบะทราย:</b> เฉลี่ย <b>3-4 ครั้ง/วัน</b> (อยู่ในเกณฑ์มาตรฐาน)<br>
• <b>ขนาดก้อนปัสสาวะเฉลี่ย:</b> ก้อนกลมแน่นขนาด <b>4.5 – 5.5 ซม.</b> (ปริมาตรปกติ)<br>
• <b>แนวโน้ม 7 วันย้อนหลัง:</b> ไม่พบสัญญาณการเบ่งปัสสาวะนาน หรือปัสสาวะหยดกะปริบกะปรอย
</p>
</div>""", unsafe_allow_html=True)

        # จำลองข้อมูลก้อนฉี่ 7 วัน
        days_7 = [(date.today() - timedelta(days=i)).strftime("%d/%m") for i in range(6, -1, -1)]
        clump_vol = [4.8, 5.0, 5.2, 4.9, 5.1, 5.3, 5.0]
        trips = [3, 4, 3, 3, 4, 3, 4]

        fig_litter = go.Figure()
        fig_litter.add_trace(go.Bar(
            x=days_7, y=clump_vol, name="ขนาดก้อนฉี่เฉลี่ย (ซม.)",
            marker_color="#FF9F43", yaxis="y1"
        ))
        fig_litter.add_trace(go.Scatter(
            x=days_7, y=trips, name="จำนวนครั้งเข้าห้องน้ำ/วัน",
            line=dict(color="#2ECC71", width=3), mode="lines+markers", yaxis="y2"
        ))
        fig_litter.update_layout(
            title="สถิติการใช้กระบะทราย 7 วันล่าสุด",
            template="plotly_white", height=320,
            yaxis=dict(title="ขนาดก้อนฉี่ (ซม.)", range=[0, 8]),
            yaxis2=dict(title="จำนวนครั้ง", overlaying="y", side="right", range=[0, 6]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(t=30, b=30), plot_bgcolor="#FFFAF4"
        )
        st.plotly_chart(fig_litter, use_container_width=True)

    with col_r2:
        st.markdown("#### 💧 เครื่องคำนวณปริมาณน้ำที่แมวต้องดื่ม (Hydration Calculator)")
        st.caption("แมวต้องการน้ำขั้นต่ำอย่างน้อย **50 ml ต่อน้ำหนักตัว 1 kg** เพื่อป้องกันนิ่วในกระเพาะปัสสาวะ")

        cat_weight_input = st.slider("⚖️ น้ำหนักตัวของแมว (kg):", 2.0, 8.0, 4.5, 0.1)
        water_needed = cat_weight_input * 50.0

        st.metric("💧 ปริมาณน้ำที่ร่างกายต้องการขั้นต่ำ:", f"{water_needed:.0f} มิลลิลิตร / วัน")

        st.markdown(f"""<div style="background:#EBF5FB;border-radius:12px;padding:12px 16px;border-left:4px solid #3498DB;font-size:0.88rem;color:#1B4F72">
<b>💡 เทคนิคเพิ่มน้ำเข้าร่างกายน้องแมว:</b><br>
• อาหารเปียก 1 ซอง (85g) ให้น้ำประมาณ <b>65-70 ml</b><br>
• น้ำสะอาดที่ต้องดื่มเพิ่มจากน้ำพุแมว: <b>{max(0.0, water_needed - 70):.0f} ml/วัน</b><br>
• ควรวางชามน้ำแยกห่างจากชามอาหารและกระบะทรายอย่างน้อย 1 เมตร
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Multi-Guardian Family Sync
# ─────────────────────────────────────────────────────────────────────────────
with tab_family:
    st.subheader("👨‍👩‍👧‍👦 Multi-Guardian Family Care & Routine Sync")
    st.caption("ระบบเวรดูแลสัตว์เลี้ยงในครอบครัว อัปเดตสถานะแบบ Real-time ป้องกันการเทข้าวหรือป้อนยาซ้ำซ้อน")

    # กำหนดสถานะใน session_state
    today_str = date.today().strftime("%Y-%m-%d")
    if "family_status" not in st.session_state or st.session_state.get("family_date") != today_str:
        st.session_state["family_date"] = today_str
        st.session_state["family_status"] = {
            "breakfast": {"done": True, "by": "คุณแม่", "time": "07:15 น."},
            "dinner": {"done": False, "by": "", "time": ""},
            "medicine": {"done": True, "by": "ลูกสาว (Natcha)", "time": "08:00 น."},
            "litter": {"done": False, "by": "", "time": ""}
        }

    # Guardian selection
    col_guard, col_spacer = st.columns([1, 2])
    with col_guard:
        current_guardian = st.selectbox("👤 คุณคือใครในบ้าน:", ["คุณแม่ (Mom)", "คุณพ่อ (Dad)", "ลูกสาว (Natcha)", "พี่เลี้ยง (Pet Sitter)"])

    st.markdown("#### 📅 ตารางเช็กอินประจำวัน:")

    col_t1, col_t2, col_t3, col_t4 = st.columns(4)

    status = st.session_state["family_status"]

    # 1. อาหารเช้า
    with col_t1:
        st.markdown('<div class="checkin-card">', unsafe_allow_html=True)
        st.markdown("### 🥣 อาหารเช้า")
        if status["breakfast"]["done"]:
            st.success(f"✅ ให้แล้ว\n\nโดย: {status['breakfast']['by']}\n\nเวลา: {status['breakfast']['time']}")
        else:
            st.warning("⏳ ยังไม่ได้ให้")
            if st.button("กดเช็กอินมื้อเช้า", key="btn_b"):
                status["breakfast"] = {"done": True, "by": current_guardian.split()[0], "time": datetime.now().strftime("%H:%M น.")}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. อาหารเย็น
    with col_t2:
        st.markdown('<div class="checkin-card">', unsafe_allow_html=True)
        st.markdown("### 🥫 อาหารเย็น")
        if status["dinner"]["done"]:
            st.success(f"✅ ให้แล้ว\n\nโดย: {status['dinner']['by']}\n\nเวลา: {status['dinner']['time']}")
        else:
            st.warning("⏳ รอให้อาหารเย็น")
            if st.button("กดเช็กอินมื้อเย็น", key="btn_d"):
                status["dinner"] = {"done": True, "by": current_guardian.split()[0], "time": datetime.now().strftime("%H:%M น.")}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 3. ยาบำรุง
    with col_t3:
        st.markdown('<div class="checkin-card">', unsafe_allow_html=True)
        st.markdown("### 💊 ป้อนยา/วิตามิน")
        if status["medicine"]["done"]:
            st.success(f"✅ ป้อนแล้ว\n\nโดย: {status['medicine']['by']}\n\nเวลา: {status['medicine']['time']}")
        else:
            st.warning("⏳ ยังไม่ป้อน")
            if st.button("กดเช็กอินป้อนยา", key="btn_m"):
                status["medicine"] = {"done": True, "by": current_guardian.split()[0], "time": datetime.now().strftime("%H:%M น.")}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 4. ตักกระบะทราย
    with col_t4:
        st.markdown('<div class="checkin-card">', unsafe_allow_html=True)
        st.markdown("### 🪣 ตักทรายรอบเย็น")
        if status["litter"]["done"]:
            st.success(f"✅ ตักแล้ว\n\nโดย: {status['litter']['by']}\n\nเวลา: {status['litter']['time']}")
        else:
            st.warning("⏳ ยังไม่ได้ตัก")
            if st.button("กดเช็กอินตักทราย", key="btn_l"):
                status["litter"] = {"done": True, "by": current_guardian.split()[0], "time": datetime.now().strftime("%H:%M น.")}
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 รีเซ็ตสถานะเวรประจำวัน (เพื่อทดสอบใหม่)"):
        st.session_state["family_status"] = {
            "breakfast": {"done": False, "by": "", "time": ""},
            "dinner": {"done": False, "by": "", "time": ""},
            "medicine": {"done": False, "by": "", "time": ""},
            "litter": {"done": False, "by": "", "time": ""}
        }
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: LINE Flex Message Simulator
# ─────────────────────────────────────────────────────────────────────────────
with tab_line:
    st.subheader("💬 Interactive LINE Flex Message Preview")
    st.caption("จำลองหน้าจอการ์ดแจ้งเตือนแบบ Rich UI ที่ส่งเข้า LINE ของเจ้าของแมวจริง")

    col_phone, col_info = st.columns([1, 1.2])

    with col_phone:
        # Smartphone Mockup rendering LINE Chat (No leading whitespace on lines)
        st.markdown("""<div style="background:#7AC5CD;border-radius:28px;padding:20px 14px;max-width:340px;margin:auto;box-shadow:0 12px 36px rgba(0,0,0,0.25);border:6px solid #2C3E50">
<div style="text-align:center;color:white;font-weight:700;font-size:0.9rem;margin-bottom:12px">🟢 LINE · Cat Care Assistant</div>
<div style="background:white;border-radius:18px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1)">
<div style="position:relative;height:140px;background:url('https://images.unsplash.com/photo-1574158622682-e40e69881006?q=80&w=600&auto=format&fit=crop') center/cover">
<span style="position:absolute;top:10px;right:10px;background:#FF6B9D;color:white;padding:3px 10px;border-radius:12px;font-size:0.75rem;font-weight:700">ด่วน อีก 2 วัน!</span>
</div>
<div style="padding:14px">
<div style="color:#FF9F43;font-weight:700;font-size:0.8rem">🐱 CAT CARE NOTIFICATION</div>
<div style="font-weight:800;font-size:1.1rem;color:#2C3E50;margin:2px 0">💉 ถึงกำหนดนัดฉีดวัคซีนรวม</div>
<div style="font-size:0.82rem;color:#666">น้องส้มซ่า (Somza) · Scottish Fold</div>
<div style="margin:10px 0;background:#FFF8F0;border-radius:8px;padding:8px 10px;font-size:0.8rem;color:#555">
📅 <b>วันนัดหมาย:</b> 12 พ.ย. 2569 (10:00 น.)<br>
🏥 <b>สถานที่:</b> รพ.สัตว์ทองหล่อ
</div>
<div style="display:flex;flex-direction:column;gap:6px;margin-top:12px">
<button style="width:100%;background:#06C755;color:white;border:none;border-radius:10px;padding:8px;font-weight:700;font-size:0.85rem;cursor:pointer">✅ บันทึกว่าพาไปฉีดแล้ว</button>
<button style="width:100%;background:#F1F5F9;color:#475569;border:none;border-radius:10px;padding:6px;font-weight:600;font-size:0.8rem;cursor:pointer">⏰ เตือนฉันอีกครั้งพรุ่งนี้</button>
</div>
</div>
</div>
<div style="text-align:right;color:white;font-size:0.7rem;margin-top:8px">อ่านแล้ว 07:00 น.</div>
</div>""", unsafe_allow_html=True)

    with col_info:
        st.markdown("""<div style="background:white;border-radius:16px;padding:1.5rem;box-shadow:0 4px 18px rgba(0,0,0,0.06)">
<h4 style="margin:0 0 10px;color:#2C3E50">✨ จุดเด่นของ LINE Flex Message</h4>
<p style="font-size:0.9rem;color:#555;line-height:1.6">
ข้อดีที่เหนือกว่าการแจ้งเตือนแบบ SMS หรือ Text LINE ทั่วไป:<br>
1. <b>Rich Interactive Actions:</b> มีปุ่มให้เจ้าของสัตว์เลี้ยงกดจากแชทได้ทันที เช่น เมื่อป้อนยาเสร็จ กดปุ่ม <code>[✅ ฉีดแล้ว]</code> ข้อมูลจะถูกอัปเดตลงฐานข้อมูล CatCare อัตโนมัติ<br>
2. <b>Dynamic Branding:</b> แสดงรูปน้องแมวตัวจริง พร้อมสีกรอบที่เปลี่ยนตามระดับความด่วน (ชมพู=ด่วนมาก, ส้ม=เตือนล่วงหน้า)<br>
3. <b>Deep Link:</b> สามารถกดปุ่มเพื่อกระโดดเปิดหน้ารายละเอียดใน Dashboard ได้ในคลิกเดียว
</p>
</div>""", unsafe_allow_html=True)

