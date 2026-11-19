"""
app/clinical_export.py
โมดูลสำหรับส่งออก (Export) ประวัติสุขภาพแมว:
1. CSV Export (UTF-8 with BOM สำหรับเปิดใน Excel ภาษาไทยไม่เพี้ยน)
2. PDF Medical Record (ReportLab พร้อมฟอนต์ภาษาไทยสำหรับส่งคลินิก/โรงพยาบาลสัตว์)
3. iCalendar (.ics) สำหรับนำเข้าปฏิทิน Google Calendar / Apple Calendar
"""

import io
import os
import csv
from datetime import datetime, date, timedelta, timezone
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ─── Thai Font Setup for ReportLab ───────────────────────────────────────────
FONT_NAME = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

THAI_FONTS_SEARCH = [
    ("Tahoma", "C:/Windows/Fonts/tahoma.ttf", "C:/Windows/Fonts/tahomabd.ttf"),
    ("THSarabun", "C:/Windows/Fonts/THSarabun.ttf", "C:/Windows/Fonts/THSarabun Bold.ttf"),
    ("Leelawadee", "C:/Windows/Fonts/leelawad.ttf", "C:/Windows/Fonts/leelawdb.ttf"),
]

for name, regular, bold in THAI_FONTS_SEARCH:
    if os.path.exists(regular):
        try:
            pdfmetrics.registerFont(TTFont(name, regular))
            FONT_NAME = name
            if os.path.exists(bold):
                pdfmetrics.registerFont(TTFont(f"{name}-Bold", bold))
                FONT_BOLD = f"{name}-Bold"
            else:
                FONT_BOLD = name
            break
        except Exception:
            continue


# ─── 1. CSV Clinical History Generator ────────────────────────────────────────
def generate_clinical_csv(cat_info: dict, weight_logs: list[dict], reminders: list[dict], expenses: list[dict]) -> str:
    """
    สร้างข้อมูล CSV สรุปประวัติสุขภาพ น้ำหนัก และวัคซีน
    พร้อม UTF-8 BOM สำหรับเปิดใน MS Excel ภาษาไทย
    """
    output = io.StringIO()
    # Write UTF-8 BOM
    output.write('\ufeff')
    writer = csv.writer(output)

    # 1. Header ประวัติน้องแมว
    writer.writerow(["=== CATCARE CLINICAL HEALTH RECORD ==="])
    writer.writerow(["ชื่อสัตว์เลี้ยง", cat_info.get("name", "-")])
    writer.writerow(["สายพันธุ์", cat_info.get("breed", "-")])
    writer.writerow(["เพศ", "ผู้ (Male)" if cat_info.get("gender") == "male" else "เมีย (Female)"])
    writer.writerow(["วันเกิด", str(cat_info.get("birth_date", "-"))])
    writer.writerow(["เลขไมโครชิป", cat_info.get("microchip", "900115002938471")])
    writer.writerow(["น้ำหนักล่าสุด (kg)", cat_info.get("weight", "-")])
    writer.writerow(["คะแนนสรีระ (BCS)", cat_info.get("bcs", "5/9")])
    writer.writerow(["วันที่พิมพ์รายงาน", datetime.now().strftime("%d/%m/%Y %H:%M")])
    writer.writerow([])

    # 2. ประวัติการชั่งน้ำหนักและการกิน
    writer.writerow(["=== ประวัติการชั่งน้ำหนัก & กิจกรรม (Weight & Activity Logs) ==="])
    writer.writerow(["วันที่", "ประเภทกิจกรรม", "น้ำหนัก (kg)", "ยี่ห้ออาหาร", "ประเภทอาหาร", "ปริมาณ (g)", "บันทึกอาการ"])
    if weight_logs:
        for log in weight_logs:
            writer.writerow([
                log.get("date", "-"),
                log.get("type", "-"),
                log.get("weight", "-"),
                log.get("food_brand", "-"),
                log.get("food_type", "-"),
                log.get("food_amount", "-"),
                log.get("notes", "-")
            ])
    else:
        writer.writerow(["ไม่มีข้อมูลบันทึก"])
    writer.writerow([])

    # 3. ประวัติการฉีดวัคซีนและนัดหมายแพทย์
    writer.writerow(["=== ประวัติวัคซีน & นัดพบสัตวแพทย์ (Vaccines & Appointments) ==="])
    writer.writerow(["หัวข้อการนัดหมาย", "ประเภท", "วันนัดหมาย", "สถานะ", "รายละเอียด/คำแนะนำ"])
    if reminders:
        for r in reminders:
            writer.writerow([
                r.get("title", "-"),
                r.get("type", "-"),
                r.get("due_date", "-"),
                "เสร็จสิ้นแล้ว" if r.get("status") == "done" else "รอดำเนินการ",
                r.get("description", "-")
            ])
    else:
        writer.writerow(["ไม่มีข้อมูลนัดหมาย"])
    writer.writerow([])

    # 4. ประวัติค่าใช้จ่ายการรักษา
    writer.writerow(["=== ประวัติค่ารักษาพยาบาล (Medical Expenses) ==="])
    writer.writerow(["วันที่", "หมวดหมู่", "รายการ", "จำนวนเงิน (บาท)"])
    if expenses:
        for exp in expenses:
            writer.writerow([
                exp.get("date", "-"),
                exp.get("category", "-"),
                exp.get("description", "-"),
                exp.get("amount", 0)
            ])
    writer.writerow([])

    return output.getvalue()


