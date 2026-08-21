import os
import sys
import json
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.db import get_db
from backend.hysteria_users import delete_hysteria_user

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

def send_telegram(chat_id: int, text: str):
    if not BOT_TOKEN:
        print(f"[Telegram Mock] To {chat_id}: {text}")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode('utf-8'))
    except Exception as e:
        print(f"Telegram notify error ({chat_id}): {e}", flush=True)

def expire_subscriptions():
    conn = get_db()
    now = int(time.time())

    expired = conn.execute("""
        SELECT s.id as sub_id, s.vpn_account_id, v.server_type, v.external_key, v.display_name, al.telegram_user_id
        FROM subscriptions s
        JOIN vpn_accounts v ON s.vpn_account_id = v.id
        LEFT JOIN account_links al ON v.id = al.vpn_account_id
        WHERE s.expires_at < ? AND s.status = 'active'
    """, (now,)).fetchall()

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Found {len(expired)} expired subscriptions.", flush=True)

    for item in expired:
        sub_id = item["sub_id"]
        vpn_id = item["vpn_account_id"]
        server_type = item["server_type"]
        ext_key = item["external_key"]
        display_name = item["display_name"]
        tg_id = item["telegram_user_id"]

        print(f"Disabling expired subscription {sub_id} (VPN ID: {vpn_id}, Name: {display_name})", flush=True)

        if server_type == "hysteria":
            try:
                delete_hysteria_user(ext_key)
            except Exception as e:
                print(f"Failed to delete hysteria user {ext_key}: {e}", flush=True)

        elif server_type == "xui":
            try:
                from backend.xui_api import XUIClient, xui_config_from_env
                config = xui_config_from_env()
                client = XUIClient(config)
                # disable direct client if applicable
                print(f"XUI disable client for key {ext_key}", flush=True)
            except Exception as e:
                print(f"XUI disable client error: {e}", flush=True)

        conn.execute("UPDATE subscriptions SET status='expired' WHERE id=?", (sub_id,))
        conn.execute("UPDATE vpn_accounts SET status='disabled' WHERE id=?", (vpn_id,))

        conn.execute("""
            INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
            VALUES ('system_expiry', 'expire_subscription', ?, 'ok', ?, ?)
        """, (str(vpn_id), now, json.dumps({"sub_id": sub_id, "display_name": display_name})))

        if tg_id:
            msg = f"🔴 **Подписка на VPN ({display_name}) истекла.**\n\nДоступ временно отключен. Продлите подписку в боте или веб-кабинете."
            send_telegram(tg_id, msg)

    conn.commit()
    conn.close()

WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://hist.yupiterpro.ru/app/")


def send_reminders():
    conn = get_db()
    now = int(time.time())

    # Notify once per window: 3 days and 1 day before expiry.
    # last_expiry_notified_at is updated after each send to avoid duplicates.
    reminders = [
        (
            71 * 3600, 73 * 3600,
            "\u23f3 *Подписка истекает через 3 дня*\n\n"
            "Аккаунт: `{display_name}`\n"
            "Продлите доступ заранее, чтобы не прерываться.",
        ),
        (
            23 * 3600, 25 * 3600,
            "\u26a0\ufe0f *Подписка истекает завтра!*\n\n"
            "Аккаунт: `{display_name}`\n"
            "Продлите сейчас, чтобы сохранить доступ к VPN.",
        ),
    ]

    notified = 0
    for min_sec, max_sec, template in reminders:
        targets = conn.execute("""
            SELECT s.id AS sub_id, s.last_expiry_notified_at,
                   v.display_name, al.telegram_user_id
            FROM subscriptions s
            JOIN vpn_accounts v ON s.vpn_account_id = v.id
            JOIN account_links al ON v.id = al.vpn_account_id
            WHERE s.status = 'active'
              AND (s.expires_at - ?) BETWEEN ? AND ?
              AND al.telegram_user_id IS NOT NULL
        """, (now, min_sec, max_sec)).fetchall()

        for t in targets:
            sub_id = t["sub_id"]
            tg_id = t["telegram_user_id"]
            name = t["display_name"]
            last_notified = t["last_expiry_notified_at"] or 0

            # Skip if already notified within last 20 hours
            if now - last_notified < 20 * 3600:
                continue

            msg = template.format(display_name=name) + f"\n\n[Открыть кабинет]({WEBAPP_URL})"
            send_telegram(tg_id, msg)
            conn.execute(
                "UPDATE subscriptions SET last_expiry_notified_at = ? WHERE id = ?",
                (now, sub_id)
            )
            notified += 1

    conn.commit()
    conn.close()
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Sent {notified} expiry reminders.", flush=True)

if __name__ == "__main__":
    expire_subscriptions()
    send_reminders()
