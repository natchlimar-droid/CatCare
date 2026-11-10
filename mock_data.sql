-- =============================================================================
-- CatCare — Mockup Dataset for GitHub Showcase & Portfolio
-- Database: PostgreSQL
-- Description: Realistic dummy data for Demo User, Cats, Activities, Expenses & Reminders
-- =============================================================================

BEGIN;

-- 1. Demo User (Password: demo1234, hashed with bcrypt)
INSERT INTO users (id, username, email, hashed_password, display_name, gender, is_active, created_at)
VALUES (
    'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d',
    'demo_user',
    'demo@catcare.io',
    '$2b$12$Z0H9x5n3p2mE1qY/Y8J2teG3GvhB3q/49h/ZqP7lQ3Yh8jW3F2Q9K',
    'Natcha & Cats',
    'female',
    true,
    NOW() - INTERVAL '60 days'
) ON CONFLICT (username) DO NOTHING;

-- 2. Cats Profiles
INSERT INTO cats (id, name, breed, gender, birth_date, color, profile_image_url, is_active, created_at, owner_id)
VALUES 
(
    '11111111-1111-1111-1111-111111111111',
    'ส้มซ่า (Somza)',
    'Scottish Fold',
    'male',
    CURRENT_DATE - INTERVAL '2 years',
    'ส้มแถบขาว (Orange Tabby)',
    'https://images.unsplash.com/photo-1574158622682-e40e69881006?q=80&w=600&auto=format&fit=crop',
    true,
    NOW() - INTERVAL '60 days',
    'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d'
),
(
    '22222222-2222-2222-2222-222222222222',
    'มิดไนท์ (Midnight)',
    'British Shorthair',
    'female',
    CURRENT_DATE - INTERVAL '1 year',
    'ดำสนิท (Solid Black)',
    'https://images.unsplash.com/photo-1514888286974-6c03e2ca1dba?q=80&w=600&auto=format&fit=crop',
    true,
    NOW() - INTERVAL '60 days',
    'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d'
),
(
    '33333333-3333-3333-3333-333333333333',
    'ถุงทอง (Thungthong)',
    'แมวไทยโคราช (Korat)',
    'male',
    CURRENT_DATE - INTERVAL '16 months',
    'สวาด / เทาเงิน (Silver-Blue)',
    'https://images.unsplash.com/photo-1543852786-1cf6624b9987?q=80&w=600&auto=format&fit=crop',
    true,
    NOW() - INTERVAL '60 days',
    'a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d'
) ON CONFLICT (id) DO NOTHING;

-- 3. Activities: Weight History (for Dashboard Charts)
INSERT INTO activities (id, cat_id, activity_type, recorded_at, weight_kg, notes, created_at)
VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '35 days', 4.10, 'ชั่งน้ำหนักตรวจสุขภาพประจำสัปดาห์', NOW() - INTERVAL '35 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '28 days', 4.20, 'สุขภาพดี ร่าเริง กินอาหารปกติ', NOW() - INTERVAL '28 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '21 days', 4.30, 'น้ำหนักขึ้นตามเกณฑ์', NOW() - INTERVAL '21 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '14 days', 4.40, 'เริ่มคุมปริมาณอาหารเม็ดเล็กน้อย', NOW() - INTERVAL '14 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '7 days',  4.45, 'ขนแน่นเงางาม น้ำหนักคงที่', NOW() - INTERVAL '7 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'weight', NOW() - INTERVAL '1 day',   4.50, 'สุขภาพแข็งแรงสมบูรณ์', NOW() - INTERVAL '1 day'),

(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'weight', NOW() - INTERVAL '28 days', 3.20, 'ตรวจติดตามน้ำหนักหลังทำหมัน', NOW() - INTERVAL '28 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'weight', NOW() - INTERVAL '14 days', 3.35, 'ปรับสูตรอาหารเป็นสูตรแมวทำหมัน', NOW() - INTERVAL '14 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'weight', NOW() - INTERVAL '2 days',  3.45, 'น้ำหนักอยู่ในเกณฑ์มาตรฐาน', NOW() - INTERVAL '2 days');

