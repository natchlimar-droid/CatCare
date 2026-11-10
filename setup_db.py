"""
setup_db.py — สร้าง PostgreSQL Database + User
รัน: python setup_db.py <postgres_password>
ตัวอย่าง: python setup_db.py postgres
"""
import sys

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("❌ ไม่พบ psycopg2 กำลังติดตั้ง...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# ─── Config — แก้ไขตามที่ต้องการ ────────────────────────────────────────────
PG_HOST     = "127.0.0.1"   # ใช้ IPv4 ตรงๆ (localhost อาจ resolve เป็น ::1)
PG_PORT     = 5432
PG_SUPER    = "postgres"          # superuser (default: postgres)
DB_NAME     = "catcare_db"
DB_USER     = "catcare_user"
DB_PASS     = "catcare2024"       # รหัสผ่านสำหรับ catcare_user


def main():
    print("🐱 Cat Care — PostgreSQL Setup")
    print("=" * 45)

    # รับ password จาก argument (ไม่ต้องพิมในหน้าต่าง)
    if len(sys.argv) >= 2:
        pg_password = sys.argv[1]
        print(f"  password: {'*' * len(pg_password)}")
    else:
        pg_password = input("รหัสผ่าน postgres (พิมแล้วกด Enter): ").strip()

    if not pg_password:
        print("❌ ต้องใส่รหัสผ่าน เช่น: python setup_db.py postgres")
        sys.exit(1)

    # เชื่อมต่อ postgres database ด้วย superuser
    try:
        conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT,
            dbname="postgres",
            user=PG_SUPER,
            password=pg_password or None,
            connect_timeout=5,
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        print(f"✅ เชื่อมต่อ PostgreSQL สำเร็จ\n")
    except psycopg2.OperationalError as e:
        print(f"\n❌ เชื่อมต่อ PostgreSQL ไม่ได้: {e}")
        print("\nตรวจสอบ:")
        print("  1. PostgreSQL กำลังรันอยู่ใน Services หรือไม่?")
        print("  2. Host/Port ถูกต้องไหม? (ตอนนี้: localhost:5432)")
        print("  3. รหัสผ่าน superuser ถูกต้องไหม?")
        sys.exit(1)

    # 1. สร้าง User
    try:
        cur.execute(
            sql.SQL("CREATE USER {} WITH PASSWORD %s").format(sql.Identifier(DB_USER)),
            [DB_PASS]
        )
        print(f"✅ สร้าง user '{DB_USER}' สำเร็จ")
    except psycopg2.errors.DuplicateObject:
        # อัปเดต password ถ้ามี user อยู่แล้ว
        cur.execute(
            sql.SQL("ALTER USER {} WITH PASSWORD %s").format(sql.Identifier(DB_USER)),
            [DB_PASS]
        )
        print(f"⚠️  User '{DB_USER}' มีอยู่แล้ว — อัปเดตรหัสผ่านแล้ว")

    # 2. สร้าง Database
    try:
        cur.execute(
            sql.SQL("CREATE DATABASE {} OWNER {}").format(
                sql.Identifier(DB_NAME),
                sql.Identifier(DB_USER)
            )
        )
        print(f"✅ สร้าง database '{DB_NAME}' สำเร็จ")
    except psycopg2.errors.DuplicateDatabase:
        print(f"⚠️  Database '{DB_NAME}' มีอยู่แล้ว — ข้ามขั้นตอนนี้")

    cur.close()
    conn.close()

    # 3. เชื่อมต่อ catcare_db เพื่อ Grant schema
    try:
        conn2 = psycopg2.connect(
            host=PG_HOST, port=PG_PORT,
            dbname=DB_NAME,
            user=PG_SUPER,
            password=pg_password or None,
        )
        conn2.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur2 = conn2.cursor()
        cur2.execute(
            sql.SQL("GRANT ALL ON SCHEMA public TO {}").format(sql.Identifier(DB_USER))
        )
        cur2.execute(
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {}").format(
                sql.Identifier(DB_USER)
            )
        )
        cur2.close()
        conn2.close()
        print(f"✅ Grant สิทธิ์ schema public ให้ '{DB_USER}' สำเร็จ")
    except Exception as e:
        print(f"⚠️  Grant schema: {e}")

    # ─── สรุป ─────────────────────────────────────────────────────────────────
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{PG_HOST}:{PG_PORT}/{DB_NAME}"
    print(f"""
{'='*45}
✅ Setup เสร็จสมบูรณ์!

👉 เปิดไฟล์ .env แล้วแก้ไขบรรทัดนี้:
   DATABASE_URL={DATABASE_URL}

👉 จากนั้นรัน:
   alembic upgrade head

👉 แล้วรัน Streamlit:
   streamlit run dashboard/dashboard.py
{'='*45}
""")


if __name__ == "__main__":
    main()
