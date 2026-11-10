"""
app/feline_health.py
────────────────────
ระบบคำนวณและประเมินสุขภาพสัตว์เลี้ยง (Feline Health & Nutrition Engine)
อ้างอิงตามหลักมาตรฐานสัตวแพทย์สากล (AAHA / WSAVA Nutritional Assessment Guidelines):
1. Body Condition Score (BCS 1-9) & Feline BMI
2. Resting Energy Requirement (RER) & Daily Energy Requirement (DER)
3. Breed Weight Standard Corridors (ช่วงน้ำหนักตามสายพันธุ์)
4. Safe Weight Velocity Alert (เตือนภาวะน้ำหนักลดเร็วเกินไป - เสี่ยงไขมันเกาะตับ)
"""

import math
from typing import Dict, Any, Tuple

# ─── ฐานข้อมูลช่วงน้ำหนักมาตรฐานตามสายพันธุ์ (กก.) ────────────────────────────
BREED_STANDARDS: Dict[str, Dict[str, Any]] = {
    "scottish fold": {
        "male": (3.5, 5.5),
        "female": (2.7, 4.2),
        "default": (3.0, 5.0),
        "thai_name": "สก็อตติช โฟลด์",
        "frame": "medium",
        "description": "โครงสร้างกลมกระดูกปานกลาง เสี่ยงปัญหาข้อต่อหากน้ำหนักเกิน"
    },
    "british shorthair": {
        "male": (4.5, 7.5),
        "female": (3.5, 5.5),
        "default": (4.0, 6.5),
        "thai_name": "บริติช ช็อตแฮร์",
        "frame": "large",
        "description": "โครงสร้างหนาล่ำ (Cobby body) กล้ามเนื้อแน่น น้ำหนักตามสายพันธุ์ค่อนข้างสูง"
    },
    "korat": {
        "male": (3.5, 4.8),
        "female": (2.8, 3.8),
        "default": (3.0, 4.5),
        "thai_name": "แมวไทยโคราช (สีสวาด)",
        "frame": "semi-cobby",
        "description": "กล้ามเนื้อกระชับ แข็งแรง คล่องแคล่ว ไม่ควรมีไขมันสะสมที่หน้าท้องหนา"
    },
    "แมวไทย": {
        "male": (3.2, 4.8),
        "female": (2.5, 3.8),
        "default": (3.0, 4.5),
        "thai_name": "แมวไทย / ศุภลักษณ์ / วิเชียรมาศ",
        "frame": "slender",
        "description": "ลำตัวเพรียวยาว คล่องตัวสูง"
    },
    "persian": {
        "male": (3.8, 5.5),
        "female": (3.0, 4.5),
        "default": (3.2, 5.0),
        "thai_name": "เปอร์เซีย",
        "frame": "medium",
        "description": "กระดูกใหญ่ ขนหนา ควรจับคลำกระดูกซี่โครงเพื่อวัดความอ้วนจริง"
    },
    "maine coon": {
        "male": (6.5, 10.5),
        "female": (4.5, 7.0),
        "default": (5.5, 9.0),
        "thai_name": "เมนคูน",
        "frame": "very-large",
        "description": "แมวสายพันธุ์ใหญ่ที่สุดในโลก เติบโตเต็มที่เมื่ออายุ 3-5 ปี"
    },
    "general": {
        "male": (3.5, 5.2),
        "female": (2.8, 4.2),
        "default": (3.0, 4.8),
        "thai_name": "แมวทั่วไป / ลูกผสม",
        "frame": "medium",
        "description": "ค่าเฉลี่ยสำหรับแมวเลี้ยงในบ้านทั่วไป"
    }
}


def get_breed_info(breed_name: str, gender: str = "female") -> Dict[str, Any]:
    """ดึงข้อมูลช่วงน้ำหนักมาตรฐานตามสายพันธุ์และเพศ"""
    if not breed_name:
        b_key = "general"
    else:
        name_lower = breed_name.lower()
        matched = "general"
        for k in BREED_STANDARDS:
            if k in name_lower or BREED_STANDARDS[k]["thai_name"].lower() in name_lower:
                matched = k
                break
        b_key = matched

    info = BREED_STANDARDS[b_key]
    g_key = "male" if "male" in gender.lower() or "ผู้" in gender else "female"
    weight_range = info.get(g_key, info["default"])
    ideal_mid = round((weight_range[0] + weight_range[1]) / 2.0, 2)

    return {
        "breed_key": b_key,
        "thai_name": info["thai_name"],
        "min_weight": weight_range[0],
        "max_weight": weight_range[1],
        "ideal_mid": ideal_mid,
        "description": info["description"]
    }


