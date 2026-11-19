"""
tests/test_core.py
Automated test suite for CatCare Platform
Verifies core algorithms, database queries, and clinical exports
"""

import os
import sys
import pytest
from datetime import date

# Add project root to sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from app.feline_health import estimate_feline_bcs, calculate_energy_needs, get_breed_info
from app.clinical_export import generate_clinical_csv, generate_clinical_pdf, generate_ics_calendar
from dashboard.db_queries import get_monthly_weight_health_stats, get_cat_full_medical_data


# ─── 1. Feline Health & BCS Tests ─────────────────────────────────────────────
def test_feline_bcs_evaluation():
    # Scottish Fold ideal weight is around 3.5 - 5.5 kg
    bcs_normal = estimate_feline_bcs(4.5, "Scottish Fold", "male")
    assert bcs_normal["bcs"] == 5
    assert "สมส่วน" in bcs_normal["status"]

    # Underweight test
    bcs_thin = estimate_feline_bcs(2.2, "Scottish Fold", "male")
    assert bcs_thin["bcs"] <= 3

    # Overweight test
    bcs_obese = estimate_feline_bcs(7.5, "Scottish Fold", "male")
    assert bcs_obese["bcs"] >= 8


def test_energy_needs_calculation():
    energy = calculate_energy_needs(4.0, bcs=5)
    assert energy["rer_kcal"] > 180
    assert energy["der_kcal"] > energy["rer_kcal"]
    assert energy["wet_food_g"] > 0
    assert energy["dry_food_g"] > 0


# ─── 2. Clinical Export Suite Tests ───────────────────────────────────────────
def test_clinical_csv_generation():
    cat = {"name": "น้องส้มซ่า", "breed": "Scottish Fold", "gender": "male", "birth_date": "2024-04-12", "weight": 4.5}
    logs = [{"date": "2026-11-10", "type": "น้ำหนัก", "weight": 4.5, "notes": "ปกติ"}]
    rems = [{"title": "ฉีดวัคซีน", "type": "vaccine", "due_date": "2026-11-20", "status": "pending"}]
    exps = [{"date": "2026-11-01", "category": "vet", "amount": 1200}]

    csv_data = generate_clinical_csv(cat, logs, rems, exps)
    assert csv_data.startswith("\ufeff") # Verify UTF-8 BOM
    assert "CATCARE CLINICAL HEALTH RECORD" in csv_data
    assert "น้องส้มซ่า" in csv_data


def test_clinical_pdf_generation():
    cat = {"name": "ส้มซ่า (Somza)", "breed": "Scottish Fold", "gender": "male", "weight": 4.5, "bcs": "5/9"}
    logs = [{"date": "10/11/2026", "weight": 4.5, "notes": "ปกติ"}]
    rems = [{"title": "ฉีดวัคซีนรวม", "type": "vaccine", "due_date": "20/11/2026", "status": "done"}]

    pdf_bytes = generate_clinical_pdf(cat, logs, rems)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 5000 # Valid generated PDF binary


def test_ics_calendar_generation():
    rem = {"id": "test-123", "title": "นัดฉีดวัคซีน", "cat_name": "ส้มซ่า", "due_date": date(2026, 11, 25), "description": "Booster"}
    ics_str = generate_ics_calendar(rem)
    assert "BEGIN:VCALENDAR" in ics_str
    assert "BEGIN:VEVENT" in ics_str
    assert "END:VCALENDAR" in ics_str
    assert "นัดฉีดวัคซีน" in ics_str


# ─── 3. Database Analytics Tests ──────────────────────────────────────────────
def test_monthly_health_analytics():
    stats = get_monthly_weight_health_stats()
    assert not stats.empty
    assert "avg_weight" in stats.columns
    assert "status" in stats.columns
    assert len(stats) >= 4


def test_cat_full_medical_data_fetch():
    data = get_cat_full_medical_data()
    assert "cat_info" in data
    assert "weight_logs" in data
    assert "reminders" in data
    assert "expenses" in data

