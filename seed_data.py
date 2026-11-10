"""
seed_data.py — สคริปต์สร้าง Mockup Data สำหรับโปรเจกต์ CatCare
รองรับทั้ง SQLite (Local/Standalone) และ PostgreSQL (Production)
คำสั่งรัน: python seed_data.py
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from app.database import sync_engine, SyncSessionLocal
from app.models import Base, User, Cat, Activity, Expense, Reminder, FamilyGroup, FamilyMember
from app.routers.auth import hash_password


def seed():
    print("🐱 CatCare — Populating Mockup Data for Showcase / Portfolio...")
    print("=" * 60)

    # 1. สร้างตารางทั้งหมดโดยอัตโนมัติหากยังไม่มี (รองรับทั้ง SQLite และ PostgreSQL)
    print("🛠️ Creating tables if not exist...")
    Base.metadata.create_all(bind=sync_engine)

    db = SyncSessionLocal()
    try:
        # 2. ตรวจสอบ/ล้าง demo user เก่า
        existing_user = db.query(User).filter(User.username == "demo_user").first()
        if existing_user:
            print("🧹 Cleaning existing demo data...")
            db.delete(existing_user)
            db.commit()

        # 3. สร้าง Demo User
        now = datetime.now(timezone.utc)
        user = User(
            id=uuid.uuid4(),
            username="demo_user",
            email="demo@catcare.io",
            hashed_password=hash_password("demo1234"),
            display_name="Natcha & Cats",
            gender="female",
            is_active=True,
            created_at=now
        )
        db.add(user)
        db.flush()
        print("✅ Created Demo User: demo_user (password: demo1234)")

        # 4. สร้างข้อมูลแมวจำลอง (3 ตัว ละเอียด น่ารัก มีบุคลิก)
        cat_somza = Cat(
            id=uuid.uuid4(),
            name="ส้มซ่า (Somza)",
            breed="Scottish Fold",
            gender="male",
            birth_date=date.today() - timedelta(days=730),
            color="ส้มแถบขาว (Orange Tabby)",
            profile_image_url="https://images.unsplash.com/photo-1574158622682-e40e69881006?q=80&w=600&auto=format&fit=crop",
            is_active=True,
            created_at=now - timedelta(days=60),
            owner_id=user.id
        )

        cat_midnight = Cat(
            id=uuid.uuid4(),
            name="มิดไนท์ (Midnight)",
            breed="British Shorthair",
            gender="female",
            birth_date=date.today() - timedelta(days=365),
            color="ดำสนิท (Solid Black)",
            profile_image_url="https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=600&auto=format&fit=crop",
            is_active=True,
            created_at=now - timedelta(days=60),
            owner_id=user.id
        )

        cat_thungthong = Cat(
            id=uuid.uuid4(),
            name="ถุงทอง (Thungthong)",
            breed="แมวไทยโคราช (Korat)",
            gender="male",
            birth_date=date.today() - timedelta(days=500),
            color="สวาด / เทาเงิน (Silver-Blue)",
            profile_image_url="https://images.unsplash.com/photo-1543852786-1cf6624b9987?q=80&w=600&auto=format&fit=crop",
            is_active=True,
            created_at=now - timedelta(days=60),
            owner_id=user.id
        )

        db.add_all([cat_somza, cat_midnight, cat_thungthong])
        db.flush()
        print("✅ Created 3 Cats Profiles (Somza, Midnight, Thungthong)")

        # 5. กิจกรรมและประวัติน้ำหนัก (Activities)
        somza_weights = [4.1, 4.2, 4.25, 4.3, 4.35, 4.4, 4.45, 4.5]
        for i, w in enumerate(somza_weights):
            rec_date = now - timedelta(days=(len(somza_weights) - i) * 7)
            db.add(Activity(
                id=uuid.uuid4(),
                cat_id=cat_somza.id,
                activity_type="weight",
                recorded_at=rec_date,
                weight_kg=w,
                notes="ชั่งน้ำหนักตรวจสุขภาพประจำสัปดาห์ ร่าเริง กินเก่ง",
                created_at=rec_date
            ))

        midnight_weights = [3.2, 3.25, 3.3, 3.35, 3.4, 3.42, 3.45, 3.5]
        for i, w in enumerate(midnight_weights):
            rec_date = now - timedelta(days=(len(midnight_weights) - i) * 7)
            db.add(Activity(
                id=uuid.uuid4(),
                cat_id=cat_midnight.id,
                activity_type="weight",
                recorded_at=rec_date,
                weight_kg=w,
                notes="ตรวจติดตามน้ำหนักหลังทำหมัน",
                created_at=rec_date
            ))

        # บันทึกการกินและขับถ่ายล่าสุด
        db.add_all([
            Activity(
                id=uuid.uuid4(),
                cat_id=cat_somza.id,
                activity_type="eating",
                recorded_at=now - timedelta(hours=3),
                food_brand="Royal Canin Indoor",
                food_type="dry",
                food_amount_g=45.0,
                notes="กินหมดเกลี้ยง อารมณ์ดี",
                created_at=now - timedelta(hours=3)
            ),
            Activity(
                id=uuid.uuid4(),
                cat_id=cat_somza.id,
                activity_type="litter",
                recorded_at=now - timedelta(hours=2),
                litter_type="urine",
                notes="ปัสสาวะก้อนกลม สีปกติ",
                created_at=now - timedelta(hours=2)
            ),
            Activity(
                id=uuid.uuid4(),
                cat_id=cat_midnight.id,
                activity_type="eating",
                recorded_at=now - timedelta(hours=4),
                food_brand="Kaniva Salmon",
                food_type="wet",
                food_amount_g=70.0,
                notes="ชอบอาหารเปียกรสปลา",
                created_at=now - timedelta(hours=4)
            ),
            Activity(
                id=uuid.uuid4(),
                cat_id=cat_thungthong.id,
                activity_type="eating",
                recorded_at=now - timedelta(hours=5),
                food_brand="Purina ONE",
                food_type="dry",
                food_amount_g=50.0,
                notes="กินตามเวลาปกติ",
                created_at=now - timedelta(hours=5)
            )
        ])
        print("✅ Created Activity logs (Weight progression, Food logs, Litter habits)")

        # 6. ค่าใช้จ่าย (Expenses)
        expenses = [
            Expense(id=uuid.uuid4(), cat_id=cat_somza.id, category="vet", amount=850.00, description="ตรวจสุขภาพประจำปี + ตรวจเลือด", expense_date=date.today() - timedelta(days=20), created_at=now - timedelta(days=20)),
            Expense(id=uuid.uuid4(), cat_id=cat_somza.id, category="medicine", amount=350.00, description="ยาหยอดหลัง Revolution Plus ป้องกันเห็บหมัดและพยาธิ", expense_date=date.today() - timedelta(days=15), created_at=now - timedelta(days=15)),
            Expense(id=uuid.uuid4(), cat_id=cat_midnight.id, category="food", amount=1250.00, description="อาหารเม็ด Kaniva 10kg + อาหารเปียก 1 โหล", expense_date=date.today() - timedelta(days=12), created_at=now - timedelta(days=12)),
            Expense(id=uuid.uuid4(), cat_id=cat_thungthong.id, category="toy", amount=290.00, description="คอนโดแมวกล่องกระดาษ + ไม้ตกแมว", expense_date=date.today() - timedelta(days=10), created_at=now - timedelta(days=10)),
            Expense(id=uuid.uuid4(), cat_id=None, category="litter", amount=580.00, description="ทรายแมวเต้าหู้กลิ่นชาเขียว 4 ถุง (ใช้ร่วมกัน)", expense_date=date.today() - timedelta(days=7), created_at=now - timedelta(days=7)),
            Expense(id=uuid.uuid4(), cat_id=cat_midnight.id, category="medicine", amount=450.00, description="วัคซีนป้องกันโรคหัด-หวัดแมว (FVRCP)", expense_date=date.today() - timedelta(days=5), created_at=now - timedelta(days=5))
        ]
        db.add_all(expenses)
        print("✅ Created Expense records (Vet, Medicine, Food, Toys, Litter)")

        # 7. แจ้งเตือน (Reminders)
        reminders = [
            Reminder(
                id=uuid.uuid4(),
                cat_id=None,  # ทั้งบ้าน
                reminder_type="litter",
                title="เปลี่ยนทรายแมว",
                description="Unicharm Dual Power",
                due_date=date.today() + timedelta(days=2),
                is_recurring=True,
                recurrence_days=14,
                notify_before_days=2,
                status="pending",
                created_at=now,
                updated_at=now
            ),
            Reminder(
                id=uuid.uuid4(),
                cat_id=cat_somza.id,
                reminder_type="vaccine",
                title="นัดฉีดวัคซีนรวม",
                description="FVRCP Booster ครั้งที่ 2",
                due_date=date.today() + timedelta(days=5),
                is_recurring=False,
                notify_before_days=3,
                status="pending",
                created_at=now,
                updated_at=now
            ),
            Reminder(
                id=uuid.uuid4(),
                cat_id=cat_midnight.id,
                reminder_type="medicine",
                title="ยาถ่ายพยาธิ",
                description="Drontal ครั้งที่ 1",
                due_date=date.today() + timedelta(days=7),
                is_recurring=True,
                recurrence_days=90,
                notify_before_days=2,
                status="pending",
                created_at=now,
                updated_at=now
            ),
            Reminder(
                id=uuid.uuid4(),
                cat_id=cat_thungthong.id,
                reminder_type="grooming",
                title="ตัดเล็บ",
                description="ทุก 4 สัปดาห์",
                due_date=date.today() + timedelta(days=10),
                is_recurring=True,
                recurrence_days=28,
                notify_before_days=1,
                status="pending",
                created_at=now,
                updated_at=now
            ),
            Reminder(
                id=uuid.uuid4(),
                cat_id=cat_thungthong.id,
                reminder_type="vet",
                title="นัดขูดหินปูนและตรวจสุขภาพช่องปาก",
                description="งดน้ำและอาหาร 8 ชั่วโมงก่อนพบสัตวแพทย์",
                due_date=date.today() + timedelta(days=25),
                is_recurring=False,
                notify_before_days=3,
                status="pending",
                created_at=now,
                updated_at=now
            )
        ]
        db.add_all(reminders)
        print("✅ Created Reminders (Vaccines, Flea prevention, Vet appointments)")

        # 8. สร้างกลุ่มครอบครัวจำลอง (Family Care Group) พร้อมสมาชิกและ LINE Group Link
        fam_group = FamilyGroup(
            id=uuid.uuid4(),
            name="บ้านสามแสบสตูดิโอ 🏠",
            invite_code="CAT-FAM-7734",
            created_by_id=user.id,
            line_group_id="C98341512ab78e0",
            is_line_linked=True,
            created_at=now
        )
        db.add(fam_group)
        db.flush()

        members = [
            FamilyMember(
                id=uuid.uuid4(),
                group_id=fam_group.id,
                user_id=user.id,
                nickname="ณัชชา (Natcha)",
                role="admin",
                avatar_emoji="👑",
                phone_or_line="@natcha_cat",
                joined_at=now - timedelta(days=60)
            ),
            FamilyMember(
                id=uuid.uuid4(),
                group_id=fam_group.id,
                user_id=None,
                nickname="คุณพ่อ (Dad)",
                role="caregiver",
                avatar_emoji="👨‍🦱",
                phone_or_line="LINE: dad_thong",
                joined_at=now - timedelta(days=45)
            ),
            FamilyMember(
                id=uuid.uuid4(),
                group_id=fam_group.id,
                user_id=None,
                nickname="คุณแม่ (Mom)",
                role="caregiver",
                avatar_emoji="👩‍🦰",
                phone_or_line="LINE: mom_wan",
                joined_at=now - timedelta(days=40)
            ),
            FamilyMember(
                id=uuid.uuid4(),
                group_id=fam_group.id,
                user_id=None,
                nickname="น้องเนย (Noey)",
                role="member",
                avatar_emoji="👧",
                phone_or_line="LINE: noey_meow",
                joined_at=now - timedelta(days=20)
            ),
        ]
        db.add_all(members)
        print("✅ Created Family Care Group: บ้านสามแสบสตูดิโอ (Invite: CAT-FAM-7734) with 4 Guardians")

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
