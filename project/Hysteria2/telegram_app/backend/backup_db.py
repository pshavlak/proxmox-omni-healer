#!/usr/bin/env python3
"""
backup_db.py — Ежедневный бэкап app.db в Telegram администраторам.
Переменные окружения (из /etc/telegram-miniapp.env):
  TELEGRAM_BOT_TOKEN   — токен бота
  TELEGRAM_ADMIN_IDS   — через запятую список admin telegram_id
  MINIAPP_DB_PATH      — путь к app.db
"""

import os
import sys
import gzip
import shutil
import time
import json
import urllib.request
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DB_PATH = os.environ.get(
    "MINIAPP_DB_PATH",
    os.path.join(os.path.dirname(__file__), "app.db"),
)


def parse_admin_ids(raw):
    ids = []
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


ADMIN_IDS = parse_admin_ids(os.environ.get("TELEGRAM_ADMIN_IDS", ""))


def send_document(chat_id, file_bytes, filename, caption):
    if not BOT_TOKEN:
        print(f"[Mock] Would send backup to {chat_id}, size={len(file_bytes)} bytes")
        return True

    boundary = "BackupBoundary9a2b3c4d"

    def field(name, value):
        return (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n"
        ).encode("utf-8")

    body = (
        field("chat_id", str(chat_id))
        + field("caption", caption)
        + field("parse_mode", "Markdown")
        + (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"document\"; filename=\"{filename}\"\r\n"
            f"Content-Type: application/gzip\r\n\r\n"
        ).encode("utf-8")
        + file_bytes
        + f"\r\n--{boundary}--\r\n".encode("utf-8")
    )

    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return bool(result.get("ok"))
    except Exception as e:
        print(f"sendDocument error to {chat_id}: {e}", flush=True)
        return False


def create_backup():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found: {DB_PATH}")

    date_str = time.strftime("%Y%m%d_%H%M")
    filename = f"app_db_backup_{date_str}.db.gz"

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        shutil.copy2(DB_PATH, tmp_path)
        with open(tmp_path, "rb") as f_in:
            buf = gzip.compress(f_in.read(), compresslevel=6)
    finally:
        os.unlink(tmp_path)

    return buf, filename


def main():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting DB backup...", flush=True)

    if not ADMIN_IDS:
        print("ERROR: TELEGRAM_ADMIN_IDS not set.", flush=True)
        sys.exit(1)

    try:
        backup_bytes, filename = create_backup()
    except Exception as e:
        print(f"ERROR creating backup: {e}", flush=True)
        sys.exit(1)

    size_kb = round(len(backup_bytes) / 1024, 1)
    caption = (
        f"*Backup: app.db*\n"
        f"{time.strftime('%Y-%m-%d %H:%M')} UTC+3\n"
        f"Размер: {size_kb} KB (gzip)\n"
        f"Ежедневный автоматический бэкап"
    )

    success = 0
    for admin_id in ADMIN_IDS:
        ok = send_document(admin_id, backup_bytes, filename, caption)
        if ok:
            print(f"Backup sent to admin {admin_id} ({size_kb} KB)", flush=True)
            success += 1
        else:
            print(f"Failed to send backup to admin {admin_id}", flush=True)

    if success == 0:
        print("ERROR: Failed to send to any admin.", flush=True)
        sys.exit(1)

    print(f"Backup complete. Sent to {success}/{len(ADMIN_IDS)} admins.", flush=True)


if __name__ == "__main__":
    main()
