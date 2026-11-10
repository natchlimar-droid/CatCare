-- ========================================
-- Cat Care — PostgreSQL Setup via pgAdmin
-- วิธีรัน: เปิด pgAdmin → เลือก postgres DB
--          → Query Tool → วางโค้ดนี้ → F5
-- ========================================

-- 1. สร้าง User
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'catcare_user') THEN
    CREATE USER catcare_user WITH PASSWORD 'catcare2024';
    RAISE NOTICE 'Created user catcare_user';
  ELSE
    ALTER USER catcare_user WITH PASSWORD 'catcare2024';
    RAISE NOTICE 'Updated password for catcare_user';
  END IF;
END$$;

-- 2. สร้าง Database
SELECT 'CREATE DATABASE catcare_db OWNER catcare_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'catcare_db')\gexec

-- 3. Grant (รัน query นี้แยกใน catcare_db หรือรันทั้งหมดก็ได้)
-- GRANT ALL ON SCHEMA public TO catcare_user;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO catcare_user;
