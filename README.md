# 🐱 CatCare — Pet Health, Activity & Expense Management System

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16%2B-336791.svg)](https://www.postgresql.org/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0%2B-red.svg)](https://www.sqlalchemy.org/)
[![Alembic](https://img.shields.io/badge/Alembic-Migration-orange.svg)](https://alembic.sqlalchemy.org/)
[![LINE API](https://img.shields.io/badge/LINE-Messaging%20API-00C300.svg)](https://developers.line.biz/)

**CatCare** คือระบบจัดการและดูแลสุขภาพแมวแบบครบวงจร (Full-Stack Pet Care Platform) ออกแบบมาเพื่อช่วยให้เจ้าของแมวสามารถติดตามสุขภาพ น้ำหนัก อาหาร บันทึกค่าใช้จ่าย และระบบแจ้งเตือนการฉีดวัคซีน/นัดหมายคุณหมอผ่าน LINE อัตโนมัติ

---

## 🌟 จุดเด่นของโปรเจกต์ (Key Features)

- 🐾 **Multi-Cat Profile**: จัดการประวัติแมวหลายตัวได้พร้อมกัน (สายพันธุ์, วันเกิด, สีขน, รูปโปรไฟล์)
- 🩺 **Feline BMI & Body Condition Score (BCS 1-9)**: ประเมินดัชนีมวลกายสรีระตามเกณฑ์สัตวแพทย์สากล WSAVA/AAHA พร้อมกราฟ Safe Weight Corridor และตัวคำนวณพลังงาน RER / DER
- 🪪 **Digital Pet Passport & QR Code**: พาสปอร์ตดิจิทัลแสดงประวัติวัคซีนครบถ้วน พร้อม QR Code สำหรับสแกนเข้าคลินิกหรือโรงแรมแมว
- 🥣 **Smart Mixed Feeding Portion Matcher**: คำนวณสัดส่วนอาหารเม็ดผสมอาหารเปียกให้ได้แคลอรีตรงเป้าหมายพอดี 100%
- 🪣 **Smart Litter & Renal Health AI**: วิเคราะห์ก้อนปัสสาวะและความถี่ คัดกรองความเสี่ยงโรคนิ่วและโรคไตล่วงหน้า
- 👨‍👩‍👧‍👦 **Family Care Group & LINE Group Sync**: ระบบบ้านร่วมดูแลแมวสำหรับครอบครัว พร้อมรหัสเชิญ **Family Invite Code (`CAT-FAM-7734`)** และ **Dynamic QR Code** ให้คนในบ้านสแกนเข้าร่วมทันที เชื่อมต่อบอทเข้ากลุ่ม LINE เพื่อ Broadcast การให้อาหารและป้อนยาแบบ Real-Time ป้องกันการให้ซ้ำซ้อน
- 💬 **LINE Messaging API Rich Flex**: ส่งการ์ดแจ้งเตือนแบบ Interactive Rich UI พร้อมปุ่ม Action (กดบันทึกว่าฉีดแล้ว / ป้อนยาแล้ว จากแชต LINE ได้ทันที)
- 🚨 **Toxic Plants & Food Radar**: สารานุกรมค้นหาพืชมีพิษและอาหารอันตราย พร้อมเบอร์โทรฉุกเฉินโรงพยาบาลสัตว์ 24 ชม.
- 💸 **Expense Tracker**: วิเคราะห์ค่าใช้จ่ายแยกหมวดหมู่ (ค่ารักษา, อาหาร, ทรายแมว, ยา, ของเล่น) พร้อมสรุปยอดรวม
- 📱 **Mobile Application UI Design**: ออกแบบ UI สไตล์ Mobile App (One-Handed Navigation, Bottom Bar, Soft Pastel Palette) ตอบโจทย์คนเลี้ยงสัตว์ยุคใหม่
- 🔐 **Secure Authentication & Dual Database**: ระบบสมัครสมาชิก/เข้าสู่ระบบ JWT Bcrypt พร้อม SQLite Fallback และ PostgreSQL Production Ready

---

## 🏗️ สถาปัตยกรรมระบบ (System Architecture)

```mermaid
flowchart TD
    subgraph UI ["Frontend / Dashboard"]
        ST["Streamlit Web App (:8501)"]
        UI_DIR["HTML/Tailwind UI"]
    end

    subgraph Backend ["FastAPI Backend (:8080)"]
        API["FastAPI App (Async / Sync)"]
        AUTH["JWT / Bcrypt Auth"]
        ROUTERS["Routers (/cats, /auth)"]
    end

    subgraph Database ["PostgreSQL Database"]
        PG[("PostgreSQL\n(catcare_db)")]
        ALEMBIC["Alembic Migrations"]
    end

    subgraph Worker ["Background Worker & Notification"]
        SCHED["APScheduler Job"]
        LINE["LINE Messaging API"]
    end

    ST -->|Query / API| Backend
    Backend -->|SQLAlchemy / asyncpg| PG
    ALEMBIC -->|DDL Migration| PG
    SCHED -->|Check Reminders| PG
    SCHED -->|Send Alert| LINE
```

---

## 🗄️ โครงสร้างฐานข้อมูล (Entity Relationship Diagram)

```mermaid
erDiagram
    USERS ||--o{ CATS : owns
    CATS ||--o{ ACTIVITIES : logs
    CATS ||--o{ EXPENSES : incurs
    CATS ||--o{ REMINDERS : schedules

    USERS {
        uuid id PK
        string username UK
        string email UK
        string hashed_password
        string display_name
        string gender
        boolean is_active
        timestamp created_at
        timestamp last_login
    }

    CATS {
        uuid id PK
        uuid owner_id FK
        string name
        string breed
        string gender
        date birth_date
        string color
        text profile_image_url
        boolean is_active
        timestamp created_at
    }

    ACTIVITIES {
        uuid id PK
        uuid cat_id FK
        string activity_type "weight | eating | litter | drinking"
        float weight_kg
        string food_brand
        string food_type "dry | wet | treat"
        float food_amount_g
        string litter_type "urine | feces"
        timestamp recorded_at
        text notes
    }

    EXPENSES {
        uuid id PK
        uuid cat_id FK
        string category "food | vet | medicine | toy | litter | other"
        numeric amount
        string description
        date expense_date
        timestamp created_at
    }

    REMINDERS {
        uuid id PK
        uuid cat_id FK
        string reminder_type "vaccine | medicine | vet | other"
        string title
        text description
        date due_date
        time due_time
        boolean is_recurring
        int recurrence_days
        string status "pending | notified | done"
    }
```

---

## 🚀 เริ่มต้นใช้งานอย่างรวดเร็ว (Quick Start)

### 1. โคลน Repository และสร้าง Virtual Environment
```bash
git clone https://github.com/natchlimar-droid/CatCare.git
cd CatCare

python -m venv .venv
# บน Windows
.venv\Scripts\activate
# บน macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. ตั้งค่าตัวแปรสภาพแวดล้อม (Environment Variables)
คัดลอกไฟล์ `.env.example` เป็น `.env`:
```bash
cp .env.example .env
```
แก้ไขการเชื่อมต่อ PostgreSQL ในไฟล์ `.env`:
```env
DATABASE_URL=postgresql://catcare_user:yourpassword@localhost:5432/catcare_db
```

### 3. รัน Migration เพื่อสร้างตารางใน Database
```bash
alembic upgrade head
```

### 4. นำเข้าข้อมูล Mockup สำหรับทดสอบ (Seed Data)
สามารถสร้างข้อมูลจำลองที่มีประวัติแมว, บันทึกน้ำหนัก, ค่าใช้จ่าย และการแจ้งเตือน ได้ใน 1 คำสั่ง:
```bash
python seed_data.py
```
*(หรือจะ import ไฟล์ `mock_data.sql` เข้า PostgreSQL โดยตรงก็ได้เช่นกัน)*

---

## 🎮 ข้อมูลเข้าสู่ระบบสำหรับการทดสอบ (Demo Account)

หลังจากรัน `python seed_data.py` แล้ว สามารถใช้บัญชีตัวอย่างนี้เข้าใช้งานได้ทันที:

- **Username**: `demo_user`
- **Password**: `demo1234`
- **ข้อมูลแมวตัวอย่าง**: 3 ตัว (ส้มซ่า, มิดไนท์, ถุงทอง) พร้อมกราฟน้ำหนักและประวัติการรักษาครบถ้วน

---

## 🏃 การรันแอปพลิเคชัน (Running Application)

### เปิดรันผ่าน Script อัตโนมัติ (Windows)
```cmd
run.bat
```

### หรือรันแยกแต่ละ Service:
1. **รัน API Server (FastAPI)**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
   ```
   - เข้าดู Swagger API Docs ได้ที่: [http://localhost:8080/docs](http://localhost:8080/docs)

2. **รัน Web Dashboard (Streamlit)**:
   ```bash
   streamlit run dashboard/dashboard.py
   ```
   - เข้าใช้งาน Dashboard ได้ที่: [http://localhost:8501](http://localhost:8501)

---

## 📁 โครงสร้างโปรเจกต์ (Project Directory)

```text
CatCare/
├── alembic/                # Database Migrations & Version Control
│   └── versions/           # ไฟล์ Migration สร้างตาราง
├── app/                    # Backend API (FastAPI) & Health Engine
│   ├── routers/            # Endpoint แยกโมดูล (Auth, Cats, ฯลฯ)
│   ├── database.py         # SQLAlchemy Engine & Session Configuration
│   ├── models.py           # SQLAlchemy ORM Models
│   ├── feline_health.py    # Feline BCS, BMI & Nutrition Calculation Engine
│   └── main.py             # FastAPI App Entrypoint
├── automation/             # Scheduler & LINE Notification Services
├── dashboard/              # Streamlit Web Analytics Dashboard
│   ├── pages/
│   │   ├── 0_🔐_Login.py           # ระบบ Login / Register พร้อมปุ่ม Auto-Fill Demo
│   │   ├── 1_📝_Daily_Entry.py     # บันทึกกิจวัตรประจำวัน & ไดนามิกการ์ดแจ้งเตือน
│   │   ├── 2_🔔_Reminders.py       # จัดการและกดเสร็จสิ้นการแจ้งเตือน
│   │   ├── 3_🪪_Pet_Passport.py    # พาสปอร์ตดิจิทัล + QR Code + คำนวณอาหารเม็ด/เปียก
│   │   └── 4_🏥_Smart_Health_AI.py # วิเคราะห์ก้อนฉี่/ไต + เวรดูแลครอบครัว + LINE Flex
│   ├── dashboard.py        # หน้าหลัก Analytics, ค่าใช้จ่าย, กราฟน้ำหนัก & BCS Gauge
│   └── db_queries.py       # รวมคำสั่งดึงข้อมูลข้ามระบบแบบ Dialect-Agnostic
├── ui/                     # Interactive HTML/CSS/JS Web App (FastAPI Static)
├── seed_data.py            # สคริปต์สร้าง Mockup Data สำหรับ Demo / Showcase
├── mock_data.sql           # ไฟล์ SQL Mockup Data สำหรับนำเข้าตรง
├── .env.example            # ตัวอย่างการตั้งค่า Environment Variables
├── .gitignore              # ละเว้นไฟล์ความลับและ Cache จาก Git
├── requirements.txt        # รายการ Dependencies ทั้งหมด
└── README.md               # เอกสารแนะนำโปรเจกต์
```

---

## 📄 ใบอนุญาต (License)
Project นี้เผยแพร่ภายใต้ [MIT License](LICENSE) เพื่อการศึกษาและการนำเสนอผลงาน (Portfolio Showcase)

