"""
dashboard/pages/3_🪪_Pet_Passport.py
───────────────────────────────────
บัตรประจำตัวและพาสปอร์ตดิจิทัลสำหรับสัตว์เลี้ยง (Digital Pet Passport)
- แสดงประวัติส่วนตัว, เลขไมโครชิป, ประวัติวัคซีน และ QR Code สำหรับสแกน
- เครื่องคำนวณสัดส่วนอาหารเม็ด + อาหารเปียกตามเป้าหมายแคลอรี (Smart Mixed Feeding Calculator)
- ฐานข้อมูลค้นหาพืชมีพิษและอาหารอันตราย (Toxic Food & Emergency Radar)
"""

import os
import sys
import io
import base64
from datetime import date
import streamlit as st
import pandas as pd
import qrcode
from PIL import Image

# ── Ensure project root (CatCare/) is on sys.path ──
_pages_dir   = os.path.dirname(__file__)
_dash_dir    = os.path.dirname(_pages_dir)
_project_dir = os.path.dirname(_dash_dir)
for _p in (_dash_dir, _project_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from db_queries import get_all_cats, is_db_available, get_latest_weight, get_cat_full_medical_data
from app.feline_health import estimate_feline_bcs, calculate_energy_needs
from app.clinical_export import generate_clinical_csv, generate_clinical_pdf

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="พาสปอร์ตสัตว์เลี้ยง | Cat Care",
    page_icon="🪪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS for Luxury Gold Passport ──────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Prompt:wght@600;700;800&family=Cinzel:wght@700&display=swap');

.passport-card {
    background: linear-gradient(145deg, #1A365D 0%, #0F172A 100%);
    border: 3px solid #D4AF37;
    border-radius: 20px;
    padding: 2rem;
    color: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
    position: relative;
    overflow: hidden;
    margin-bottom: 2rem;
}
.passport-card::after {
    content: "🐾 FELINE PASSPORT";
    position: absolute;
    bottom: -15px;
    right: 20px;
    font-family: 'Cinzel', serif;
    font-size: 3rem;
    color: rgba(212, 175, 55, 0.05);
    pointer-events: none;
}
.passport-header {
    border-bottom: 2px solid rgba(212, 175, 55, 0.4);
    padding-bottom: 12px;
    margin-bottom: 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.passport-title {
    font-family: 'Cinzel', serif;
    color: #D4AF37;
    font-size: 1.4rem;
    letter-spacing: 2px;
}
.cat-avatar {
    width: 140px;
    height: 140px;
    border-radius: 14px;
    object-fit: cover;
    border: 3px solid #D4AF37;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.field-label {
    font-size: 0.78rem;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.field-value {
    font-size: 0.95rem;
    font-weight: 600;
    color: #F8FAFC;
    margin-bottom: 10px;
}
.visa-badge {
    display: inline-block;
    background: rgba(46, 204, 113, 0.15);
    border: 1px solid #2ECC71;
    color: #2ECC71;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin: 4px 6px 4px 0;
}
.danger-tag-high {
    background: #FEE2E2;
    color: #991B1B;
    border-left: 4px solid #DC2626;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 10px;
}
.danger-tag-med {
    background: #FEF3C7;
    color: #92400E;
    border-left: 4px solid #F59E0B;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 10px;
}
.danger-tag-safe {
    background: #ECFDF5;
    color: #065F46;
    border-left: 4px solid #10B981;
    padding: 10px 14px;
    border-radius: 8px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🪪 Digital Pet Passport & Smart Assistant")
st.caption("ระบบพาสปอร์ตสัตว์เลี้ยงดิจิทัล สำหรับคลินิก โรงแรมแมว พร้อมระบบคำนวณโภชนาการอัจฉริยะ")

# ─── Load Cats ────────────────────────────────────────────────────────────────
if is_db_available():
    cats_df = get_all_cats()
else:
    cats_df = pd.DataFrame()

if cats_df.empty:
    cats_df = pd.DataFrame([
        {"id": "1", "name": "ส้มซ่า (Somza)", "breed": "Scottish Fold", "gender": "male", "birth_date": date(2024, 11, 10)},
        {"id": "2", "name": "มิดไนท์ (Midnight)", "breed": "British Shorthair", "gender": "female", "birth_date": date(2025, 11, 10)},
        {"id": "3", "name": "ถุงทอง (Thungthong)", "breed": "แมวไทยโคราช (Korat)", "gender": "male", "birth_date": date(2025, 6, 28)},
    ])

cat_names = cats_df["name"].tolist()
selected_cat_name = st.selectbox("🐾 เลือกแมวที่ต้องการดูพาสปอร์ต:", cat_names)

cat_row = cats_df[cats_df["name"] == selected_cat_name].iloc[0]
cat_id = str(cat_row.get("id", ""))
breed = str(cat_row.get("breed", "Scottish Fold"))
gender = str(cat_row.get("gender", "male"))
birth = cat_row.get("birth_date")

# Profile images mapping
AVATARS = {
    "ส้มซ่า (Somza)": "https://images.unsplash.com/photo-1574158622682-e40e69881006?q=80&w=400&auto=format&fit=crop",
    "มิดไนท์ (Midnight)": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=400&auto=format&fit=crop",
    "ถุงทอง (Thungthong)": "https://images.unsplash.com/photo-1543852786-1cf6624b9987?q=80&w=400&auto=format&fit=crop",
}
avatar_url = AVATARS.get(selected_cat_name, "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=400&auto=format&fit=crop")

# Mock microchips & blood type
MICROCHIPS = {
    "ส้มซ่า (Somza)": "900215002981324",
    "มิดไนท์ (Midnight)": "900215002981325",
    "ถุงทอง (Thungthong)": "900215002981326",
}
chip_num = MICROCHIPS.get(selected_cat_name, "900215000000000")

# คำนวณอายุ
if isinstance(birth, date):
    age_years = (date.today() - birth).days // 365
    age_months = ((date.today() - birth).days % 365) // 30
    age_str = f"{age_years} ปี {age_months} เดือน"
else:
    age_str = "2 ขวบ"

# น้ำหนักปัจจุบัน
current_w = get_latest_weight(cat_id) or 4.5
bcs_data = estimate_feline_bcs(current_w, breed, gender)

# ─── Generate QR Code ─────────────────────────────────────────────────────────
qr_data = (
    f"CATCARE PASSPORT\n"
    f"Name: {selected_cat_name}\n"
    f"Breed: {breed}\n"
    f"Microchip: {chip_num}\n"
    f"Weight: {current_w} kg (BCS {bcs_data['bcs']}/9)\n"
    f"Rabies: Vaccinated (Valid until Nov 2027)\n"
    f"Emergency: 081-234-5678"
)

qr = qrcode.QRCode(version=1, box_size=4, border=1)
qr.add_data(qr_data)
qr.make(fit=True)
qr_img = qr.make_image(fill_color="#1A365D", back_color="white")

buf = io.BytesIO()
qr_img.save(buf, format="PNG")
qr_b64 = base64.b64encode(buf.getvalue()).decode()

# ─── Render Passport Card ─────────────────────────────────────────────────────
st.markdown(f"""<div class="passport-card">
<div class="passport-header">
<div class="passport-title">🐾 DIGITAL PET PASSPORT</div>
<div style="font-size:0.85rem;color:#D4AF37">KINGDOM OF CATCARE · NO. {chip_num[-6:]}</div>
</div>
<div style="display:flex;gap:2rem;flex-wrap:wrap">
<div>
<img src="{avatar_url}" class="cat-avatar">
</div>
<div style="flex:1;min-width:250px">
<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px">
<div>
<div class="field-label">ชื่อสัตว์เลี้ยง (Name)</div>
<div class="field-value" style="font-size:1.2rem;color:#D4AF37">{selected_cat_name}</div>
</div>
<div>
<div class="field-label">เลขไมโครชิป (Microchip No.)</div>
<div class="field-value">{chip_num}</div>
</div>
<div>
<div class="field-label">สายพันธุ์ (Breed)</div>
<div class="field-value">{breed}</div>
</div>
<div>
<div class="field-label">เพศ & สถานะทำหมัน</div>
<div class="field-value">{'เพศผู้ (Male)' if 'male' in gender else 'เพศเมีย (Female)'} · ทำหมันแล้ว ✅</div>
</div>
<div>
<div class="field-label">อายุ (Age)</div>
<div class="field-value">{age_str}</div>
</div>
<div>
<div class="field-label">ดัชนีมวลกายสรีระ (BCS)</div>
<div class="field-value" style="color:{bcs_data['color']}">{current_w:.2f} kg (ระดับ {bcs_data['bcs']}/9 - {bcs_data['status'][:15]})</div>
</div>
</div>
<div style="margin-top:12px;border-top:1px dashed rgba(255,255,255,0.15);padding-top:10px">
<div class="field-label" style="margin-bottom:6px">วีซ่าวัคซีนที่ได้รับรองแล้ว (Validated Vaccines):</div>
<span class="visa-badge">💉 พิษสุนัขบ้า (Rabies) 2026</span>
<span class="visa-badge">💉 หัด-หวัดแมว (FVRCP) 2026</span>
<span class="visa-badge">💊 ถ่ายพยาธิ (Dewormed) Q4</span>
</div>
</div>
<div style="text-align:center;background:white;padding:12px;border-radius:12px;display:flex;flex-direction:column;align-items:center;justify-content:center;height:fit-content">
<img src="data:image/png;base64,{qr_b64}" width="120" height="120">
<span style="font-size:0.75rem;color:#1A365D;font-weight:700;margin-top:6px">สแกนดูประวัติคลินิก</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

# ─── Tabs for Additional Tools ────────────────────────────────────────────────
tab_feed, tab_toxic, tab_export = st.tabs([
    "🍽️ เครื่องคำนวณอาหารเม็ด + อาหารเปียก (Mixed Feeding)",
    "🚨 ค้นหาพืชมีพิษและอาหารอันตราย (Toxic Radar)",
    "📄 ส่งออกประวัติการรักษาคลินิก (PDF / CSV Clinical Export)"
])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: Smart Mixed Feeding Calculator
# ─────────────────────────────────────────────────────────────────────────────
with tab_feed:
    st.subheader("🥣 Smart Calorie & Mixed Feeding Portion Matcher")
    st.caption("คำนวณปริมาณอาหารเปียกผสมอาหารเม็ดให้ได้แคลอรีตรงตามเป้าหมายของสรีระแมวตัวนี้พอดี 100%")

    energy = calculate_energy_needs(current_w, bcs_data["bcs"])
    target_der = energy["der_kcal"]

    st.info(f"🎯 **เป้าหมายแคลอรีของ {selected_cat_name}:** **{target_der:.0f} kcal / วัน** (สภาวะ: {energy['goal']})")

    col_w1, col_w2 = st.columns([1, 1.2])

    with col_w1:
        wet_pouches = st.slider("🥫 ปริมาณอาหารเปียกที่ให้ต่อวัน (ซอง / กระป๋อง):", 0.0, 3.0, 1.0, 0.5)
        wet_kcal_per_pouch = st.number_input("แคลอรีอาหารเปียกต่อซอง (kcal/ซอง):", value=85, step=5)
        dry_kcal_per_100g = st.number_input("แคลอรีอาหารเม็ดต่อ 100 กรัม (kcal/100g):", value=380, step=10)

    # คำนวณส่วนต่าง
    wet_total_kcal = wet_pouches * wet_kcal_per_pouch
    remaining_kcal = max(0.0, target_der - wet_total_kcal)
    dry_needed_grams = (remaining_kcal / dry_kcal_per_100g) * 100.0

    with col_w2:
        st.markdown(f"""<div style="background:#FFF8F0;border:2px solid #FF9F43;border-radius:16px;padding:1.4rem">
<h4 style="margin:0 0 10px;color:#2C3E50">📋 สัดส่วนมื้ออาหารที่แนะนำต่อวัน:</h4>
<p style="font-size:1.1rem;margin:6px 0">🥫 <b>อาหารเปียก:</b> <span style="color:#E65100;font-weight:700">{wet_pouches} ซอง</span> ({wet_total_kcal:.0f} kcal)</p>
<p style="font-size:1.1rem;margin:6px 0">🥣 <b>อาหารเม็ดที่ต้องเติม:</b> <span style="color:#FF9F43;font-weight:700">{dry_needed_grams:.1f} กรัม</span> ({remaining_kcal:.0f} kcal)</p>
<hr style="border:none;border-top:1px dashed #FFD093;margin:12px 0">
<p style="font-size:0.9rem;color:#666;margin:0">💡 <b>คำแนะนำการแบ่งมื้อ:</b> แบ่งอาหารเม็ด {dry_needed_grams/2:.1f} กรัม สำหรับมื้อเช้า-เย็น และให้อาหารเปียก 1 ซองผสมน้ำสะอาดเล็กน้อยเพื่อเพิ่มปริมาณน้ำในร่างกาย ป้องกันโรคนิ่วและไต</p>
</div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: Toxic Food & Plants Radar
# ─────────────────────────────────────────────────────────────────────────────
with tab_toxic:
    st.subheader("🚨 สารานุกรมความปลอดภัย: พืชและอาหารที่มีพิษต่อแมว")
    st.caption("ค้นหาด่วนก่อนให้น้องแมวกินหรือนำต้นไม้เข้าบ้าน")

    search_q = st.text_input("🔍 พิมพ์ชื่ออาหารหรือต้นไม้ที่ต้องการค้นหา (เช่น ลิลลี่, ช็อกโกแลต, ไก่ต้ม, พลูด่าง):", placeholder="พิมพ์คำค้นหา...")

    TOXIC_DB = [
        {"name": "ดอกลิลลี่ (Lily ทุกสายพันธุ์)", "level": "high", "detail": "☠️ อันตรายถึงชีวิต! แม้แต่ละอองเกสรหรือน้ำในแจกัน ทำให้ไตวายเฉียบพลันภายใน 24-72 ชม."},
        {"name": "ยาพาราเซตามอล (Paracetamol)", "level": "high", "detail": "☠️ ยาพิษร้ายแรงสำหรับแมว! ทำให้เม็ดเลือดแดงแตก ร่างกายขาดออกซิเจน เสียชีวิตอย่างรวดเร็ว ห้ามให้เด็ดขาด"},
        {"name": "ช็อกโกแลต & โกโก้ (Theobromine)", "level": "high", "detail": "☠️ มีสาร Theobromine หัวใจเต้นผิดจังหวะ ชัก กล้ามเนื้อเกร็ง และอาจเสียชีวิต"},
        {"name": "หัวหอม กระเทียม ชาบู ต้นหอม", "level": "high", "detail": "☠️ ทำลายเซลล์เม็ดเลือดแดง ทำให้เกิดภาวะโลหิตจางอย่างรุนแรง (Heinz Body Anemia)"},
        {"name": "ต้นพลูด่าง / มอนสเตอร่า (Monstera)", "level": "med", "detail": "⚠️ มีผลึกแคลเซียมออกซาเลต ทำให้ระคายเคืองช่องปาก ลิ้นบวม กลืนลำบาก น้ำลายไหลย้อย"},
        {"name": "กาแฟ & คาเฟอีน", "level": "high", "detail": "☠️ กระตุ้นระบบประสาทและหัวใจอย่างรุนแรง ทำให้หัวใจวาย"},
        {"name": "เนื้ออกไก่ต้มสุก (ไม่ปรุงรส)", "level": "safe", "detail": "✅ ปลอดภัย ย่อยง่าย โปรตีนสูง เหมาะเป็นอาหารเสริมเพื่อสุขภาพ"},
        {"name": "ต้นหญ้าข้าวบาร์เลย์ / ต้นข้าวสาลี (Cat Grass)", "level": "safe", "detail": "✅ ปลอดภัย ดีต่อระบบทางเดินอาหาร ช่วยขับก้อนขน"},
        {"name": "กัญชาแมว (Catnip / Silvervine)", "level": "safe", "detail": "✅ ปลอดภัย ช่วยผ่อนคลายและลดความเครียดในแมว"},
    ]

    filtered = [item for item in TOXIC_DB if not search_q or search_q.lower() in item["name"].lower() or search_q.lower() in item["detail"].lower()]

    for item in filtered:
        lvl = item["level"]
        cls = "danger-tag-high" if lvl == "high" else ("danger-tag-med" if lvl == "med" else "danger-tag-safe")
        badge = "🔴 อันตรายร้ายแรงถึงชีวิต" if lvl == "high" else ("🟡 มีพิษปานกลาง / ระคายเคือง" if lvl == "med" else "🟢 ปลอดภัยสำหรับแมว")
        st.markdown(f"""<div class="{cls}">
<div style="font-weight:700;font-size:1.05rem;margin-bottom:4px">{item['name']} <span style="font-size:0.8rem;margin-left:8px">[{badge}]</span></div>
<div style="font-size:0.9rem">{item['detail']}</div>
</div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("📞 **เบอร์โทรฉุกเฉินโรงพยาบาลสัตว์ 24 ชั่วโมง:**")
    st.markdown("• **รพ.สัตว์ทองหล่อ (24 ชม.):** `02-079-9999` &nbsp;&nbsp;|&nbsp;&nbsp; • **รพ.สัตว์ ม.เกษตรศาสตร์ บางเขน:** `02-797-1900`")


# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: Clinical & Hospital Export Suite (PDF / CSV)
# ─────────────────────────────────────────────────────────────────────────────
with tab_export:
    st.subheader(f"🏥 เอกสารสรุปประวัติสุขภาพทางการแพทย์: {selected_cat_name}")
    st.caption("ส่งออกประวัติสุขภาพที่ได้รับการรับรอง สำหรับยื่นต่อสัตวแพทย์ที่โรงพยาบาลสัตว์ หรือคลินิกประจำ")

    med_export = get_cat_full_medical_data(cat_id)

    col_ep1, col_ep2 = st.columns(2)

    with col_ep1:
        st.markdown(f"""<div style="background:white;border-radius:18px;padding:1.4rem;border:1.5px solid #E2E8F0;box-shadow:0 4px 16px rgba(0,0,0,0.05);height:100%">
<div style="font-size:2.2rem;margin-bottom:8px">📄</div>
<h4 style="margin:0 0 6px;color:#1E293B">Official Medical Record (PDF)</h4>
<p style="font-size:0.88rem;color:#64748B;line-height:1.6;margin-bottom:14px">
เอกสารสรุปประวัติสุขภาพทางการแพทย์ ออกแบบตามมาตรฐานเวชระเบียนสัตว์เลี้ยง ประกอบด้วย:
<br>• ข้อมูลประจำตัวและเลขไมโครชิป ({chip_num})
<br>• สรีระและคะแนนดัชนีมวลกายสากล (WSAVA BCS 1-9)
<br>• ตารางบันทึกการรับวัคซีนและยาป้องกันปรสิต
<br>• ประวัติแนวโน้มน้ำหนักตัวย้อนหลัง
<br>• ช่องลงนามรับรองโดยสัตวแพทย์ผู้ตรวจ
</p>
</div>""", unsafe_allow_html=True)

        pdf_doc = generate_clinical_pdf(med_export["cat_info"], med_export["weight_logs"], med_export["reminders"])
        st.download_button(
            label=f"📥 ดาวน์โหลด Medical Record PDF ({selected_cat_name})",
            data=pdf_doc,
            file_name=f"CatCare_Medical_Record_{selected_cat_name}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    with col_ep2:
        st.markdown(f"""<div style="background:white;border-radius:18px;padding:1.4rem;border:1.5px solid #E2E8F0;box-shadow:0 4px 16px rgba(0,0,0,0.05);height:100%">
<div style="font-size:2.2rem;margin-bottom:8px">📊</div>
<h4 style="margin:0 0 6px;color:#1E293B">Raw Clinical & Expense Data (CSV)</h4>
<p style="font-size:0.88rem;color:#64748B;line-height:1.6;margin-bottom:14px">
ส่งออกข้อมูลดิบทั้งหมดเพื่อนำไปประมวลผลต่อ หรือส่งให้คลินิก:
<br>• รองรับ UTF-8 with BOM เปิดใน <b>Microsoft Excel ภาษาไทยไม่เพี้ยน</b>
<br>• ข้อมูลการชั่งน้ำหนักและการกินรายวัน
<br>• ข้อมูลนัดหมายและการฉีดวัคซีน
<br>• บันทึกค่ารักษาพยาบาลและค่ายาแยกหมวดหมู่
<br>• เหมาะสำหรับการเคลมประกันสุขภาพสัตว์เลี้ยง
</p>
</div>""", unsafe_allow_html=True)

        csv_doc = generate_clinical_csv(med_export["cat_info"], med_export["weight_logs"], med_export["reminders"], med_export["expenses"])
        st.download_button(
            label=f"📥 ดาวน์โหลดข้อมูลดิบ CSV ({selected_cat_name})",
            data=csv_doc.encode("utf-8-sig"),
            file_name=f"CatCare_Clinical_Data_{selected_cat_name}.csv",
            mime="text/csv",
            use_container_width=True
        )