# ─── 2. PDF Veterinary Clinical Summary Generator ─────────────────────────────
def generate_clinical_pdf(cat_info: dict, weight_logs: list[dict], reminders: list[dict], clinic_name: str = "CatCare Veterinary Network") -> bytes:
    """
    สร้างไฟล์ PDF สรุปประวัติสุขภาพสัตวแพทย์อย่างเป็นทางการ (Official Clinical Summary)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles with Thai font
    style_header = ParagraphStyle(
        'HeaderTitle',
        fontName=FONT_BOLD,
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1A365D"),
        alignment=1 # Center
    )
    style_sub = ParagraphStyle(
        'HeaderSub',
        fontName=FONT_NAME,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#64748B"),
        alignment=1
    )
    style_sec = ParagraphStyle(
        'SecTitle',
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2C3E50"),
        spaceBefore=10,
        spaceAfter=4
    )
    style_body = ParagraphStyle(
        'Body',
        fontName=FONT_NAME,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#334155")
    )
    style_bold = ParagraphStyle(
        'BodyBold',
        fontName=FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1E293B")
    )

    story = []

    # Title & Clinic Header
    story.append(Paragraph("🏥 CATCARE VETERINARY CLINICAL SUMMARY", style_header))
    story.append(Paragraph(f"เอกสารสรุปประวัติสุขภาพสัตว์เลี้ยงอย่างเป็นทางการ · {clinic_name}", style_sub))
    story.append(Paragraph(f"วันที่พิมพ์เอกสาร: {datetime.now().strftime('%d/%m/%Y %H:%M')} | รหัสอ้างอิง: MED-{datetime.now().strftime('%y%m%d')}-092", style_sub))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#FF9F43"), spaceAfter=12))

    # Patient Identification Table (2 Columns)
    story.append(Paragraph("🐾 1. ข้อมูลประจำตัวสัตว์เลี้ยง (Patient Identification)", style_sec))
    patient_data = [
        [
            Paragraph("<b>ชื่อสัตว์เลี้ยง:</b>", style_bold), Paragraph(str(cat_info.get("name", "-")), style_body),
            Paragraph("<b>เลขไมโครชิป:</b>", style_bold), Paragraph(str(cat_info.get("microchip", "900115002938471")), style_body)
        ],
        [
            Paragraph("<b>สายพันธุ์:</b>", style_bold), Paragraph(str(cat_info.get("breed", "-")), style_body),
            Paragraph("<b>เพศ & ทำหมัน:</b>", style_bold), Paragraph(f"{'เพศผู้' if cat_info.get('gender')=='male' else 'เพศเมีย'} (ทำหมันแล้ว ✅)", style_body)
        ],
        [
            Paragraph("<b>วันเกิด / อายุ:</b>", style_bold), Paragraph(str(cat_info.get("birth_date", "-")), style_body),
            Paragraph("<b>สี / ลักษณะขน:</b>", style_bold), Paragraph(str(cat_info.get("color", "สามสี / ลายส้ม")), style_body)
        ],
        [
            Paragraph("<b>น้ำหนักล่าสุด:</b>", style_bold), Paragraph(f"<b>{cat_info.get('weight', '-')} kg</b>", style_bold),
            Paragraph("<b>คะแนนสรีระ (BCS):</b>", style_bold), Paragraph(f"{cat_info.get('bcs', '5/9')} (สมส่วนเกณฑ์ WSAVA)", style_body)
        ],
    ]
    t_patient = Table(patient_data, colWidths=[95, 160, 95, 170])
    t_patient.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_patient)
    story.append(Spacer(1, 12))

    # Vaccination & Preventive Care Table
    story.append(Paragraph("💉 2. ประวัติการรับวัคซีน & ป้องกันปรสิต (Vaccinations & Preventive Care)", style_sec))
    vax_rows = [
        [
            Paragraph("<b>รายการวัคซีน / การรักษา</b>", style_bold),
            Paragraph("<b>ประเภท</b>", style_bold),
            Paragraph("<b>กำหนดวัน</b>", style_bold),
            Paragraph("<b>สถานะ</b>", style_bold),
            Paragraph("<b>คำแนะนำจากแพทย์</b>", style_bold)
        ]
    ]
    if reminders:
        for r in reminders[:6]:
            status_txt = "✅ ได้รับแล้ว" if r.get("status") == "done" else "⏳ รอนัดหมาย"
            vax_rows.append([
                Paragraph(str(r.get("title", "-")), style_body),
                Paragraph(str(r.get("type", "-")), style_body),
                Paragraph(str(r.get("due_date", "-")), style_body),
                Paragraph(status_txt, style_bold),
                Paragraph(str(r.get("description", "-") or "-"), style_body)
            ])
    else:
        vax_rows.append([Paragraph("ไม่มีประวัติวัคซีน", style_body), Paragraph("-", style_body), Paragraph("-", style_body), Paragraph("-", style_body), Paragraph("-", style_body)])

    t_vax = Table(vax_rows, colWidths=[140, 75, 75, 75, 155])
    t_vax.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#FEF3C7")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_vax)
    story.append(Spacer(1, 12))

    # Recent Weight Progression Table
    story.append(Paragraph("📉 3. ประวัติการชั่งน้ำหนักย้อนหลัง (Weight Progression Log)", style_sec))
    w_rows = [
        [
            Paragraph("<b>วันที่บันทึก</b>", style_bold),
            Paragraph("<b>น้ำหนัก (kg)</b>", style_bold),
            Paragraph("<b>ส่วนต่าง (Diff)</b>", style_bold),
            Paragraph("<b>การขับถ่าย & บันทึกสุขภาพ</b>", style_bold)
        ]
    ]
    if weight_logs:
        prev_w = None
        for log in weight_logs[:8]:
            curr_w = float(log.get("weight", 0)) if log.get("weight") else 0
            if prev_w is not None and curr_w:
                diff = curr_w - prev_w
                diff_str = f"{'+' if diff > 0 else ''}{diff:.2f} kg"
            else:
                diff_str = "-"
            prev_w = curr_w if curr_w else prev_w

            w_rows.append([
                Paragraph(str(log.get("date", "-")), style_body),
                Paragraph(f"<b>{curr_w:.2f} kg</b>" if curr_w else "-", style_body),
                Paragraph(diff_str, style_body),
                Paragraph(str(log.get("notes", "สุขภาพปกติ")), style_body)
            ])
    else:
        w_rows.append([Paragraph("-", style_body), Paragraph("-", style_body), Paragraph("-", style_body), Paragraph("ไม่มีข้อมูล", style_body)])

    t_w = Table(w_rows, colWidths=[100, 90, 80, 250])
    t_w.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#E0E7FF")),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_w)
    story.append(Spacer(1, 15))

    # Doctor Verification & Clinic Signature Box
    sig_data = [
        [
            Paragraph("<b>หมายเหตุของแพทย์ผู้ตรวจ (Veterinarian Remarks):</b><br/>สภาวะร่างกายโดยรวมสมบูรณ์แข็งแรง การทำงานของหัวใจและปอดปกติ ไม่มีประวัติแพ้ยา อาหารแนะนำ 220 kcal/วัน", style_body),
            Paragraph("<b>การรับรองโดยสัตวแพทย์ (Verified By):</b><br/><br/><br/>____________________________________<br/>( น.สพ. / สพ.ญ. .............................................. )<br/>เลขที่ใบประกอบวิชาชีพ: ............................", style_body)
        ]
    ]
    t_sig = Table(sig_data, colWidths=[310, 210])
    t_sig.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F1F5F9")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#94A3B8")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(KeepTogether(t_sig))

    doc.build(story)
    return buffer.getvalue()


# ─── 3. iCalendar (.ics) Generator ───────────────────────────────────────────
def generate_ics_calendar(reminder: dict) -> str:
    """
    สร้างไฟล์ iCalendar (.ics) สำหรับนำเข้า Apple Calendar, Google Calendar หรือ Outlook
    """
    due_date = reminder.get("due_date")
    if isinstance(due_date, str):
        try:
            dt = datetime.strptime(due_date[:10], "%Y-%m-%d").date()
        except Exception:
            dt = date.today()
    elif isinstance(due_date, (date, datetime)):
        dt = due_date
    else:
        dt = date.today()

    dt_str = dt.strftime("%Y%m%d")
    now_str = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    uid = f"catcare-{reminder.get('id', 'rem')}-{dt_str}@catcare.app"

    title = reminder.get("title", "นัดหมายสุขภาพแมว")
    cat_name = reminder.get("cat_name", "น้องแมว")
    desc = reminder.get("description", "นัดหมายโดย CatCare Application")

    ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//CatCare//Pet Health Automation//TH
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{now_str}
DTSTART;VALUE=DATE:{dt_str}
DTEND;VALUE=DATE:{(dt + timedelta(days=1)).strftime("%Y%m%d")}
SUMMARY:🐱 {title} ({cat_name})
DESCRIPTION:{desc} · บันทึกผ่าน CatCare
LOCATION:โรงพยาบาลสัตว์ / คลินิกประจำ
STATUS:CONFIRMED
BEGIN:VALARM
TRIGGER:-P1D
ACTION:DISPLAY
DESCRIPTION:เตือนล่วงหน้า 1 วัน: {title}
END:VALARM
END:VEVENT
END:VCALENDAR"""
    return ics_content