def estimate_feline_bcs(current_weight: float, breed_name: str = "", gender: str = "female") -> Dict[str, Any]:
    """
    ประเมินระดับ Body Condition Score (BCS 1-9) จากน้ำหนักเทียบกับค่ามาตรฐานสายพันธุ์
    1-3: ผอมเกินไป (Underweight)
    4-5: สมส่วน สมบูรณ์แบบ (Ideal)
    6-7: ท้วม / เริ่มอ้วน (Overweight)
    8-9: โรคอ้วน (Obese)
    """
    info = get_breed_info(breed_name, gender)
    min_w = info["min_weight"]
    max_w = info["max_weight"]
    mid_w = info["ideal_mid"]

    if current_weight <= 0:
        ratio = 1.0
    else:
        ratio = current_weight / mid_w

    # แปลง Ratio เป็นระดับ BCS 1-9
    # อ้างอิง: แมวที่มีน้ำหนักเกินอุดมคติ 10-15% จะมีคะแนน BCS เพิ่ม 1 ระดับ
    if ratio < 0.70:
        bcs = 1
        status = "ผอมแห้งมาก (Emaciated)"
        color = "#3498DB"
        tag = "underweight"
    elif ratio < 0.82:
        bcs = 2
        status = "ผอมบาง (Very Thin)"
        color = "#2980B9"
        tag = "underweight"
    elif ratio < 0.92:
        bcs = 3
        status = "ค่อนข้างผอม (Underweight)"
        color = "#1ABC9C"
        tag = "underweight"
    elif ratio <= 1.08:
        # ช่วงสมส่วน
        bcs = 5 if ratio >= 1.0 else 4
        status = "สมส่วนสุขภาพดีเยี่ยม (Ideal Condition)"
        color = "#2ECC71"
        tag = "ideal"
    elif ratio <= 1.20:
        bcs = 6
        status = "เริ่มท้วม / มีไขมันสะสม (Slightly Overweight)"
        color = "#F1C40F"
        tag = "overweight"
    elif ratio <= 1.35:
        bcs = 7
        status = "น้ำหนักเกิน (Overweight)"
        color = "#E67E22"
        tag = "overweight"
    elif ratio <= 1.50:
        bcs = 8
        status = "ภาวะโรคอ้วน (Obese)"
        color = "#E74C3C"
        tag = "obese"
    else:
        bcs = 9
        status = "อ้วนรุนแรงขั้นวิกฤต (Severely Obese)"
        color = "#962D22"
        tag = "obese"

    # คำนวณความต่างจากน้ำหนักอุดมคติ
    diff_kg = round(current_weight - mid_w, 2)
    diff_pct = round(((current_weight - mid_w) / mid_w) * 100, 1)

    return {
        "bcs": bcs,
        "status": status,
        "tag": tag,
        "color": color,
        "ratio": ratio,
        "current_weight": current_weight,
        "ideal_min": min_w,
        "ideal_max": max_w,
        "ideal_mid": mid_w,
        "diff_kg": diff_kg,
        "diff_pct": diff_pct,
        "breed_name": info["thai_name"],
        "description": info["description"]
    }


def calculate_energy_needs(weight_kg: float, bcs: int, is_neutered: bool = True) -> Dict[str, Any]:
    """
    คำนวณพลังงานที่แมวต้องการต่อวันตามหลักโภชนาการสัตวแพทย์:
    - RER (Resting Energy Requirement) = 70 * (Weight)^0.75
    - DER (Daily Energy Requirement) = RER * Factor ตามสถานะร่างกาย
    """
    if weight_kg <= 0:
        return {"rer": 0, "der": 0, "dry_food_grams": 0, "wet_food_grams": 0}

    # พลังงานขณะพักผ่อน (kcal/day)
    rer = 70.0 * math.pow(weight_kg, 0.75)

    # Multiplier ตามสภาวะร่างกาย (AAHA Nutritional Guidelines)
    if bcs <= 3:
        # ต้องการเพิ่มน้ำหนัก
        factor = 1.4 if is_neutered else 1.6
        goal = "เพิ่มน้ำหนักเสริมสร้างกล้ามเนื้อ"
    elif bcs in (4, 5):
        # รักษาน้ำหนักมาตรฐาน
        factor = 1.2 if is_neutered else 1.4
        goal = "รักษาน้ำหนักและสุขภาพที่สมดุล"
    elif bcs in (6, 7):
        # ควบคุมน้ำหนักอย่างปลอดภัย (ลดไขมันสะสม)
        factor = 1.0
        goal = "ควบคุมน้ำหนักและลดไขมันหน้าท้องอย่างปลอดภัย"
    else:
        # โรคอ้วน (ลดพลังงานอย่างเข้มงวด)
        factor = 0.8
        goal = "โปรแกรมลดน้ำหนักเพื่อสุขภาพ ป้องกันโรคตับและเบาหวาน"

    der = rer * factor

    # ประมาณการปริมาณอาหาร:
    # อาหารเม็ดเฉลี่ย 380 kcal / 100g -> ~3.8 kcal/g
    # อาหารเปียกเฉลี่ย 85 kcal / 85g ซอง -> ~1.0 kcal/g
    dry_food_g = round(der / 3.8, 1)
    wet_food_g = round(der / 1.0, 1)

    return {
        "rer_kcal": round(rer, 1),
        "der_kcal": round(der, 1),
        "factor": factor,
        "goal": goal,
        "dry_food_g": dry_food_g,
        "wet_food_g": wet_food_g,
        "recommended_portions": "แบ่งให้วันละ 2-3 มื้อเพื่อระบบย่อยอาหารที่ดี"
    }

