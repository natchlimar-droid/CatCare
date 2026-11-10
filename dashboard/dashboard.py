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

sys.path.insert(0, os.path.dirname(__file__))
from db_queries import (
    is_db_available, get_all_cats, get_expense_summary_by_month,
    get_expense_kpi, get_weight_food_trend, get_latest_weight,
)

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
