"""
備份與還原工具（SQLite + firmware）

用途：
- backup: 建立 DB 與 firmware 備份壓縮檔
- restore: 從備份壓縮檔還原 DB 與 firmware

範例：
  venv\\Scripts\\python.exe backup_restore.py backup
  venv\\Scripts\\python.exe backup_restore.py restore --file backups\\esp_iot_backup_20260322_103000.zip
"""

import argparse
import os
import shutil
import zipfile
from datetime import datetime


ROOT = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DB = os.path.join(ROOT, "instance", "devices.db")
FIRMWARE_DIR = os.path.join(ROOT, "firmware")
BACKUP_DIR = os.path.join(ROOT, "backups")


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def backup():
    ensure_dir(BACKUP_DIR)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_file = os.path.join(BACKUP_DIR, f"esp_iot_backup_{ts}.zip")

    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(INSTANCE_DB):
            zf.write(INSTANCE_DB, arcname="instance/devices.db")

        if os.path.exists(FIRMWARE_DIR):
            for root, _, files in os.walk(FIRMWARE_DIR):
                for f in files:
                    fp = os.path.join(root, f)
                    rel = os.path.relpath(fp, ROOT)
                    zf.write(fp, arcname=rel)

    print({"status": "ok", "backup_file": out_file})


def restore(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(file_path)

    ensure_dir(os.path.join(ROOT, "instance"))
    ensure_dir(FIRMWARE_DIR)

    with zipfile.ZipFile(file_path, "r") as zf:
        names = zf.namelist()

        if "instance/devices.db" in names:
            temp_db = os.path.join(ROOT, "instance", "devices.db.restore_tmp")
            with zf.open("instance/devices.db") as src, open(temp_db, "wb") as dst:
                shutil.copyfileobj(src, dst)
            os.replace(temp_db, INSTANCE_DB)

        for name in names:
            if not name.startswith("firmware/") or name.endswith("/"):
                continue
            target = os.path.join(ROOT, name)
            target_dir = os.path.dirname(target)
            ensure_dir(target_dir)
            with zf.open(name) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)

    print({"status": "ok", "restored_from": file_path})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup and restore utility")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("backup", help="Create backup zip")
    p_restore = sub.add_parser("restore", help="Restore from backup zip")
    p_restore.add_argument("--file", required=True, help="Backup zip file path")

    args = parser.parse_args()
    if args.cmd == "backup":
        backup()
    elif args.cmd == "restore":
        restore(args.file)