-- Activities: Recent Eating & Litter Logs
INSERT INTO activities (id, cat_id, activity_type, recorded_at, food_brand, food_type, food_amount_g, litter_type, notes, created_at)
VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'eating', NOW() - INTERVAL '4 hours', 'Royal Canin Indoor', 'dry', 45.0, NULL, 'กินหมดเกลี้ยง อารมณ์ดี', NOW() - INTERVAL '4 hours'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'litter', NOW() - INTERVAL '2 hours', NULL, NULL, NULL, 'urine', 'ปัสสาวะก้อนกลม สีปกติ', NOW() - INTERVAL '2 hours'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'eating', NOW() - INTERVAL '3 hours', 'Kaniva Salmon', 'wet', 70.0, NULL, 'ชอบรสแซลมอนมาก', NOW() - INTERVAL '3 hours'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'eating', NOW() - INTERVAL '5 hours', 'Purina ONE', 'dry', 50.0, NULL, 'กินตามเวลาปกติ', NOW() - INTERVAL '5 hours');

-- 4. Expenses
INSERT INTO expenses (id, cat_id, category, amount, description, expense_date, created_at)
VALUES
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'vet', 850.00, 'ตรวจสุขภาพประจำปี + ตรวจเลือด', CURRENT_DATE - INTERVAL '20 days', NOW() - INTERVAL '20 days'),
(gen_random_uuid(), '11111111-1111-1111-1111-111111111111', 'medicine', 350.00, 'ยาหยอดหลัง Revolution Plus ป้องกันเห็บหมัดและพยาธิ', CURRENT_DATE - INTERVAL '15 days', NOW() - INTERVAL '15 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'food', 1250.00, 'อาหารเม็ด Kaniva 10kg + อาหารเปียก 1 โหล', CURRENT_DATE - INTERVAL '12 days', NOW() - INTERVAL '12 days'),
(gen_random_uuid(), '33333333-3333-3333-3333-333333333333', 'toy', 290.00, 'คอนโดแมวกล่องกระดาษ + ไม้ตกแมว', CURRENT_DATE - INTERVAL '10 days', NOW() - INTERVAL '10 days'),
(gen_random_uuid(), NULL, 'litter', 580.00, 'ทรายแมวเต้าหู้กลิ่นชาเขียว 4 ถุง (ใช้ร่วมกัน)', CURRENT_DATE - INTERVAL '7 days', NOW() - INTERVAL '7 days'),
(gen_random_uuid(), '22222222-2222-2222-2222-222222222222', 'medicine', 450.00, 'วัคซีนป้องกันโรคหัด-หวัดแมว (FVRCP)', CURRENT_DATE - INTERVAL '5 days', NOW() - INTERVAL '5 days');

-- 5. Reminders
INSERT INTO reminders (id, cat_id, reminder_type, title, description, due_date, due_time, is_recurring, recurrence_days, notify_before_days, status, created_at, updated_at)
VALUES
(
    gen_random_uuid(),
    '11111111-1111-1111-1111-111111111111',
    'vaccine',
    'ฉีดวัคซีนพิษสุนัขบ้า (Rabies Vaccine)',
    'พาน้องส้มซ่าไปฉีดวัคซีนกระตุ้นประจำปีที่ รพ.สัตว์ทองหล่อ',
    CURRENT_DATE + INTERVAL '5 days',
    '10:00:00',
    false,
    NULL,
    3,
    'pending',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    '22222222-2222-2222-2222-222222222222',
    'medicine',
    'หยอดยาป้องกันเห็บหมัดรอบถัดไป',
    'หยอด Revolution Plus บริเวณหลังคอ',
    CURRENT_DATE + INTERVAL '15 days',
    '20:00:00',
    true,
    30,
    2,
    'pending',
    NOW(),
    NOW()
),
(
    gen_random_uuid(),
    '33333333-3333-3333-3333-333333333333',
    'vet',
    'นัดขูดหินปูนและตรวจสุขภาพช่องปาก',
    'งดน้ำและอาหาร 8 ชั่วโมงก่อนพบสัตวแพทย์',
    CURRENT_DATE + INTERVAL '25 days',
    '09:30:00',
    false,
    NULL,
    3,
    'pending',
    NOW(),
    NOW()
);

COMMIT;

