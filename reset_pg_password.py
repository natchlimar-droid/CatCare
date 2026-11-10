"""
reset_pg_password.py (v2)
=========================
ใช้ IPv4 (127.0.0.1) ทั้งหมด + trust ครอบคลุม IPv6 ด้วย
ต้องรันใน PowerShell ในฐานะ Administrator
"""
import os, sys, shutil, time, subprocess, ctypes
from pathlib import Path

NEW_PASSWORD    = "postgres"
PG_VERSION      = "16"
PG_SERVICE      = f"postgresql-x64-{PG_VERSION}"
PG_DATA         = Path(f"C:/Program Files/PostgreSQL/{PG_VERSION}/data")
PG_BIN          = Path(f"C:/Program Files/PostgreSQL/{PG_VERSION}/bin")
PG_HBA          = PG_DATA / "pg_hba.conf"
PG_HBA_BACKUP   = PG_DATA / "pg_hba.conf.bak"

def is_admin():
    try: return ctypes.windll.shell32.IsUserAnAdmin()
    except: return False

def svc(action):
    r = subprocess.run(["sc", action, PG_SERVICE], capture_output=True)
    time.sleep(5)
    return r.returncode == 0

def main():
    print("=" * 48, flush=True)
    print("  Reset PostgreSQL Password (v2)", flush=True)
    print("=" * 48, flush=True)

    if not is_admin():
        print("ERROR: ต้องรันในฐานะ Administrator!", flush=True)
        print("  คลิกขวา PowerShell -> Run as Administrator", flush=True)
        sys.exit(1)

    if not PG_HBA.exists():
        print(f"ERROR: ไม่พบ pg_hba.conf ที่ {PG_HBA}", flush=True)
        sys.exit(1)

    print(f"[1/5] Backup pg_hba.conf...", flush=True)
    shutil.copy2(PG_HBA, PG_HBA_BACKUP)
    print(f"      saved -> {PG_HBA_BACKUP}", flush=True)

    print("[2/5] แก้ pg_hba.conf เป็น trust...", flush=True)
    original = PG_HBA.read_text(encoding="utf-8")
    trust = (
        "# TEMP TRUST - will be restored\n"
        "host    all    all    127.0.0.1/32    trust\n"
        "host    all    all    ::1/128         trust\n"
        "local   all    all                    trust\n"
        "\n"
    )
    PG_HBA.write_text(trust + original, encoding="utf-8")
    print("      done", flush=True)

    print("[3/5] Restart PostgreSQL...", flush=True)
    subprocess.run(["sc", "stop",  PG_SERVICE], capture_output=True)
    time.sleep(5)
    subprocess.run(["sc", "start", PG_SERVICE], capture_output=True)
    time.sleep(5)
    print("      done", flush=True)

    print(f"[4/5] Reset password -> '{NEW_PASSWORD}'...", flush=True)
    psql = PG_BIN / "psql.exe"
    sql  = f"ALTER USER postgres WITH PASSWORD '{NEW_PASSWORD}';"
    r = subprocess.run(
        [str(psql), "-U", "postgres", "-h", "127.0.0.1", "-p", "5432", "-c", sql],
        capture_output=True, text=True, env={**os.environ, "PGPASSWORD": ""}
    )
    if r.returncode == 0:
        print(f"      SUCCESS: password = '{NEW_PASSWORD}'", flush=True)
    else:
        print(f"      WARN: {r.stderr.strip()}", flush=True)

    print("[5/5] คืนค่า pg_hba.conf...", flush=True)
    PG_HBA.write_text(original, encoding="utf-8")
    subprocess.run(["sc", "stop",  PG_SERVICE], capture_output=True)
    time.sleep(5)
    subprocess.run(["sc", "start", PG_SERVICE], capture_output=True)
    time.sleep(5)
    print("      done", flush=True)

    print("=" * 48, flush=True)
    print(f"DONE! รหัสผ่านใหม่: {NEW_PASSWORD}", flush=True)
    print("รัน: python setup_db.py", flush=True)
    print("=" * 48, flush=True)

if __name__ == "__main__":
    main()

