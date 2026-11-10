"""
seed_data.py — สคริปต์สร้าง Mockup Data สำหรับโปรเจกต์ CatCare
ใช้รันเมื่อต้องการข้อมูลจำลองสำหรับนำเสนอผลงานบน GitHub / Portfolio
คำสั่งรัน: python seed_data.py
"""

import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from app.database import SyncSessionLocal
from app.routers.auth import hash_password
from sqlalchemy import text


def seed():
    print("🐱 CatCare — Populating Mockup Data for Showcase / Portfolio...")
    print("=" * 60)

    db = SyncSessionLocal()
    try:
        # ตรวจสอบการเชื่อมต่อ
        db.execute(text("SELECT 1"))

        # ล้างข้อมูลเดิมของ demo ถ้าต้องการเริ่มใหม่สะอาดๆ (optional)
        print("🧹 Checking existing demo data...")
        db.execute(text("DELETE FROM users WHERE username = 'demo_user'"))
        db.commit()

        # 1. สร้าง Demo User
        user_id = str(uuid.uuid4())
        hashed_pw = hash_password("demo1234")
        now = datetime.now(timezone.utc)

        db.execute(
            text("""
                INSERT INTO users (id, username, email, hashed_password, display_name, gender, is_active, created_at)
                VALUES (:id, :username, :email, :hashed_password, :display_name, :gender, true, :created_at)
            """),
            {
                "id": user_id,
                "username": "demo_user",
                "email": "demo@catcare.io",
                "hashed_password": hashed_pw,
                "display_name": "Natcha & Cats",
                "gender": "female",
                "created_at": now
            }
        )
        print("✅ Created Demo User: demo_user (password: demo1234)")

        # 2. สร้างข้อมูลแมวจำลอง (3 ตัว ละเอียด น่ารัก มีบุคลิก)
        cat_somza_id = str(uuid.uuid4())
        cat_midnight_id = str(uuid.uuid4())
        cat_thungthong_id = str(uuid.uuid4())

        cats_data = [
            {
                "id": cat_somza_id,
                "name": "ส้มซ่า (Somza)",
                "breed": "Scottish Fold",
                "gender": "male",
                "birth_date": date.today() - timedelta(days=730), # ~2 ขวบ
                "color": "ส้มแถบขาว (Orange Tabby)",
                "profile_image_url": "https://images.unsplash.com/photo-1574158622682-e40e69881006?q=80&w=600&auto=format&fit=crop",
                "owner_id": user_id,
                "created_at": now - timedelta(days=60)
            },
            {
                "id": cat_midnight_id,
                "name": "มิดไนท์ (Midnight)",
                "breed": "British Shorthair",
                "gender": "female",
                "birth_date": date.today() - timedelta(days=365), # ~1 ขวบ
                "color": "ดำสนิท (Solid Black)",
                "profile_image_url": "https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=600&auto=format&fit=crop",
                "owner_id": user_id,
                "created_at": now - timedelta(days=60)
            },
            {
                "id": cat_thungthong_id,
                "name": "ถุงทอง (Thungthong)",
                "breed": "แมวไทยโคราช (Korat)",
                "gender": "male",
                "birth_date": date.today() - timedelta(days=500),
                "color": "สวาด / เทาเงิน (Silver-Blue)",
                "profile_image_url": "https://images.unsplash.com/photo-1543852786-1cf6624b9987?q=80&w=600&auto=format&fit=crop",
                "owner_id": user_id,
                "created_at": now - timedelta(days=60)
            }
        ]

        for c in cats_data:
            db.execute(
                text("""
                    INSERT INTO cats (id, name, breed, gender, birth_date, color, profile_image_url, is_active, created_at, owner_id)
                    VALUES (:id, :name, :breed, :gender, :birth_date, :color, :profile_image_url, true, :created_at, :owner_id)
                """),
                c
            )
        print("✅ Created 3 Cats Profile (Somza, Midnight, Thungthong)")

        # 3. สร้างประวัติสุขภาพและกิจกรรมย้อนหลัง (Activities: น้ำหนัก, อาหาร, ขับถ่าย)
        # ให้กราฟน้ำหนักใน Dashboard แสดงแนวโน้มสวยงาม
        somza_weights = [4.1, 4.2, 4.25, 4.3, 4.35, 4.4, 4.45, 4.5]
        midnight_weights = [3.2, 3.25, 3.3, 3.35, 3.4, 3.42, 3.45, 3.5]
        thungthong_weights = [3.8, 3.85, 3.9, 3.9, 3.95, 4.0, 4.02, 4.05]

        for i, w in enumerate(somza_weights):
            rec_date = now - timedelta(days=(len(somza_weights) - i) * 7)
            db.execute(
                text("""
                    INSERT INTO activities (id, cat_id, activity_type, recorded_at, weight_kg, food_brand, food_type, food_amount_g, notes, created_at)
                    VALUES (:id, :cat_id, 'weight', :recorded_at, :weight_kg, NULL, NULL, NULL, :notes, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "cat_id": cat_somza_id,
                    "recorded_at": rec_date,
                    "weight_kg": w,
                    "notes": f"ชั่งน้ำหนักประจำสัปดาห์ สุขภาพแข็งแรงดี ร่าเริง",
                    "created_at": rec_date
                }
            )

        for i, w in enumerate(midnight_weights):
            rec_date = now - timedelta(days=(len(midnight_weights) - i) * 7)
            db.execute(
                text("""
                    INSERT INTO activities (id, cat_id, activity_type, recorded_at, weight_kg, food_brand, food_type, food_amount_g, notes, created_at)
                    VALUES (:id, :cat_id, 'weight', :recorded_at, :weight_kg, NULL, NULL, NULL, :notes, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "cat_id": cat_midnight_id,
                    "recorded_at": rec_date,
                    "weight_kg": w,
                    "notes": "น้ำหนักคงที่ กินเก่ง",
                    "created_at": rec_date
                }
            )

        # บันทึกการกินอาหารและกระบะทรายล่าสุด
        activities_recent = [
            (cat_somza_id, "eating", now - timedelta(hours=3), None, "Royal Canin Indoor", "dry", 45.0, None, "กินหมดเกลี้ยง"),
            (cat_somza_id, "litter", now - timedelta(hours=2), None, None, None, None, "urine", "ปัสสาวะสีปกติ ก้อนกลม"),
            (cat_midnight_id, "eating", now - timedelta(hours=4), None, "Kaniva Salmon & Tuna", "wet", 70.0, None, "ชอบอาหารเปียกรสปลา"),
            (cat_midnight_id, "litter", now - timedelta(hours=1), None, None, None, None, "feces", "ขับถ่ายเป็นก้อนสวย ไม่ท้องเสีย"),
            (cat_thungthong_id, "eating", now - timedelta(hours=5), None, "Purina ONE Indoor", "dry", 50.0, None, "กินตามเวลาปกติ")
        ]

        for cid, atype, rec_at, w, fbrand, ftype, famount, ltype, notes in activities_recent:
            db.execute(
                text("""
                    INSERT INTO activities (id, cat_id, activity_type, recorded_at, weight_kg, food_brand, food_type, food_amount_g, litter_type, notes, created_at)
                    VALUES (:id, :cat_id, :activity_type, :recorded_at, :weight_kg, :food_brand, :food_type, :food_amount_g, :litter_type, :notes, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "cat_id": cid,
                    "activity_type": atype,
                    "recorded_at": rec_at,
                    "weight_kg": w,
                    "food_brand": fbrand,
                    "food_type": ftype,
                    "food_amount_g": famount,
                    "litter_type": ltype,
                    "notes": notes,
                    "created_at": rec_at
                }
            )
        print("✅ Created Activity logs (Weight trends, Food records, Litter habits)")

        # 4. สร้างค่าใช้จ่ายจำลอง (Expenses: อาหาร, ทราย, หมอ, วัคซีน, ขนม)
        expenses_data = [
            (cat_somza_id, "vet", 850.00, "ตรวจสุขภาพประจำปี + ตรวจเลือด", date.today() - timedelta(days=20)),
            (cat_somza_id, "medicine", 350.00, "ยาหยอดหลังป้องกันเห็บหมัดและพยาธิหนอนหัวใจ (Revolution Plus)", date.today() - timedelta(days=15)),
            (cat_midnight_id, "food", 1250.00, "อาหารเม็ด Kaniva 10kg + อาหารเปียก 1 โหล", date.today() - timedelta(days=12)),
            (cat_thungthong_id, "toy", 290.00, "คอนโดแมวทรงกล่องกระดาษ + ไม้ตกแมวขนนก", date.today() - timedelta(days=10)),
            (None, "litter", 580.00, "ทรายแมวเต้าหู้กลิ่นชาเขียว 4 ถุง (ใช้รวมกัน)", date.today() - timedelta(days=7)),
            (cat_midnight_id, "medicine", 450.00, "วัคซีนป้องกันโรคหัด-หวัดแมว (FVRCP)", date.today() - timedelta(days=5)),
            (cat_somza_id, "food", 180.00, "ขนมแมวเลีย Ciao Churu รสปลาแซลมอน", date.today() - timedelta(days=2))
        ]

        for cid, catg, amt, desc, edate in expenses_data:
            db.execute(
                text("""
                    INSERT INTO expenses (id, cat_id, category, amount, description, expense_date, created_at)
                    VALUES (:id, :cat_id, :category, :amount, :description, :expense_date, :created_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "cat_id": cid,
                    "category": catg,
                    "amount": amt,
                    "description": desc,
                    "expense_date": edate,
                    "created_at": datetime.combine(edate, datetime.min.time(), tzinfo=timezone.utc)
                }
            )
        print("✅ Created Expense records (Vet, Medicine, Food, Toys, Litter)")

        # 5. สร้างการแจ้งเตือนจำลอง (Reminders: วัคซีน, ป้อนยา, นัดคุณหมอ)
        reminders_data = [
            (
                cat_somza_id, "vaccine", "ฉีดวัคซีนพิษสุนัขบ้า (Rabies Vaccine)",
                "พาน้องส้มซ่าไปฉีดวัคซีนกระตุ้นประจำปีที่ รพ.สัตว์ทองหล่อ",
                date.today() + timedelta(days=5), "10:00:00", False, None, 3, "pending"
            ),
            (
                cat_midnight_id, "medicine", "หยอดยาป้องกันเห็บหมัดรอบถัดไป",
                "หยอด Revolution Plus บริเวณหลังคอ",
                date.today() + timedelta(days=15), "20:00:00", True, 30, 2, "pending"
            ),
            (
                cat_thungthong_id, "vet", "นัดขูดหินปูนและตรวจสุขภาพช่องปาก",
                "งดน้ำและอาหาร 8 ชั่วโมงก่อนพบสัตวแพทย์",
                date.today() + timedelta(days=25), "09:30:00", False, None, 3, "pending"
            ),
            (
                cat_somza_id, "medicine", "ป้อนวิตามินบำรุงขนและผิวหนัง",
                "ผสมเจลวิตามินกับอาหารเช้า",
                date.today(), "08:00:00", True, 1, 0, "done"
            )
        ]

        for cid, rtype, title, desc, due_d, due_t, is_rec, rec_d, notif_b, status in reminders_data:
            db.execute(
                text("""
                    INSERT INTO reminders (id, cat_id, reminder_type, title, description, due_date, due_time, is_recurring, recurrence_days, notify_before_days, status, created_at, updated_at)
                    VALUES (:id, :cat_id, :reminder_type, :title, :description, :due_date, :due_time, :is_recurring, :recurrence_days, :notify_before_days, :status, :created_at, :updated_at)
                """),
                {
                    "id": str(uuid.uuid4()),
                    "cat_id": cid,
                    "reminder_type": rtype,
                    "title": title,
                    "description": desc,
                    "due_date": due_d,
                    "due_time": due_t,
                    "is_recurring": is_rec,
                    "recurrence_days": rec_d,
                    "notify_before_days": notif_b,
                    "status": status,
                    "created_at": now,
                    "updated_at": now
                }
            )
        print("✅ Created Reminders (Vaccines, Flea treatment, Vet appointments)")

        db.commit()
        print("=" * 60)
        print("🎉 Successfully generated mockup data for CatCare Showcase!")
        print("   Username : demo_user")
        print("   Password : demo1234")
        print("   Cats     : 3 profiles with activities, expenses & reminders")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()

