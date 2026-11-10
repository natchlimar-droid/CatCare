"""
🐱 Cat Care — Analytics Dashboard (เชื่อม DB จริง)
====================================================
- ถ้า DB พร้อม → ดึงข้อมูลจริง
- ถ้า DB ไม่พร้อม → แสดง Demo Mode (Mock Data)
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import random, sys, os

_dash_dir = os.path.dirname(__file__)
_project_dir = os.path.abspath(os.path.join(_dash_dir, ".."))
for _p in (_dash_dir, _project_dir):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from db_queries import (
    is_db_available, get_all_cats, get_expense_summary_by_month,
    get_expense_kpi, get_weight_food_trend, get_latest_weight,
)
from app.feline_health import estimate_feline_bcs, calculate_energy_needs, get_breed_info

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="📊 Analytics | Cat Care", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;600;700&family=Prompt:wght@600;700&display=swap');
html, body, [class*="css"], .stApp {
    font-family: 'Sarabun', sans-serif !important;
    background: linear-gradient(135deg, #FFF8F0 0%, #F7F1E3 100%) !important;
}
h1,h2,h3 { font-family: 'Prompt', sans-serif !important; color: #2C3E50 !important; }
.db-badge {
    display: inline-block; border-radius: 20px;
    padding: 3px 14px; font-size: 0.82rem; font-weight: 600;
    margin-bottom: 1rem;
}
.db-live  { background: #d4edda; color: #155724; }
.db-demo  { background: #fff3cd; color: #856404; }
div[data-testid="stMetricValue"] { color: #FF9F43 !important; }
.stButton button {
    background: linear-gradient(135deg, #FF9F43, #FFB347) !important;
    color: white !important; border: none !important; border-radius: 10px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)


# ─── Mock Data (Demo Mode) ────────────────────────────────────────────────────
@st.cache_data(ttl=60)
def mock_expense_data():
    months = pd.date_range(end=date.today(), periods=6, freq="MS").strftime("%Y-%m").tolist()
    records = []
    for m in months:
        records += [
            {"month": m, "category": "food",     "amount": random.randint(1400, 2200)},
            {"month": m, "category": "vet",       "amount": random.randint(0, 2500)},
            {"month": m, "category": "litter",    "amount": random.randint(700, 1100)},
            {"month": m, "category": "medicine",  "amount": random.randint(0, 600)},
            {"month": m, "category": "toy",       "amount": random.randint(0, 400)},
        ]
    return pd.DataFrame(records)


@st.cache_data(ttl=60)
def mock_weight_food(cat_name: str):
    days = [date.today() - timedelta(days=i) for i in range(29, -1, -1)]
    weight, food = 4.1, 200.0
    records = []
    for d in days:
        weight += random.uniform(-0.05, 0.07)
        food += random.uniform(-20, 25)
        records.append({"date": pd.Timestamp(d), "avg_weight_kg": round(max(3.5, weight), 2),
                         "total_food_g": round(max(150, food), 1)})
    return pd.DataFrame(records)


# ─── DB Status ────────────────────────────────────────────────────────────────
DB_LIVE = is_db_available()

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🐱 Cat Care")

    # User Profile / Login status in sidebar
    user = st.session_state.get("user")
    if user:
        st.markdown(f"👤 **{user['display_name']}**")
        st.caption(f"@{user['username']} · เข้าสู่ระบบแล้ว")
    else:
        st.caption("🔒 ยังไม่ได้เข้าสู่ระบบ")
        if st.button("🔐 ไปที่หน้า Login", use_container_width=True):
            st.switch_page("pages/0_🔐_Login.py")
    st.markdown("---")
    if DB_LIVE:
        cats_df = get_all_cats()
        cat_options = cats_df["name"].tolist() if not cats_df.empty else ["ทั้งหมด"]
        cat_options = ["ทั้งหมด"] + cat_options
    else:
        cats_df = pd.DataFrame({"id": ["demo-1"], "name": ["น้องสามสี (Demo)"]})
        cat_options = ["น้องสามสี (Demo)"]
    selected_cat = st.selectbox("🐾 เลือกแมว", cat_options)
    st.markdown("---")
    show_months = st.slider("แสดงย้อนหลัง (เดือน)", 3, 12, 6)
    st.caption("📅 " + date.today().strftime("%d/%m/%Y"))

# ─── Header ───────────────────────────────────────────────────────────────────
st.title("📊 Cat Care — Analytics Dashboard")
if DB_LIVE:
    st.markdown('<span class="db-badge db-live">🟢 เชื่อมต่อ Database แล้ว (Live Data)</span>', unsafe_allow_html=True)
else:
    st.markdown('<span class="db-badge db-demo">🟡 Demo Mode — ตั้งค่า DATABASE_URL ใน .env เพื่อดูข้อมูลจริง</span>', unsafe_allow_html=True)

st.markdown("---")

# ─── KPI Cards ────────────────────────────────────────────────────────────────
if DB_LIVE:
    kpi = get_expense_kpi()
    latest_w = get_latest_weight(
        cats_df[cats_df["name"] == selected_cat]["id"].iloc[0]
        if selected_cat != "ทั้งหมด" and not cats_df.empty else ""
    )
else:
    kpi = {"total": 4850, "food": 1800, "vet": 1500, "litter": 950}
    latest_w = 4.35

k1, k2, k3, k4 = st.columns(4)
k1.metric("💰 รวมเดือนนี้",  f"฿{kpi.get('total', 0):,.0f}")
k2.metric("🍽️ ค่าอาหาร",   f"฿{kpi.get('food', 0):,.0f}")
k3.metric("🏥 ค่าหมอ",     f"฿{kpi.get('vet', 0):,.0f}")
k4.metric("⚖️ น้ำหนักล่าสุด", f"{latest_w:.2f} kg" if latest_w else "—")

st.markdown("---")

# ─── Chart 1: Stacked Bar ─────────────────────────────────────────────────────
st.subheader("📊 ค่าใช้จ่ายรายเดือน แยกหมวดหมู่")

expense_df = get_expense_summary_by_month(show_months) if DB_LIVE else mock_expense_data()

COLORS = {"food": "#FF9F43", "vet": "#FF6B9D", "litter": "#A8E6CF",
          "medicine": "#C3A9D1", "toy": "#FFD93D", "other": "#b0bec5"}
LABELS = {"food": "อาหาร", "vet": "ค่าหมอ", "litter": "ทราย",
          "medicine": "ยา", "toy": "ของเล่น", "other": "อื่นๆ"}

fig_bar = go.Figure()
for cat_key in COLORS:
    sub = expense_df[expense_df["category"] == cat_key]
    if sub.empty:
        continue
    fig_bar.add_trace(go.Bar(
        name=LABELS.get(cat_key, cat_key),
        x=sub["month"], y=sub["amount"],
        marker_color=COLORS[cat_key],
        text=sub["amount"].apply(lambda v: f"฿{v:,.0f}"),
        textposition="inside",
    ))
fig_bar.update_layout(
    barmode="stack", template="plotly_white", height=400,
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    xaxis_title="เดือน", yaxis_title="จำนวนเงิน (บาท)",
    margin=dict(t=10, b=40),
    plot_bgcolor="#FFFAF4", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")

# ─── Chart 2: Dual-Axis Line ──────────────────────────────────────────────────
st.subheader("📈 น้ำหนักตัว vs ปริมาณอาหาร (30 วันย้อนหลัง)")
st.caption("🟠 เส้นอาหาร (กรัม, แกนซ้าย) · 🔵 เส้นน้ำหนัก (kg, แกนขวา)")

if DB_LIVE and selected_cat != "ทั้งหมด" and not cats_df.empty:
    cat_id = cats_df[cats_df["name"] == selected_cat]["id"].iloc[0]
    wf_df = get_weight_food_trend(cat_id, days=30)
else:
    wf_df = mock_weight_food(selected_cat)

fig_dual = go.Figure()
fig_dual.add_trace(go.Scatter(
    x=wf_df["date"], y=wf_df["total_food_g"],
    name="ปริมาณอาหาร (กรัม)", yaxis="y1",
    line=dict(color="#FF9F43", width=2.5, dash="dot"),
    fill="tozeroy", fillcolor="rgba(255,159,67,0.08)",
))
fig_dual.add_trace(go.Scatter(
    x=wf_df["date"], y=wf_df["avg_weight_kg"],
    name="น้ำหนักตัว (kg)", yaxis="y2",
    line=dict(color="#4A90D9", width=3),
    mode="lines+markers", marker=dict(size=5),
))
fig_dual.update_layout(
    template="plotly_white", height=420,
    xaxis=dict(title="วันที่", showgrid=False),
    yaxis=dict(
        title=dict(text="ปริมาณอาหาร (กรัม)", font=dict(color="#FF9F43")),
        tickfont=dict(color="#FF9F43"),
    ),
    yaxis2=dict(
        title=dict(text="น้ำหนักตัว (kg)", font=dict(color="#4A90D9")),
        tickfont=dict(color="#4A90D9"),
        overlaying="y", side="right",
    ),
    legend=dict(orientation="h", yanchor="bottom", y=1.02),
    margin=dict(t=10, b=40), hovermode="x unified",
    plot_bgcolor="#FFFAF4", paper_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_dual, use_container_width=True)

# Correlation Insight
with st.expander("🔍 วิเคราะห์ความสัมพันธ์ (Pearson Correlation)"):
    if not wf_df.empty and wf_df["avg_weight_kg"].notna().sum() > 2:
        corr = wf_df["total_food_g"].corr(wf_df["avg_weight_kg"])
        col_a, col_b = st.columns([1, 3])
        col_a.metric("Correlation", f"{corr:.3f}")
        with col_b:
            if corr > 0.6:
                st.success("✅ ความสัมพันธ์สูง — กินมากขึ้น น้ำหนักเพิ่มตามสัดส่วน")
            elif corr > 0.3:
                st.info("ℹ️ ความสัมพันธ์ปานกลาง — ปัจจัยอื่นอาจมีผล")
            elif corr >= 0:
                st.warning("⚠️ ความสัมพันธ์ต่ำ — ควรตรวจสอบกิจกรรมอื่น")
            else:
                st.error("❗ ความสัมพันธ์เป็นลบ — ควรปรึกษาสัตวแพทย์")
    else:
        st.info("ต้องการข้อมูลอย่างน้อย 3 วันเพื่อคำนวณ Correlation")

# ─── Feline BMI, Body Condition Score (BCS) & Nutrition Intelligence ──────────
st.markdown("---")
st.subheader("🩺 การวิเคราะห์ดัชนีมวลกายสัตว์เลี้ยง & โภชนาการ (Feline BMI & BCS)")
st.caption("อ้างอิงเกณฑ์ประเมินสรีระแมวสากล Body Condition Score (WSAVA / AAHA Guidelines 1-9 Scale)")

# หาข้อมูลแมวตัวที่เลือก
cur_cat_name = selected_cat if selected_cat != "ทั้งหมด" else (cats_df["name"].iloc[0] if not cats_df.empty else "น้องสามสี")
cat_row = cats_df[cats_df["name"] == cur_cat_name] if not cats_df.empty else pd.DataFrame()

cur_breed = cat_row["breed"].iloc[0] if not cat_row.empty and pd.notna(cat_row["breed"].iloc[0]) else "Scottish Fold"
cur_gender = cat_row["gender"].iloc[0] if not cat_row.empty and pd.notna(cat_row["gender"].iloc[0]) else "male"
cur_weight = latest_w if latest_w else 4.5

# คำนวณ BCS และความต้องการพลังงาน
bcs_info = estimate_feline_bcs(cur_weight, cur_breed, cur_gender)
energy_info = calculate_energy_needs(cur_weight, bcs_info["bcs"])

col_gauge, col_details = st.columns([1, 1.4])

with col_gauge:
    # Plotly Gauge Chart สำหรับ BCS 1-9
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=bcs_info["bcs"],
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"<b>คะแนน BCS: {bcs_info['bcs']} / 9</b><br><span style='font-size:0.85em;color:{bcs_info['color']}'>{bcs_info['status']}</span>", 'font': {'size': 18, 'color': '#2C3E50'}},
        gauge={
            'axis': {'range': [1, 9], 'tickwidth': 1, 'tickcolor': "#2C3E50", 'tickmode': 'linear', 'tick0': 1, 'dtick': 1},
            'bar': {'color': bcs_info['color'], 'thickness': 0.3},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#ddd",
            'steps': [
                {'range': [1, 3.5], 'color': 'rgba(52, 152, 219, 0.25)'},    # ผอม (Blue)
                {'range': [3.5, 5.5], 'color': 'rgba(46, 204, 113, 0.35)'},   # สมส่วน (Green)
                {'range': [5.5, 7.5], 'color': 'rgba(241, 196, 15, 0.3)'},    # ท้วม (Yellow)
                {'range': [7.5, 9.0], 'color': 'rgba(231, 76, 60, 0.3)'},     # อ้วน (Red)
            ],
            'threshold': {
                'line': {'color': "#2C3E50", 'width': 4},
                'thickness': 0.75,
                'value': bcs_info['bcs']
            }
        }
    ))
    fig_gauge.update_layout(
        height=320,
        margin=dict(l=25, r=25, t=50, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        font={'family': "Sarabun, sans-serif"}
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_details:
    st.markdown(f"""<div style="background:white;border-radius:14px;padding:1.2rem;box-shadow:0 3px 12px rgba(0,0,0,0.05);border-left:5px solid {bcs_info['color']};margin-top:10px">
<h4 style="margin:0 0 8px;color:#2C3E50">📋 ผลการวินิจฉัยสรีระ: {cur_cat_name}</h4>
<p style="margin:4px 0;font-size:0.92rem">🧬 <b>สายพันธุ์:</b> {bcs_info['breed_name']} ({cur_breed})</p>
<p style="margin:4px 0;font-size:0.92rem">⚖️ <b>น้ำหนักปัจจุบัน:</b> <span style="font-weight:700;color:{bcs_info['color']}">{cur_weight:.2f} kg</span></p>
<p style="margin:4px 0;font-size:0.92rem">🎯 <b>ช่วงน้ำหนักมาตรฐานสายพันธุ์:</b> <b>{bcs_info['ideal_min']:.2f} – {bcs_info['ideal_max']:.2f} kg</b> (ค่าเฉลี่ย {bcs_info['ideal_mid']:.2f} kg)</p>
<p style="margin:4px 0;font-size:0.92rem">📊 <b>ส่วนต่างจากน้ำหนักอุดมคติ:</b> {'+' if bcs_info['diff_kg'] > 0 else ''}{bcs_info['diff_kg']} kg ({'+' if bcs_info['diff_pct'] > 0 else ''}{bcs_info['diff_pct']}%)</p>
<hr style="margin:10px 0;border:none;border-top:1px dashed #eee">
<p style="margin:0;font-size:0.85rem;color:#666">💡 <i>{bcs_info['description']}</i></p>
</div>""", unsafe_allow_html=True)

# ─── Daily Nutrition Advisor Cards ───
st.markdown("#### 🍽️ ปริมาณพลังงานและอาหารที่แนะนำต่อวัน (Nutrition Advisor)")
st.caption("คำนวณตามหลักสัตวแพทย์: RER (Resting Energy) & DER (Daily Energy Requirement)")

c_n1, c_n2, c_n3, c_n4 = st.columns(4)
c_n1.metric("🔥 พลังงานพักผ่อน (RER)", f"{energy_info['rer_kcal']:.1f} kcal", help="พลังงานขั้นต่ำที่ใช้ในการดำรงชีวิตขณะพักผ่อน")
c_n2.metric("⚡ พลังงานที่ต้องการ (DER)", f"{energy_info['der_kcal']:.1f} kcal", f"Factor {energy_info['factor']}x ({energy_info['goal']})")
c_n3.metric("🥣 อาหารเม็ดแนะนำ", f"{energy_info['dry_food_g']:.0f} กรัม/วัน", "~380 kcal/100g")
c_n4.metric("🥫 อาหารเปียกแนะนำ", f"{energy_info['wet_food_g']:.0f} กรัม/วัน", "~85 kcal/ซอง")

# ─── Chart 3: Weight Trend with Healthy Corridor Tunnel ───
st.markdown("#### 📉 แนวโน้มน้ำหนักเทียบกับ Safe Healthy Corridor")
st.caption("เส้นกราฟแสดงน้ำหนักจริงเทียบกับแถบสีเขียวที่เป็นช่วงน้ำหนักสุขภาพดีตามสายพันธุ์")

if not wf_df.empty:
    wf_dates = wf_df["date"]
    fig_corridor = go.Figure()

    # แถบพื้นที่ Healthy Range (Shaded Corridor)
    fig_corridor.add_trace(go.Scatter(
        x=pd.concat([wf_dates, wf_dates[::-1]]),
        y=[bcs_info['ideal_max']] * len(wf_dates) + [bcs_info['ideal_min']] * len(wf_dates),
        fill='toself',
        fillcolor='rgba(46, 204, 113, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name="Healthy Weight Corridor (ช่วงสุขภาพดี)"
    ))

    # เส้นน้ำหนักจริง
    fig_corridor.add_trace(go.Scatter(
        x=wf_dates,
        y=wf_df["avg_weight_kg"],
        mode='lines+markers',
        name='น้ำหนักจริง (kg)',
        line=dict(color='#2C3E50', width=3),
        marker=dict(size=7, color=bcs_info['color'])
    ))

    fig_corridor.update_layout(
        template="plotly_white",
        height=350,
        xaxis=dict(title="วันที่", showgrid=False),
        yaxis=dict(
            title="น้ำหนัก (kg)",
            range=[max(1.0, bcs_info['ideal_min'] - 1.0), bcs_info['ideal_max'] + 1.2]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        margin=dict(t=10, b=40),
        plot_bgcolor="#FFFAF4",
        paper_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_corridor, use_container_width=True)
