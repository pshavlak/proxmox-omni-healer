import http.server
import socketserver
import json
import urllib.parse
import os
import sys
import time
import re
import hashlib
import secrets

# Ensure package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db, init_db, get_or_create_sub_token
from backend.hysteria_users import (
    DEFAULT_USERS_FILE,
    HysteriaUsersError,
    create_hysteria_user,
    delete_hysteria_user,
    verify_auth,
)
from backend.latvia_hysteria import (
    LatviaHysteriaError,
    attach_user as attach_latvia_hysteria_user,
    delete_user as delete_latvia_hysteria_user,
)
from backend.telegram_auth import parse_and_verify_init_data
from backend.xui_api import XUIAPIError, XUIConfigError, XUIClient

PORT = int(os.environ.get("PORT", 8085))
PUBLIC_DOMAIN = os.environ.get("PUBLIC_DOMAIN", "hist.yupiterpro.ru")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

def parse_admin_ids(raw):
    ids = set()
    for part in (raw or "").replace(";", ",").split(","):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

ADMIN_IDS = parse_admin_ids(os.environ.get("TELEGRAM_ADMIN_IDS", ""))

def is_admin_user(user):
    try:
        return int(user.get("id")) in ADMIN_IDS
    except Exception:
        return False

class AppRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        message = format % args
        message = self.redact_log_message(message)
        sys.stderr.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), message))

    @staticmethod
    def redact_log_message(message):
        message = re.sub(r"(/sub/)[^ ?\"]+", r"\1[redacted]", message)
        message = re.sub(r"(\?)[^ \"]+", r"\1[query-redacted]", message)
        return message

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def get_telegram_user(self):
        init_data = self.headers.get("X-Telegram-Init-Data", "")
        if not init_data or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
            return None
        try:
            return parse_and_verify_init_data(init_data, BOT_TOKEN)
        except Exception:
            return None

    def is_admin_request(self):
        user = self.get_telegram_user()
        return bool(user and is_admin_user(user))

    def require_admin(self):
        if self.is_admin_request():
            return True
        self.send_json({"error": "admin_forbidden"}, status=403)
        return False

    def send_text(self, text, content_type='text/plain', status=200):
        body = text.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def get_client_ip(self):
        return (
            self.headers.get("X-Real-IP")
            or self.headers.get("X-Forwarded-For", "").split(",", 1)[0].strip()
            or self.client_address[0]
        )

    def send_head_only(self, status=200, content_type='text/plain', content_length=0):
        self.send_response(status)
        self.send_header('Content-Type', f'{content_type}; charset=utf-8')
        self.send_header('Content-Length', str(content_length))
        self.end_headers()

    def do_HEAD(self):
        parsed = urllib.parse.urlparse(self.path)
        path = self.normalize_path(parsed.path)
        if path == "/" or path == "/index.html" or path.startswith("/app/"):
            file_path = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.exists(file_path):
                return self.send_head_only(
                    status=200,
                    content_type="text/html",
                    content_length=os.path.getsize(file_path),
                )
        if path.startswith("/sub/") or path.startswith("/api/"):
            return self.send_head_only(status=405, content_type="text/plain")
        return self.send_head_only(status=404, content_type="application/json")

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = self.normalize_path(parsed.path)

        # Handle /sub/<token>
        if path.startswith("/sub/"):
            token = path[len("/sub/"):].strip()
            return self.handle_subscription(token)

        # Handle /api/user/me
        if path == "/api/user/me":
            return self.handle_user_me()

        if path == "/api/user/devices":
            return self.handle_user_devices()

        if path == "/api/user/routing":
            return self.handle_user_routing()

        # Handle /api/admin/clients
        if path == "/api/admin/clients":
            return self.handle_admin_clients()

        if path == "/api/admin/client":
            query = urllib.parse.parse_qs(parsed.query)
            return self.handle_admin_client_detail(query)

        # Handle /api/admin/receipts
        if path == "/api/admin/receipts":
            return self.handle_admin_receipts()

        if path == "/api/admin/payments":
            return self.handle_admin_payments()

        if path == "/api/admin/payment-settings":
            return self.handle_admin_payment_settings()

        if path == "/api/admin/promocodes":
            return self.handle_admin_promocodes()

        if path == "/api/payment/settings":
            return self.handle_payment_settings()

        # Serve static frontend files
        if path == "/" or path == "/index.html" or path.startswith("/app/"):
            file_path = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    return self.send_text(f.read(), content_type="text/html")

        self.send_json({"error": "Not found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = self.normalize_path(parsed.path)
        length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(length) if length > 0 else b'{}'
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except Exception:
            body = {}

        # Hysteria 2 HTTP Auth Protocol
        if path == "/auth":
            return self.handle_hysteria_auth(body)

        if path == "/api/admin/extend":
            return self.handle_admin_extend(body)

        if path == "/api/admin/hysteria/create":
            return self.handle_admin_create_hysteria(body)

        if path == "/api/admin/xui/create-direct":
            return self.handle_admin_create_xui_direct(body)

        if path == "/api/user/devices/reset":
            return self.handle_user_devices_reset()

        if path == "/api/user/routing":
            return self.handle_user_routing_update(body)

        if path == "/api/promocode/apply":
            return self.handle_apply_promocode(body)

        if path == "/api/payment/manual":
            return self.handle_manual_receipt(body)

        if path == "/api/payment/stars":
            return self.handle_stars_payment_request(body)

        if path == "/api/admin/receipts/action":
            return self.handle_admin_receipt_action(body)

        if path == "/api/admin/payments/action":
            return self.handle_admin_receipt_action(body)

        if path == "/api/admin/payment-settings/save":
            return self.handle_admin_payment_settings_save(body)

        if path == "/api/admin/promocodes/save":
            return self.handle_admin_promocode_save(body)

        if path == "/api/admin/promocodes/delete":
            return self.handle_admin_promocode_delete(body)

        if path == "/api/admin/client/delete":
            return self.handle_admin_client_delete(body)

        if path == "/api/admin/client/set-limit":
            return self.handle_admin_client_set_limit(body)

        if path == "/api/admin/client/grant-trial":
            return self.handle_admin_client_grant_trial(body)

        self.send_json({"error": "Not found"}, status=404)

    @staticmethod
    def normalize_path(path):
        if path.startswith("/app/api/"):
            return path[len("/app"):]
        if path.startswith("/app/sub/"):
            return path[len("/app"):]
        return path

    def handle_hysteria_auth(self, body: dict):
        auth_secret = body.get("auth", "").strip()
        if not auth_secret:
            return self.send_json({"ok": False, "msg": "empty auth"}, status=400)

        conn = get_db()
        row = conn.execute("""
            SELECT va.id, va.traffic_total_bytes, s.status, s.expires_at, s.traffic_limit_bytes
            FROM vpn_accounts va
            JOIN subscriptions s ON va.id = s.vpn_account_id
            WHERE va.external_key = ? AND va.status = 'active'
        """, (auth_secret,)).fetchone()
        conn.close()

        now = int(time.time())
        if row and row["status"] == "active" and row["expires_at"] > now:
            # Traffic limit check: 0 means unlimited
            limit = int(row["traffic_limit_bytes"] or 0)
            used = int(row["traffic_total_bytes"] or 0)
            if limit > 0 and used >= limit:
                return self.send_json({"ok": False, "msg": "traffic limit exceeded"})
            self.record_connection_event(row["id"], "hysteria_auth", "auth_success")
            return self.send_json({"ok": True, "id": str(row["id"])})

        return self.send_json({"ok": False, "msg": "subscription expired or invalid"})

    def handle_apply_promocode(self, body: dict):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "Откройте кабинет внутри Telegram"}, status=403)

        code = body.get("code", "").strip().upper()
        if not code:
            return self.send_json({"error": "Введите промокод"}, status=400)

        conn = get_db()
        promo = conn.execute("SELECT * FROM promocodes WHERE code = ?", (code,)).fetchone()
        if not promo:
            conn.close()
            return self.send_json({"error": "Промокод не найден"}, status=404)

        if promo["activations_count"] >= promo["max_activations"]:
            conn.close()
            return self.send_json({"error": "Лимит активаций промокода исчерпан"}, status=400)

        now = int(time.time())
        if promo["expires_at"] and promo["expires_at"] < now:
            conn.close()
            return self.send_json({"error": "Срок действия промокода истёк"}, status=400)

        acc = self.get_user_account(conn, telegram_user)
        if not acc:
            conn.close()
            return self.issue_promocode_key(telegram_user, promo, code)

        current_exp = acc["expires_at"] if acc["expires_at"] and acc["expires_at"] > now else now
        new_exp = current_exp + (promo["bonus_days"] * 86400)

        with conn:
            conn.execute("UPDATE subscriptions SET expires_at = ?, status = 'active' WHERE vpn_account_id = ?", (new_exp, acc["id"]))
            conn.execute("UPDATE promocodes SET activations_count = activations_count + 1 WHERE code = ?", (code,))
        conn.close()

        return self.send_json({
            "ok": True,
            "message": f"Промокод активирован! Добавлено +{promo['bonus_days']} дней",
            "new_expires_at": time.strftime("%Y-%m-%d", time.localtime(new_exp))
        })

    def issue_promocode_key(self, telegram_user, promo, code):
        days = int(promo["bonus_days"] or 0)
        if days < 1 or days > 3650:
            return self.send_json({"error": "Промокод настроен без срока ключа"}, status=400)

        username = self.promo_username(telegram_user, code)
        created = None
        account_id = None
        xui = None
        direct_created = []
        try:
            created = create_hysteria_user(username)
            auth_check = verify_auth(created["auth_secret"], expected_id=username)
            if not auth_check["ok"]:
                delete_hysteria_user(username)
                return self.send_json({"error": "auth_verification_failed"}, status=500)

            account_id, token, expires_at = self.create_local_hysteria_account(
                username,
                created["auth_secret"],
                days,
            )
            self.mark_promocode_account(account_id, code, expires_at)
            xui = XUIClient()
            tcp = xui.create_direct_client(username, expiry_time_seconds=expires_at, transport="tcp")
            direct_created.append("tcp")
            self.attach_direct_profile(
                account_id,
                tcp["uri"],
                f"x-ui managed inbound #{tcp['inbound_id']}",
                transport="tcp",
            )
            xhttp = xui.create_direct_client(username, expiry_time_seconds=expires_at, transport="xhttp")
            direct_created.append("xhttp")
            self.attach_direct_profile(
                account_id,
                xhttp["uri"],
                f"x-ui managed inbound #{xhttp['inbound_id']}",
                transport="xhttp",
            )
            latvia_hysteria = attach_latvia_hysteria_user(username, created["auth_secret"])
            direct_created.append("hysteria")
            self.attach_direct_profile(
                account_id,
                latvia_hysteria["uri"],
                "Latvia Hysteria direct inbound",
                transport="hysteria",
            )
        except (HysteriaUsersError, XUIConfigError, XUIAPIError, LatviaHysteriaError) as e:
            self.rollback_promocode_key_issue(username, created, account_id, xui, direct_created)
            return self.send_json({"error": str(e)}, status=502)
        except Exception:
            self.rollback_promocode_key_issue(username, created, account_id, xui, direct_created)
            return self.send_json({"error": "promocode_key_create_failed"}, status=500)

        now = int(time.time())
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT INTO telegram_users (telegram_id, username, first_name, role, created_at, last_seen_at)
                VALUES (?, ?, ?, 'user', ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    last_seen_at = excluded.last_seen_at
            """, (
                int(telegram_user["id"]),
                telegram_user.get("username", ""),
                telegram_user.get("first_name", "User"),
                now,
                now,
            ))
            conn.execute("""
                INSERT OR REPLACE INTO account_links (telegram_user_id, vpn_account_id, linked_at, link_method)
                VALUES (?, ?, ?, 'promocode')
            """, (int(telegram_user["id"]), account_id, now))
            conn.execute("UPDATE promocodes SET activations_count = activations_count + 1 WHERE code = ?", (code,))
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES (?, 'promocode_issue_key', ?, 'ok', ?, ?)""",
                (
                    f"telegram:{telegram_user.get('id')}",
                    str(account_id),
                    now,
                    json.dumps({"code": code, "days": days}, ensure_ascii=False),
                )
            )
        conn.close()

        return self.send_json({
            "ok": True,
            "issued_key": True,
            "message": f"Промокод активирован! Ключ выдан на {days} дн.",
            "account_id": account_id,
            "name": username,
            "expires_at": self.format_expiry(expires_at),
            "sub_link": f"https://{PUBLIC_DOMAIN}/sub/{token}",
        })

    def handle_manual_receipt(self, body: dict):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)

        amount = body.get("amount", 300)
        note = (body.get("note") or "Перевод по СБП").strip()[:500]
        now = int(time.time())

        conn = get_db()
        settings = conn.execute("SELECT manual_enabled FROM payment_settings WHERE id = 1").fetchone()
        if not settings or not settings["manual_enabled"]:
            conn.close()
            return self.send_json({"error": "manual_payment_disabled"}, status=409)
        with conn:
            conn.execute(
                """INSERT INTO manual_receipts
                   (telegram_user_id, amount, currency, receipt_note, status, created_at)
                   VALUES (?, ?, 'RUB', ?, 'pending', ?)""",
                (int(telegram_user["id"]), amount, note, now)
            )
        conn.close()
        return self.send_json({"ok": True, "message": "Чек отправлен на проверку администратору"})

    def handle_stars_payment_request(self, body: dict):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)

        amount = body.get("amount", 150)
        note = (body.get("note") or "Telegram Stars invoice request").strip()[:500]
        now = int(time.time())

        conn = get_db()
        with conn:
            conn.execute(
                """INSERT INTO manual_receipts
                   (telegram_user_id, amount, currency, receipt_note, status, created_at)
                   VALUES (?, ?, 'STARS', ?, 'pending', ?)""",
                (int(telegram_user["id"]), amount, note, now)
            )
        conn.close()
        return self.send_json({"ok": True, "message": "Заявка на счёт Telegram Stars отправлена админу"})

    @staticmethod
    def payment_settings_payload(row, admin=False):
        row = row or {}
        payload = {
            "manual_enabled": bool(row["manual_enabled"]) if row else False,
            "card_number": row["card_number"] if row else "",
            "bank_name": row["bank_name"] if row else "",
            "recipient_name": row["recipient_name"] if row else "",
            "sbp_phone": row["sbp_phone"] if row else "",
            "payment_comment": row["payment_comment"] if row else "",
            "user_instructions": row["user_instructions"] if row else "",
        }
        if admin:
            payload["updated_at"] = row["updated_at"] if row else None
        return payload

    def handle_payment_settings(self):
        conn = get_db()
        row = conn.execute("SELECT * FROM payment_settings WHERE id = 1").fetchone()
        conn.close()
        return self.send_json({"settings": self.payment_settings_payload(row)})

    def handle_admin_payment_settings(self):
        if not self.require_admin():
            return
        conn = get_db()
        row = conn.execute("SELECT * FROM payment_settings WHERE id = 1").fetchone()
        conn.close()
        return self.send_json({"settings": self.payment_settings_payload(row, admin=True)})

    def handle_admin_payment_settings_save(self, body):
        if not self.require_admin():
            return
        def clean(name, limit=300):
            return (body.get(name) or "").strip()[:limit]

        manual_enabled = 1 if body.get("manual_enabled") else 0
        now = int(time.time())
        values = {
            "card_number": clean("card_number", 80),
            "bank_name": clean("bank_name", 120),
            "recipient_name": clean("recipient_name", 160),
            "sbp_phone": clean("sbp_phone", 80),
            "payment_comment": clean("payment_comment", 200),
            "user_instructions": clean("user_instructions", 1000),
        }

        conn = get_db()
        with conn:
            conn.execute("""
                INSERT INTO payment_settings
                  (id, manual_enabled, card_number, bank_name, recipient_name, sbp_phone,
                   payment_comment, user_instructions, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  manual_enabled = excluded.manual_enabled,
                  card_number = excluded.card_number,
                  bank_name = excluded.bank_name,
                  recipient_name = excluded.recipient_name,
                  sbp_phone = excluded.sbp_phone,
                  payment_comment = excluded.payment_comment,
                  user_instructions = excluded.user_instructions,
                  updated_at = excluded.updated_at
            """, (
                manual_enabled,
                values["card_number"],
                values["bank_name"],
                values["recipient_name"],
                values["sbp_phone"],
                values["payment_comment"],
                values["user_instructions"],
                now,
            ))
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'payment_settings_save', 'manual', 'ok', ?, ?)""",
                (now, json.dumps({"manual_enabled": manual_enabled}, ensure_ascii=False)),
            )
        conn.close()
        return self.send_json({"ok": True, "settings": {"manual_enabled": bool(manual_enabled), **values}})

    def handle_admin_receipts(self):
        if not self.require_admin():
            return
        conn = get_db()
        rows = conn.execute("SELECT * FROM manual_receipts WHERE status = 'pending' ORDER BY created_at DESC").fetchall()
        conn.close()
        receipts = [dict(r) for r in rows]
        return self.send_json({"receipts": receipts})

    @staticmethod
    def format_timestamp(ts):
        if not ts:
            return ""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ts)))

    @staticmethod
    def normalize_promocode(code):
        code = (code or "").strip().upper()
        if not re.fullmatch(r"[A-Z0-9_-]{3,32}", code):
            raise ValueError("code_must_be_3_32_latin_digits_dash_underscore")
        return code

    @staticmethod
    def parse_promocode_expiry(value):
        value = (value or "").strip()
        if not value:
            return None
        try:
            return int(time.mktime(time.strptime(value, "%Y-%m-%d"))) + 86399
        except Exception:
            raise ValueError("invalid_expires_at")

    @staticmethod
    def promocode_payload(row):
        expires_at = row["expires_at"]
        now = int(time.time())
        return {
            "code": row["code"],
            "bonus_days": row["bonus_days"],
            "discount_percent": row["discount_percent"],
            "max_activations": row["max_activations"],
            "activations_count": row["activations_count"],
            "expires_at": time.strftime("%Y-%m-%d", time.localtime(expires_at)) if expires_at else "",
            "issue_key_on_activation": bool(row["issue_key_on_activation"]),
            "is_expired": bool(expires_at and expires_at < now),
            "is_exhausted": row["activations_count"] >= row["max_activations"],
        }

    @staticmethod
    def promo_username(telegram_user, code):
        tg_id = int(telegram_user.get("id") or 0)
        safe_code = re.sub(r"[^A-Z0-9_-]+", "_", (code or "PROMO").upper()).strip("_")[:16] or "PROMO"
        suffix = secrets.token_hex(3)
        return f"tg{tg_id}_{safe_code}_{suffix}"[:64]

    def handle_admin_payments(self):
        if not self.require_admin():
            return
        conn = get_db()
        receipt_rows = conn.execute("""
            SELECT * FROM manual_receipts
            ORDER BY created_at DESC
            LIMIT 100
        """).fetchall()
        transaction_rows = conn.execute("""
            SELECT * FROM transactions
            ORDER BY created_at DESC
            LIMIT 100
        """).fetchall()
        pending_count = conn.execute(
            "SELECT count(*) FROM manual_receipts WHERE status = 'pending'"
        ).fetchone()[0]
        approved_sum = conn.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM manual_receipts
            WHERE status = 'approved' AND COALESCE(currency, 'RUB') = 'RUB'
        """).fetchone()[0]
        conn.close()

        receipts = []
        for row in receipt_rows:
            item = dict(row)
            item["currency"] = item.get("currency") or "RUB"
            item["created_at_text"] = self.format_timestamp(row["created_at"])
            item["processed_at_text"] = self.format_timestamp(row["processed_at"])
            receipts.append(item)

        transactions = []
        for row in transaction_rows:
            item = dict(row)
            item["created_at_text"] = self.format_timestamp(row["created_at"])
            transactions.append(item)

        return self.send_json({
            "summary": {
                "pending_count": pending_count,
                "approved_sum": approved_sum,
                "receipts_count": len(receipts),
                "transactions_count": len(transactions),
            },
            "receipts": receipts,
            "transactions": transactions,
        })

    def handle_admin_promocodes(self):
        if not self.require_admin():
            return
        conn = get_db()
        rows = conn.execute("""
            SELECT * FROM promocodes
            ORDER BY expires_at IS NULL DESC, expires_at DESC, code ASC
        """).fetchall()
        conn.close()
        return self.send_json({"promocodes": [self.promocode_payload(row) for row in rows]})

    def handle_admin_promocode_save(self, body):
        if not self.require_admin():
            return
        try:
            code = self.normalize_promocode(body.get("code"))
            bonus_days = int(body.get("bonus_days", 0) or 0)
            discount_percent = int(body.get("discount_percent", 0) or 0)
            max_activations = int(body.get("max_activations", 1) or 1)
            issue_key = 1 if body.get("issue_key_on_activation") else 0
            expires_at = self.parse_promocode_expiry(body.get("expires_at"))
        except ValueError as e:
            return self.send_json({"error": str(e)}, status=400)
        except Exception:
            return self.send_json({"error": "invalid_promocode_payload"}, status=400)

        if bonus_days < 0 or bonus_days > 3650:
            return self.send_json({"error": "invalid_bonus_days"}, status=400)
        if discount_percent < 0 or discount_percent > 100:
            return self.send_json({"error": "invalid_discount_percent"}, status=400)
        if max_activations < 1 or max_activations > 1_000_000:
            return self.send_json({"error": "invalid_max_activations"}, status=400)

        now = int(time.time())
        conn = get_db()
        with conn:
            existing = conn.execute("SELECT activations_count FROM promocodes WHERE code = ?", (code,)).fetchone()
            activations_count = existing["activations_count"] if existing else 0
            if activations_count > max_activations:
                max_activations = activations_count
            conn.execute("""
                INSERT INTO promocodes
                    (code, bonus_days, discount_percent, max_activations, activations_count, expires_at, issue_key_on_activation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET
                    bonus_days = excluded.bonus_days,
                    discount_percent = excluded.discount_percent,
                    max_activations = excluded.max_activations,
                    expires_at = excluded.expires_at,
                    issue_key_on_activation = excluded.issue_key_on_activation
            """, (code, bonus_days, discount_percent, max_activations, activations_count, expires_at, issue_key))
            conn.execute(
                """INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'promocode_save', ?, 'ok', ?, ?)""",
                (code, now, json.dumps({
                    "bonus_days": bonus_days,
                    "discount_percent": discount_percent,
                    "max_activations": max_activations,
                    "expires_at": expires_at,
                    "issue_key_on_activation": issue_key,
                }, ensure_ascii=False))
            )
        conn.close()
        return self.send_json({"ok": True, "code": code})

    def handle_admin_promocode_delete(self, body):
        if not self.require_admin():
            return
        try:
            code = self.normalize_promocode(body.get("code"))
        except ValueError as e:
            return self.send_json({"error": str(e)}, status=400)

        now = int(time.time())
        conn = get_db()
        with conn:
            cur = conn.execute("DELETE FROM promocodes WHERE code = ?", (code,))
            conn.execute(
                """INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'promocode_delete', ?, ?, ?, '{}')""",
                (code, "ok" if cur.rowcount else "not_found", now)
            )
        conn.close()
        return self.send_json({"ok": True, "deleted": cur.rowcount > 0})

    def handle_admin_receipt_action(self, body: dict):
        if not self.require_admin():
            return
        receipt_id = body.get("id")
        action = body.get("action") # 'approve' or 'reject'
        now = int(time.time())

        conn = get_db()
        receipt = conn.execute("SELECT * FROM manual_receipts WHERE id = ?", (receipt_id,)).fetchone()
        if not receipt:
            conn.close()
            return self.send_json({"error": "Чек не найден"}, status=404)

        if action == 'approve':
            linked = conn.execute("""
                SELECT vpn_account_id
                FROM account_links
                WHERE telegram_user_id = ?
                ORDER BY linked_at DESC
                LIMIT 1
            """, (receipt["telegram_user_id"],)).fetchone()
            if not linked:
                conn.close()
                return self.send_json({"error": "vpn_account_not_linked"}, status=409)

        new_status = 'approved' if action == 'approve' else 'rejected'
        with conn:
            conn.execute("UPDATE manual_receipts SET status = ?, processed_at = ? WHERE id = ?", (new_status, now, receipt_id))
            if action == 'approve':
                sub = conn.execute("SELECT expires_at FROM subscriptions WHERE vpn_account_id = ?", (linked["vpn_account_id"],)).fetchone()
                current_exp = sub["expires_at"] if sub and sub["expires_at"] > now else now
                conn.execute(
                    "UPDATE subscriptions SET expires_at = ?, status = 'active' WHERE vpn_account_id = ?",
                    (current_exp + 2592000, linked["vpn_account_id"])
                )
                conn.execute(
                    """INSERT INTO transactions (telegram_user_id, type, amount, description, created_at)
                       VALUES (?, 'manual_payment', ?, ?, ?)""",
                    (
                        receipt["telegram_user_id"],
                        receipt["amount"],
                        f"Одобрена заявка #{receipt_id} ({receipt['currency'] or 'RUB'})",
                        now,
                    )
                )

        conn.close()
        return self.send_json({"ok": True, "status": new_status})

    def handle_subscription(self, token: str):
        conn = get_db()
        row = conn.execute("""
            SELECT st.vpn_account_id, va.server_type, va.external_key, va.display_name, va.routing_mode,
                   va.direct_config_uri, va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
                   va.direct_hysteria_config_uri,
                   s.status, s.expires_at
            FROM subscription_tokens st
            JOIN vpn_accounts va ON st.vpn_account_id = va.id
            JOIN subscriptions s ON va.id = s.vpn_account_id
            WHERE st.token = ? AND st.revoked_at IS NULL
        """, (token,)).fetchone()
        conn.close()

        if not row:
            return self.send_text("Invalid or expired subscription link", status=404)

        now = int(time.time())
        if row["status"] != "active" or row["expires_at"] < now:
            return self.send_text("Subscription expired or inactive", status=403)

        self.record_connection_event(row["vpn_account_id"], "subscription", "config_fetch")
        self.record_subscription_device(row["vpn_account_id"])

        # Build Hysteria2 URI
        auth_secret = row["external_key"]
        cascade_label = urllib.parse.quote("Каскад Москва Латвия")
        cascade_uri = f"hysteria2://{auth_secret}@{PUBLIC_DOMAIN}:8443/?insecure=0#{cascade_label}"
        uris = []
        if row["server_type"] == "hysteria":
            uris.append(cascade_uri)
        labeled_direct = [
            self.with_uri_label(row["direct_tcp_config_uri"], "Латвия TCP") if row["direct_tcp_config_uri"] else None,
            self.with_uri_label(row["direct_xhttp_config_uri"], "Латвия XHTTP") if row["direct_xhttp_config_uri"] else None,
            self.with_uri_label(row["direct_hysteria_config_uri"], "Латвия Hysteria") if row["direct_hysteria_config_uri"] else None,
            self.with_uri_label(row["direct_config_uri"], "Латвия TCP") if row["direct_config_uri"] else None,
        ]
        for uri in labeled_direct:
            if uri and uri not in uris:
                uris.append(uri)
        if row["server_type"] == "xui" and not uris and row["direct_config_uri"]:
            uris.append(row["direct_config_uri"])

        # Return subscription config
        return self.send_text("\n".join(uris), content_type="text/plain; charset=utf-8")

    def get_user_account(self, conn, telegram_user=None):
        if telegram_user and telegram_user.get("id"):
            linked = conn.execute("""
                SELECT va.id, va.server_type, va.display_name, va.routing_mode, va.direct_config_uri,
                       va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
                       va.direct_hysteria_config_uri,
                       s.status, s.expires_at, st.token,
                       va.traffic_up_bytes, va.traffic_down_bytes, va.traffic_total_bytes, va.traffic_source,
                       va.online_devices,
                       al.telegram_user_id, tu.username AS tg_username, tu.first_name AS tg_first_name
                FROM account_links al
                JOIN vpn_accounts va ON al.vpn_account_id = va.id
                JOIN subscriptions s ON va.id = s.vpn_account_id
                JOIN subscription_tokens st ON va.id = st.vpn_account_id
                LEFT JOIN telegram_users tu ON tu.telegram_id = al.telegram_user_id
                WHERE al.telegram_user_id = ?
                  AND va.status != 'deleted'
                  AND st.revoked_at IS NULL
                ORDER BY al.linked_at DESC
                LIMIT 1
            """, (int(telegram_user["id"]),)).fetchone()
            if linked:
                return linked

        return None

    def handle_user_me(self):
        telegram_user = self.get_telegram_user()
        is_admin = bool(telegram_user and is_admin_user(telegram_user))
        conn = get_db()
        acc = self.get_user_account(conn, telegram_user)
        conn.close()

        if not acc:
            return self.send_json({
                "has_subscription": False,
                "username": telegram_user.get("first_name", "Пользователь") if telegram_user else "Пользователь",
                "status": "inactive",
                "days_left": 0,
                "expires_at": "нет подписки",
                "sub_link": None,
                "used_gb": None,
                "total_gb": None,
                "devices_count": None,
                "metrics_note": "Нет активной подписки",
                "routing_mode": "cascade",
                "routing_label": "Каскад",
                "direct_available": False,
                "direct_tcp_available": False,
                "direct_xhttp_available": False,
                "direct_hysteria_available": False,
                "is_admin": is_admin
            })

        now = int(time.time())
        days_left = max(0, (acc["expires_at"] - now) // 86400)
        sub_link = f"https://{PUBLIC_DOMAIN}/sub/{acc['token']}"
        up = int(acc["traffic_up_bytes"] or 0)
        down = int(acc["traffic_down_bytes"] or 0)
        total = int(acc["traffic_total_bytes"] or 0)
        has_traffic = bool(acc["traffic_source"])
        used_gb = round((up + down) / (1024 ** 3), 2) if has_traffic else None
        total_gb = round(total / (1024 ** 3), 2) if total else None

        return self.send_json({
            "has_subscription": True,
            "username": self.linked_display_name(acc),
            "technical_name": acc["display_name"],
            "status": acc["status"] if days_left > 0 else "expired",
            "days_left": days_left,
            "expires_at": time.strftime("%Y-%m-%d", time.localtime(acc["expires_at"])),
            "sub_link": sub_link,
            "used_gb": used_gb,
            "total_gb": total_gb,
            "devices_count": acc["online_devices"],
            "metrics_note": self.metrics_note(acc["server_type"], acc["traffic_source"]),
            "routing_mode": acc["routing_mode"] or "cascade",
            "routing_label": self.routing_label(acc["routing_mode"] or "cascade"),
            "direct_available": bool(acc["direct_config_uri"] or acc["direct_tcp_config_uri"] or acc["direct_xhttp_config_uri"] or acc["direct_hysteria_config_uri"]),
            "direct_tcp_available": bool(acc["direct_tcp_config_uri"] or acc["direct_config_uri"]),
            "direct_xhttp_available": bool(acc["direct_xhttp_config_uri"]),
            "direct_hysteria_available": bool(acc["direct_hysteria_config_uri"]),
            "is_admin": is_admin
        })

    @staticmethod
    def routing_label(mode):
        return {
            "cascade": "Каскад",
            "direct": "Прямой VPN",
        }.get(mode or "cascade", "Каскад")

    @staticmethod
    def normalize_routing_mode(mode):
        mode = (mode or "").strip().lower()
        if mode not in ("cascade", "direct"):
            raise ValueError("unsupported_routing_mode")
        return mode

    @staticmethod
    def with_uri_label(uri, label):
        base = (uri or "").split("#", 1)[0]
        return f"{base}#{urllib.parse.quote(label)}"

    def handle_user_routing(self):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)
        conn = get_db()
        acc = self.get_user_account(conn, telegram_user)
        conn.close()
        if not acc:
            return self.send_json({
                "routing_mode": "cascade",
                "routing_label": "Каскад",
                "direct_available": False,
                "direct_tcp_available": False,
                "direct_xhttp_available": False,
                "direct_hysteria_available": False,
            })
        mode = acc["routing_mode"] or "cascade"
        return self.send_json({
            "routing_mode": mode,
            "routing_label": self.routing_label(mode),
            "direct_available": bool(acc["direct_config_uri"] or acc["direct_tcp_config_uri"] or acc["direct_xhttp_config_uri"] or acc["direct_hysteria_config_uri"]),
            "direct_tcp_available": bool(acc["direct_tcp_config_uri"] or acc["direct_config_uri"]),
            "direct_xhttp_available": bool(acc["direct_xhttp_config_uri"]),
            "direct_hysteria_available": bool(acc["direct_hysteria_config_uri"]),
        })

    def handle_user_routing_update(self, body):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)
        try:
            mode = self.normalize_routing_mode(body.get("mode"))
        except ValueError as e:
            return self.send_json({"error": str(e)}, status=400)

        conn = get_db()
        acc = self.get_user_account(conn, telegram_user)
        if not acc:
            conn.close()
            return self.send_json({"error": "account_not_found"}, status=404)
        if mode == "direct" and not (acc["direct_config_uri"] or acc["direct_tcp_config_uri"] or acc["direct_xhttp_config_uri"] or acc["direct_hysteria_config_uri"]):
            conn.close()
            return self.send_json({"error": "direct_profile_not_available"}, status=409)
        with conn:
            conn.execute("UPDATE vpn_accounts SET routing_mode = ? WHERE id = ?", (mode, acc["id"]))
            conn.execute(
                """INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
                   VALUES (?, 'routing_update', ?, 'ok', ?, ?)""",
                (
                    f"telegram:{telegram_user.get('id')}",
                    str(acc["id"]),
                    int(time.time()),
                    json.dumps({"mode": mode}, ensure_ascii=False),
                )
            )
        conn.close()
        return self.send_json({
            "ok": True,
            "routing_mode": mode,
            "routing_label": self.routing_label(mode),
            "direct_available": True,
        })

    @staticmethod
    def clean_header(value, limit=160):
        value = (value or "").strip()
        value = re.sub(r"[\r\n\t]+", " ", value)
        return value[:limit]

    def get_header_any(self, names):
        for name in names:
            value = self.headers.get(name)
            if value:
                return self.clean_header(value)
        return ""

    @staticmethod
    def parse_client_from_user_agent(user_agent):
        user_agent = user_agent or ""
        first = user_agent.split(" ", 1)[0].strip()
        if "/" in first:
            name, version = first.split("/", 1)
            return name[:60], version[:40]
        if first:
            return first[:60], ""
        return "", ""

    @staticmethod
    def infer_platform(user_agent):
        ua = (user_agent or "").lower()
        if "iphone" in ua or "ios" in ua:
            return "iOS"
        if "mac" in ua or "darwin" in ua:
            return "macOS"
        if "android" in ua:
            return "Android"
        if "windows" in ua or "win64" in ua:
            return "Windows"
        if "linux" in ua:
            return "Linux"
        return ""

    @staticmethod
    def infer_model(user_agent, platform):
        ua = user_agent or ""
        model_match = re.search(r"\(([^;)]+(?:iPhone|iPad|MacBook|Mac|Android|Windows)[^;)]*)", ua, re.I)
        if model_match:
            return model_match.group(1)[:100]
        if platform:
            return f"{platform} client"
        return "Unknown client"

    @staticmethod
    def device_display_name(device):
        model = device["device_model"] or "Unknown client"
        platform = device["platform"] or ""
        if platform and platform.lower() not in model.lower():
            return f"{model} ({platform})"
        return model

    def build_subscription_device(self):
        user_agent = self.clean_header(self.headers.get("User-Agent", ""), 300)
        hwid = self.get_header_any([
            "X-Hwid",
            "X-HWID",
            "X-Device-Id",
            "X-Device-ID",
            "X-Device-UUID",
            "X-Device",
        ])
        device_model = self.get_header_any([
            "X-Device-Model",
            "X-Device-Name",
            "X-Model",
            "X-Hwid-Model",
        ])
        platform = self.get_header_any([
            "X-Platform",
            "X-Device-Platform",
            "X-OS",
            "X-Client-Platform",
        ])
        client_version = self.get_header_any([
            "X-Client-Version",
            "X-App-Version",
            "X-Version",
        ])
        client_name, ua_version = self.parse_client_from_user_agent(user_agent)
        if not client_version:
            client_version = ua_version
        if not platform:
            platform = self.infer_platform(user_agent)
        if not device_model:
            device_model = self.infer_model(user_agent, platform)

        if hwid:
            fingerprint_source = f"hwid:{hwid}"
        else:
            fingerprint_source = f"fallback:{user_agent}:{self.get_client_ip()}"
        device_key = hashlib.sha256(fingerprint_source.encode("utf-8")).hexdigest()[:32]

        return {
            "device_key": device_key,
            "hwid": hwid or None,
            "device_model": device_model or "Unknown client",
            "platform": platform or None,
            "client_name": client_name or None,
            "client_version": client_version or None,
            "user_agent": user_agent or None,
            "ip": self.get_client_ip(),
        }

    def record_subscription_device(self, vpn_account_id):
        device = self.build_subscription_device()
        now = int(time.time())
        conn = get_db()
        with conn:
            conn.execute("""
                INSERT INTO subscription_devices (
                    vpn_account_id, device_key, hwid, device_model, platform, client_name,
                    client_version, user_agent, ip, first_seen_at, last_seen_at, hits, is_reset, source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 0, 'subscription_headers')
                ON CONFLICT(vpn_account_id, device_key) DO UPDATE SET
                    hwid = excluded.hwid,
                    device_model = excluded.device_model,
                    platform = excluded.platform,
                    client_name = excluded.client_name,
                    client_version = excluded.client_version,
                    user_agent = excluded.user_agent,
                    ip = excluded.ip,
                    last_seen_at = excluded.last_seen_at,
                    hits = subscription_devices.hits + 1,
                    is_reset = 0
            """, (
                vpn_account_id,
                device["device_key"],
                device["hwid"],
                device["device_model"],
                device["platform"],
                device["client_name"],
                device["client_version"],
                device["user_agent"],
                device["ip"],
                now,
                now,
            ))
        conn.close()

    def list_account_devices(self, conn, account_id):
        rows = conn.execute("""
            SELECT *
            FROM subscription_devices
            WHERE vpn_account_id = ? AND is_reset = 0
            ORDER BY last_seen_at DESC
        """, (account_id,)).fetchall()
        return [
            {
                "id": row["id"],
                "name": self.device_display_name(row),
                "model": row["device_model"],
                "platform": row["platform"],
                "client": row["client_name"],
                "version": row["client_version"],
                "ip": row["ip"],
                "first_seen": time.strftime("%Y-%m-%d %H:%M", time.localtime(row["first_seen_at"])),
                "last_seen": time.strftime("%Y-%m-%d %H:%M", time.localtime(row["last_seen_at"])),
                "hits": row["hits"],
                "has_hwid": bool(row["hwid"]),
            }
            for row in rows
        ]

    def handle_user_devices(self):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)
        conn = get_db()
        acc = self.get_user_account(conn, telegram_user)
        if not acc:
            conn.close()
            return self.send_json({"devices": [], "count": 0})
        devices = self.list_account_devices(conn, acc["id"])
        conn.close()
        return self.send_json({"devices": devices, "count": len(devices)})

    def handle_user_devices_reset(self):
        telegram_user = self.get_telegram_user()
        if not telegram_user:
            return self.send_json({"error": "telegram_auth_required"}, status=403)
        conn = get_db()
        acc = self.get_user_account(conn, telegram_user)
        if not acc:
            conn.close()
            return self.send_json({"ok": True, "reset_count": 0})
        now = int(time.time())
        with conn:
            cur = conn.execute(
                """UPDATE subscription_devices
                   SET is_reset = 1, last_seen_at = ?
                   WHERE vpn_account_id = ? AND is_reset = 0""",
                (now, acc["id"])
            )
        conn.close()
        return self.send_json({"ok": True, "reset_count": cur.rowcount})

    def handle_admin_clients(self):
        if not self.require_admin():
            return
        conn = get_db()
        rows = conn.execute("""
            SELECT va.id, va.server_type, va.display_name, va.external_key, s.status, s.expires_at, st.token,
                   va.traffic_up_bytes, va.traffic_down_bytes, va.traffic_total_bytes, va.traffic_updated_at,
                   va.traffic_source, va.online_devices, va.account_origin,
                   va.direct_config_uri, va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
                   va.direct_hysteria_config_uri,
                   al.telegram_user_id, tu.username AS tg_username, tu.first_name AS tg_first_name
            FROM vpn_accounts va
            LEFT JOIN subscriptions s ON va.id = s.vpn_account_id
            LEFT JOIN subscription_tokens st ON va.id = st.vpn_account_id
            LEFT JOIN account_links al ON al.vpn_account_id = va.id
            LEFT JOIN telegram_users tu ON tu.telegram_id = al.telegram_user_id
            WHERE va.status != 'deleted'
            GROUP BY va.id
        """).fetchall()

        now = int(time.time())
        clients = []
        for r in rows:
            expires_at = r["expires_at"] or now
            days_left = max(0, (expires_at - now) // 86400)
            up = int(r["traffic_up_bytes"] or 0)
            down = int(r["traffic_down_bytes"] or 0)
            total = int(r["traffic_total_bytes"] or 0)
            last_ips = conn.execute(
                """SELECT ip, max(created_at) AS last_seen
                   FROM connection_events
                   WHERE vpn_account_id = ? AND ip IS NOT NULL AND ip != ''
                   GROUP BY ip
                   ORDER BY last_seen DESC
                   LIMIT 5""",
                (r["id"],)
            ).fetchall()
            clients.append({
                "id": r["id"],
                "name": self.linked_display_name(r),
                "technical_name": r["display_name"],
                "telegram_user_id": r["telegram_user_id"],
                "type": r["server_type"],
                "origin": r["account_origin"] or "legacy",
                "is_new_logic": r["account_origin"] == "miniapp",
                "status": r["status"] if days_left > 0 else "expired",
                "days_left": days_left,
                "expires_at": time.strftime("%Y-%m-%d", time.localtime(expires_at)),
                "token": r["token"],
                "used_gb": round((up + down) / (1024 ** 3), 2) if r["traffic_source"] else None,
                "up_gb": round(up / (1024 ** 3), 2) if r["traffic_source"] else None,
                "down_gb": round(down / (1024 ** 3), 2) if r["traffic_source"] else None,
                "total_gb": round(total / (1024 ** 3), 2) if total else None,
                "traffic_source": r["traffic_source"] or None,
                "active_devices": r["online_devices"],
                "last_ips": [dict(ip) for ip in last_ips],
                "metrics_note": self.metrics_note(r["server_type"], r["traffic_source"])
            })
        conn.close()

        return self.send_json({"clients": clients})

    @staticmethod
    def bytes_to_gb(value):
        return round(int(value or 0) / (1024 ** 3), 2)

    @staticmethod
    def metrics_note(server_type, traffic_source):
        if traffic_source == "x-ui/client_traffics":
            return "Реальный x-ui трафик"
        if traffic_source == "hysteria/trafficStats":
            return "Реальный Hysteria trafficStats"
        if traffic_source == "hysteria/trafficStats/pending":
            return "Hysteria trafficStats подключён, ждём первый трафик"
        if server_type == "hysteria":
            return "Hysteria traffic accounting не подключён"
        return "Трафик: нет данных"

    @staticmethod
    def parse_date_start(value, default_ts):
        if not value:
            return default_ts
        try:
            return int(time.mktime(time.strptime(value, "%Y-%m-%d")))
        except Exception:
            return default_ts

    @staticmethod
    def format_expiry(expires_at):
        if not expires_at:
            return "нет данных"
        if int(expires_at) >= 4_000_000_000:
            return "бессрочно"
        return time.strftime("%Y-%m-%d", time.localtime(int(expires_at)))

    @staticmethod
    def linked_display_name(row):
        first_name = (row["tg_first_name"] if "tg_first_name" in row.keys() else "") or ""
        username = (row["tg_username"] if "tg_username" in row.keys() else "") or ""
        telegram_id = row["telegram_user_id"] if "telegram_user_id" in row.keys() else None
        first_name = first_name.strip()
        username = username.strip().lstrip("@")
        if first_name and username:
            return f"{first_name} (@{username})"
        if username:
            return f"@{username}"
        if first_name:
            return first_name
        if telegram_id:
            return f"Telegram ID {telegram_id}"
        return row["display_name"]

    def build_client_payload(self, conn, account_id, from_ts=None, to_ts=None):
        now = int(time.time())
        if from_ts is None:
            from_ts = now - 30 * 86400
        if to_ts is None:
            to_ts = now

        row = conn.execute("""
            SELECT va.id, va.server_type, va.display_name, va.status AS account_status,
                   va.traffic_up_bytes, va.traffic_down_bytes, va.traffic_total_bytes,
                   va.traffic_updated_at, va.traffic_source, va.online_devices,
                   va.direct_config_uri, va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
                   va.direct_hysteria_config_uri,
                   va.direct_config_note,
                   va.account_origin, va.deleted_at,
                   al.telegram_user_id, tu.username AS tg_username, tu.first_name AS tg_first_name,
                   s.status AS subscription_status, s.expires_at, s.traffic_limit_bytes, st.token
            FROM vpn_accounts va
            LEFT JOIN subscriptions s ON va.id = s.vpn_account_id
            LEFT JOIN subscription_tokens st ON va.id = st.vpn_account_id
            LEFT JOIN account_links al ON al.vpn_account_id = va.id
            LEFT JOIN telegram_users tu ON tu.telegram_id = al.telegram_user_id
            WHERE va.id = ? AND va.status != 'deleted'
            GROUP BY va.id
        """, (account_id,)).fetchone()
        if not row:
            return None

        first_snapshot = conn.execute("""
            SELECT up_bytes, down_bytes, captured_at
            FROM traffic_snapshots
            WHERE vpn_account_id = ? AND captured_at >= ? AND captured_at <= ?
            ORDER BY captured_at ASC
            LIMIT 1
        """, (account_id, from_ts, to_ts)).fetchone()
        last_snapshot = conn.execute("""
            SELECT up_bytes, down_bytes, captured_at
            FROM traffic_snapshots
            WHERE vpn_account_id = ? AND captured_at >= ? AND captured_at <= ?
            ORDER BY captured_at DESC
            LIMIT 1
        """, (account_id, from_ts, to_ts)).fetchone()
        snapshot_count = conn.execute("""
            SELECT count(*)
            FROM traffic_snapshots
            WHERE vpn_account_id = ? AND captured_at >= ? AND captured_at <= ?
        """, (account_id, from_ts, to_ts)).fetchone()[0]

        current_up = int(row["traffic_up_bytes"] or 0)
        current_down = int(row["traffic_down_bytes"] or 0)
        if first_snapshot and last_snapshot and snapshot_count > 1:
            range_up = max(0, int(last_snapshot["up_bytes"] or 0) - int(first_snapshot["up_bytes"] or 0))
            range_down = max(0, int(last_snapshot["down_bytes"] or 0) - int(first_snapshot["down_bytes"] or 0))
            range_note = "Расход за выбранный период по snapshots"
        elif row["traffic_source"]:
            range_up = current_up
            range_down = current_down
            if row["traffic_source"] == "hysteria/trafficStats/pending":
                range_note = "Hysteria trafficStats подключён; данные появятся после первого подключения по каскаду"
            else:
                range_note = "История по датам начнёт накапливаться с момента snapshots; сейчас показан накопительный трафик"
        else:
            range_up = 0
            range_down = 0
            range_note = "Hysteria traffic accounting не подключён"

        ips = conn.execute("""
            SELECT ip, max(created_at) AS last_seen, count(*) AS events
            FROM connection_events
            WHERE vpn_account_id = ? AND created_at >= ? AND created_at <= ? AND ip IS NOT NULL AND ip != ''
            GROUP BY ip
            ORDER BY last_seen DESC
            LIMIT 20
        """, (account_id, from_ts, to_ts)).fetchall()

        expires_at = int(row["expires_at"] or 0)
        is_infinite = expires_at >= 4_000_000_000
        days_left = 999999 if is_infinite else max(0, (expires_at - now) // 86400)
        traffic_limit_bytes = int(row["traffic_limit_bytes"] or 0)
        traffic_limit_gb = round(traffic_limit_bytes / (1024 ** 3), 2) if traffic_limit_bytes > 0 else None

        return {
            "id": row["id"],
            "name": self.linked_display_name(row),
            "technical_name": row["display_name"],
            "telegram_user_id": row["telegram_user_id"],
            "type": row["server_type"],
            "origin": row["account_origin"] or "legacy",
            "account_status": row["account_status"],
            "subscription_status": row["subscription_status"],
            "expires_at": self.format_expiry(expires_at),
            "days_left": days_left,
            "is_infinite": is_infinite,
            "sub_link": f"https://{PUBLIC_DOMAIN}/sub/{row['token']}" if row["token"] else None,
            "direct_available": bool(row["direct_config_uri"] or row["direct_tcp_config_uri"] or row["direct_xhttp_config_uri"] or row["direct_hysteria_config_uri"]),
            "direct_tcp_available": bool(row["direct_tcp_config_uri"] or row["direct_config_uri"]),
            "direct_xhttp_available": bool(row["direct_xhttp_config_uri"]),
            "direct_hysteria_available": bool(row["direct_hysteria_config_uri"]),
            "direct_note": row["direct_config_note"],
            "traffic_limit_bytes": traffic_limit_bytes,
            "traffic_limit_gb": traffic_limit_gb,
            "traffic": {
                "used_gb": self.bytes_to_gb(current_up + current_down) if row["traffic_source"] else None,
                "up_gb": self.bytes_to_gb(current_up) if row["traffic_source"] else None,
                "down_gb": self.bytes_to_gb(current_down) if row["traffic_source"] else None,
                "total_gb": self.bytes_to_gb(row["traffic_total_bytes"]) if row["traffic_total_bytes"] else None,
                "range_used_gb": self.bytes_to_gb(range_up + range_down) if row["traffic_source"] else None,
                "range_up_gb": self.bytes_to_gb(range_up) if row["traffic_source"] else None,
                "range_down_gb": self.bytes_to_gb(range_down) if row["traffic_source"] else None,
                "source": row["traffic_source"],
                "snapshot_count": snapshot_count,
                "note": range_note,
            },
            "online_devices": row["online_devices"],
            "ips": [
                {
                    "ip": ip["ip"],
                    "last_seen": time.strftime("%Y-%m-%d %H:%M", time.localtime(ip["last_seen"])),
                    "events": ip["events"],
                }
                for ip in ips
            ],
        }

    def handle_admin_client_detail(self, query):
        if not self.require_admin():
            return
        try:
            account_id = int((query.get("id") or [""])[0])
        except Exception:
            return self.send_json({"error": "invalid_client_id"}, status=400)
        now = int(time.time())
        from_ts = self.parse_date_start((query.get("from") or [""])[0], now - 30 * 86400)
        to_ts = self.parse_date_start((query.get("to") or [""])[0], now) + 86399
        conn = get_db()
        payload = self.build_client_payload(conn, account_id, from_ts, to_ts)
        conn.close()
        if not payload:
            return self.send_json({"error": "client_not_found"}, status=404)
        return self.send_json({"client": payload})

    def handle_admin_client_delete(self, body):
        if not self.require_admin():
            return
        try:
            account_id = int(body.get("id") or 0)
        except Exception:
            return self.send_json({"error": "invalid_client_id"}, status=400)
        if not account_id:
            return self.send_json({"error": "missing_client_id"}, status=400)

        conn = get_db()
        row = conn.execute("""
            SELECT id, display_name, server_type, account_origin, status
            FROM vpn_accounts
            WHERE id = ?
        """, (account_id,)).fetchone()
        conn.close()
        if not row:
            return self.send_json({"error": "client_not_found"}, status=404)
        if (row["account_origin"] or "legacy") != "miniapp":
            return self.send_json({"error": "legacy_delete_blocked"}, status=409)

        try:
            metadata = self.delete_miniapp_account(account_id, actor="telegram_admin")
        except (HysteriaUsersError, XUIConfigError, XUIAPIError, LatviaHysteriaError) as e:
            return self.send_json({"error": str(e)}, status=502)
        except Exception:
            return self.send_json({"error": "client_delete_failed"}, status=500)
        return self.send_json({"ok": True, "deleted": True, "metadata": metadata})

    @staticmethod
    def delete_miniapp_account(account_id, actor="system"):
        now = int(time.time())
        conn = get_db()
        row = conn.execute("""
            SELECT id, display_name, server_type, account_origin, status
            FROM vpn_accounts
            WHERE id = ?
        """, (account_id,)).fetchone()
        conn.close()
        if not row:
            raise ValueError("client_not_found")
        if (row["account_origin"] or "legacy") != "miniapp":
            raise ValueError("legacy_delete_blocked")

        name = row["display_name"]
        metadata = {
            "display_name": name,
            "hysteria_deleted": False,
            "latvia_hysteria_deleted": False,
            "xui_tcp_deleted": False,
            "xui_xhttp_deleted": False,
        }

        xui = XUIClient()
        for transport, key in (("tcp", "xui_tcp_deleted"), ("xhttp", "xui_xhttp_deleted")):
            result = xui.delete_direct_client(name, transport=transport)
            metadata[key] = bool(result.get("deleted"))

        if row["server_type"] == "hysteria":
            metadata["hysteria_deleted"] = bool(delete_hysteria_user(name))
            metadata["latvia_hysteria_deleted"] = bool(delete_latvia_hysteria_user(name).get("changed"))

        conn = get_db()
        with conn:
            conn.execute(
                "UPDATE vpn_accounts SET status = 'deleted', deleted_at = ? WHERE id = ?",
                (now, account_id),
            )
            conn.execute("UPDATE subscriptions SET status = 'expired' WHERE vpn_account_id = ?", (account_id,))
            conn.execute(
                "UPDATE subscription_tokens SET revoked_at = ? WHERE vpn_account_id = ? AND revoked_at IS NULL",
                (now, account_id),
            )
            conn.execute("DELETE FROM account_links WHERE vpn_account_id = ?", (account_id,))
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES (?, 'admin_client_delete', ?, 'ok', ?, ?)""",
                (actor, str(account_id), now, json.dumps(metadata, ensure_ascii=False)),
            )
        conn.close()
        return metadata

    def record_connection_event(self, vpn_account_id, source, event_type):
        conn = get_db()
        with conn:
            conn.execute(
                """INSERT INTO connection_events (vpn_account_id, source, event_type, ip, user_agent, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    vpn_account_id,
                    source,
                    event_type,
                    self.get_client_ip(),
                    self.headers.get("User-Agent", "")[:300],
                    int(time.time()),
                )
            )
        conn.close()

    def handle_admin_extend(self, body):
        if not self.require_admin():
            return
        vpn_account_id = body.get("id")
        add_days = body.get("days", 30)

        if not vpn_account_id:
            return self.send_json({"error": "Missing id"}, status=400)

        conn = get_db()
        sub = conn.execute("SELECT expires_at FROM subscriptions WHERE vpn_account_id = ?", (vpn_account_id,)).fetchone()
        now = int(time.time())
        if add_days == "infinite":
            new_exp = 4102444800
        else:
            try:
                add_days = int(add_days)
            except Exception:
                conn.close()
                return self.send_json({"error": "invalid_days"}, status=400)
            if add_days not in (5, 15, 30):
                conn.close()
                return self.send_json({"error": "unsupported_days"}, status=400)
            current_exp = sub["expires_at"] if sub and sub["expires_at"] > now else now
            new_exp = current_exp + (add_days * 86400)

        with conn:
            conn.execute(
                "UPDATE subscriptions SET expires_at = ?, status = 'active' WHERE vpn_account_id = ?",
                (new_exp, vpn_account_id)
            )
        conn.close()

        return self.send_json({"ok": True, "new_expires_at": self.format_expiry(new_exp)})

    @staticmethod
    def parse_plan_days(value):
        if value == "infinite":
            return "infinite"
        try:
            days = int(value)
        except Exception:
            raise ValueError("invalid_days")
        if days not in (5, 15, 30):
            raise ValueError("unsupported_days")
        return days

    def create_local_hysteria_account(self, username, auth_secret, days):
        now = int(time.time())
        expires_at = 4102444800 if days == "infinite" else now + (int(days) * 86400)
        plan_id = "infinite" if days == "infinite" else f"{days}_days"

        conn = get_db()
        with conn:
            existing = conn.execute(
                "SELECT id FROM vpn_accounts WHERE server_type = 'hysteria' AND display_name = ?",
                (username,)
            ).fetchone()
            if existing:
                account_id = existing["id"]
                conn.execute(
                    """UPDATE vpn_accounts
                       SET external_key = ?, status = 'active',
                           traffic_source = COALESCE(traffic_source, 'hysteria/trafficStats/pending'),
                           traffic_updated_at = COALESCE(traffic_updated_at, ?),
                           online_devices = COALESCE(online_devices, 0)
                       WHERE id = ?""",
                    (auth_secret, now, account_id)
                )
            else:
                cursor = conn.execute(
                    """INSERT INTO vpn_accounts
                       (server_type, server_name, external_key, display_name, status, created_at, account_origin,
                        traffic_source, traffic_up_bytes, traffic_down_bytes, traffic_total_bytes, traffic_updated_at,
                        online_devices)
                       VALUES ('hysteria', 'main', ?, ?, 'active', ?, 'miniapp',
                               'hysteria/trafficStats/pending', 0, 0, 0, ?, 0)""",
                    (auth_secret, username, now, now)
                )
                account_id = cursor.lastrowid
                conn.execute(
                    """INSERT INTO traffic_snapshots
                       (vpn_account_id, up_bytes, down_bytes, total_bytes, source, captured_at)
                       VALUES (?, 0, 0, 0, 'hysteria/trafficStats/pending', ?)""",
                    (account_id, now)
                )

            sub = conn.execute(
                "SELECT id FROM subscriptions WHERE vpn_account_id = ?",
                (account_id,)
            ).fetchone()
            if sub:
                conn.execute(
                    """UPDATE subscriptions
                       SET status = 'active', expires_at = ?, plan_id = ?
                       WHERE vpn_account_id = ?""",
                    (expires_at, plan_id, account_id)
                )
            else:
                conn.execute(
                    """INSERT INTO subscriptions
                       (vpn_account_id, status, starts_at, expires_at, plan_id)
                       VALUES (?, 'active', ?, ?, ?)""",
                    (account_id, now, expires_at, plan_id)
                )

            token = get_or_create_sub_token(account_id, conn)
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'hysteria_create', ?, 'ok', ?, ?)""",
                (
                    str(account_id),
                    now,
                    json.dumps({"username": username, "days": days}, ensure_ascii=False),
                )
            )
        conn.close()
        return account_id, token, expires_at

    def attach_direct_profile(self, account_id, direct_uri, note, transport="tcp"):
        now = int(time.time())
        transport = (transport or "").lower()
        if transport == "xhttp":
            uri_column = "direct_xhttp_config_uri"
        elif transport == "hysteria":
            uri_column = "direct_hysteria_config_uri"
        else:
            uri_column = "direct_tcp_config_uri"
        action = "latvia_hysteria_direct_attach" if transport == "hysteria" else "xui_direct_attach"
        conn = get_db()
        with conn:
            conn.execute(
                f"""UPDATE vpn_accounts
                    SET {uri_column} = ?, direct_config_uri = COALESCE(direct_config_uri, ?),
                        account_origin = 'miniapp',
                        direct_config_updated_at = ?, direct_config_note = ?
                    WHERE id = ?""",
                (direct_uri, direct_uri, now, note, account_id)
            )
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', ?, ?, 'ok', ?, ?)""",
                (action, str(account_id), now, json.dumps({"note": note}, ensure_ascii=False))
            )
        conn.close()

    def handle_admin_create_hysteria(self, body):
        if not self.require_admin():
            return

        username = (body.get("username") or "").strip()
        created = None
        try:
            days = self.parse_plan_days(body.get("days", 30))
            created = create_hysteria_user(username)
            auth_check = verify_auth(created["auth_secret"], expected_id=username)
            if not auth_check["ok"]:
                delete_hysteria_user(username)
                return self.send_json({"error": "auth_verification_failed"}, status=500)

            account_id, token, expires_at = self.create_local_hysteria_account(
                username,
                created["auth_secret"],
                days,
            )
        except ValueError as e:
            return self.send_json({"error": str(e)}, status=400)
        except HysteriaUsersError as e:
            code = str(e)
            status = 409 if code == "username_already_exists" else 400
            return self.send_json({"error": code}, status=status)
        except Exception:
            if created:
                try:
                    delete_hysteria_user(username)
                except Exception:
                    pass
            return self.send_json({"error": "create_failed"}, status=500)

        return self.send_json({
            "ok": True,
            "account_id": account_id,
            "name": username,
            "expires_at": self.format_expiry(expires_at),
            "sub_link": f"https://{PUBLIC_DOMAIN}/sub/{token}",
            "auth_verified": True,
            "users_file": DEFAULT_USERS_FILE,
            "backup": os.path.basename(created["backup_path"]),
        })

    @staticmethod
    def mark_promocode_account(account_id, code, expires_at):
        now = int(time.time())
        conn = get_db()
        with conn:
            conn.execute(
                """UPDATE vpn_accounts
                   SET account_origin = 'miniapp',
                       created_by_promocode = ?,
                       auto_delete_at = ?,
                       deleted_at = NULL
                   WHERE id = ?""",
                (code, expires_at, account_id),
            )
            conn.execute(
                """INSERT INTO audit_log
                   (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'promocode_auto_delete_set', ?, 'ok', ?, ?)""",
                (
                    str(account_id),
                    now,
                    json.dumps({"code": code, "auto_delete_at": expires_at}, ensure_ascii=False),
                ),
            )
        conn.close()

    @staticmethod
    def rollback_promocode_key_issue(username, created, account_id, xui, transports):
        for transport in reversed(transports or []):
            try:
                if transport == "hysteria":
                    delete_latvia_hysteria_user(username)
                elif xui:
                    xui.delete_direct_client(username, transport=transport)
            except Exception:
                pass
        if created:
            try:
                delete_hysteria_user(username)
            except Exception:
                pass
        if account_id:
            now = int(time.time())
            conn = get_db()
            with conn:
                conn.execute(
                    "UPDATE vpn_accounts SET status = 'deleted', deleted_at = ? WHERE id = ?",
                    (now, account_id),
                )
                conn.execute(
                    "UPDATE subscription_tokens SET revoked_at = ? WHERE vpn_account_id = ? AND revoked_at IS NULL",
                    (now, account_id),
                )
                conn.execute("DELETE FROM account_links WHERE vpn_account_id = ?", (account_id,))
            conn.close()

    def handle_admin_create_xui_direct(self, body):
        if not self.require_admin():
            return
        try:
            account_id = int(body.get("account_id") or 0)
        except Exception:
            return self.send_json({"error": "invalid_account_id"}, status=400)
        if not account_id:
            return self.send_json({"error": "missing_account_id"}, status=400)

        conn = get_db()
        account = conn.execute("""
            SELECT va.id, va.display_name, va.direct_config_uri,
                   va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
                   va.direct_hysteria_config_uri, va.external_key,
                   s.expires_at
            FROM vpn_accounts va
            LEFT JOIN subscriptions s ON va.id = s.vpn_account_id
            WHERE va.id = ?
        """, (account_id,)).fetchone()
        conn.close()
        if not account:
            return self.send_json({"error": "account_not_found"}, status=404)
        transport = (body.get("transport") or "tcp").strip().lower()
        if transport not in ("tcp", "xhttp", "hysteria"):
            return self.send_json({"error": "unsupported_xui_transport"}, status=400)
        if transport == "tcp" and account["direct_tcp_config_uri"]:
            return self.send_json({"ok": True, "created": False, "message": "direct_tcp_already_attached"})
        if transport == "xhttp" and account["direct_xhttp_config_uri"]:
            return self.send_json({"ok": True, "created": False, "message": "direct_xhttp_already_attached"})
        if transport == "hysteria" and account["direct_hysteria_config_uri"]:
            return self.send_json({"ok": True, "created": False, "message": "direct_hysteria_already_attached"})

        try:
            if transport == "hysteria":
                result = attach_latvia_hysteria_user(account["display_name"], account["external_key"])
                result["created"] = bool(result.get("changed"))
                result["inbound_id"] = "latvia-hysteria"
            else:
                result = XUIClient().create_direct_client(
                    account["display_name"],
                    expiry_time_seconds=account["expires_at"] or 0,
                    transport=transport,
                )
        except XUIConfigError as e:
            return self.send_json({"error": str(e)}, status=409)
        except XUIAPIError as e:
            return self.send_json({"error": str(e)}, status=502)
        except LatviaHysteriaError as e:
            return self.send_json({"error": str(e)}, status=502)
        except Exception:
            return self.send_json({"error": "xui_direct_create_failed"}, status=500)

        self.attach_direct_profile(
            account_id,
            result["uri"],
            "Latvia Hysteria direct inbound" if transport == "hysteria" else f"x-ui managed inbound #{result['inbound_id']}",
            transport=transport,
        )
        return self.send_json({
            "ok": True,
            "created": result["created"],
            "account_id": account_id,
            "message": "direct_profile_attached",
        })

    def handle_admin_client_set_limit(self, body):
        """POST /api/admin/client/set-limit
        body: { id: int, limit_gb: float|null }
        limit_gb == null or 0 → безлимит
        """
        if not self.require_admin():
            return
        try:
            account_id = int(body.get("id") or 0)
        except Exception:
            return self.send_json({"error": "invalid_client_id"}, status=400)
        if not account_id:
            return self.send_json({"error": "missing_client_id"}, status=400)

        limit_gb = body.get("limit_gb")
        try:
            if limit_gb is None or limit_gb == "" or float(limit_gb) <= 0:
                limit_bytes = 0  # unlimited
            else:
                limit_bytes = int(float(limit_gb) * (1024 ** 3))
        except Exception:
            return self.send_json({"error": "invalid_limit_gb"}, status=400)

        now = int(time.time())
        conn = get_db()
        sub = conn.execute(
            "SELECT id FROM subscriptions WHERE vpn_account_id = ?", (account_id,)
        ).fetchone()
        if not sub:
            conn.close()
            return self.send_json({"error": "subscription_not_found"}, status=404)

        with conn:
            conn.execute(
                "UPDATE subscriptions SET traffic_limit_bytes = ? WHERE vpn_account_id = ?",
                (limit_bytes, account_id)
            )
            conn.execute(
                """INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
                   VALUES ('telegram_admin', 'set_traffic_limit', ?, 'ok', ?, ?)""",
                (str(account_id), now, json.dumps({"limit_bytes": limit_bytes, "limit_gb": limit_gb}))
            )
        conn.close()

        return self.send_json({
            "ok": True,
            "traffic_limit_bytes": limit_bytes,
            "traffic_limit_gb": round(limit_bytes / (1024 ** 3), 2) if limit_bytes > 0 else None,
        })

    def handle_admin_client_grant_trial(self, body):
        """POST /api/admin/client/grant-trial
        body: { telegram_user_id: int, hours: int (default 24) }
        Выдаёт/продлевает триальный период. Сбрасывает trial_used.
        """
        if not self.require_admin():
            return
        try:
            telegram_user_id = int(body.get("telegram_user_id") or 0)
        except Exception:
            return self.send_json({"error": "invalid_telegram_user_id"}, status=400)
        if not telegram_user_id:
            return self.send_json({"error": "missing_telegram_user_id"}, status=400)

        try:
            hours = max(1, min(int(body.get("hours", 24) or 24), 720))
        except Exception:
            hours = 24

        now = int(time.time())
        conn = get_db()

        # Сбрасываем trial_used чтобы пользователь мог воспользоваться триалом
        with conn:
            conn.execute(
                "UPDATE telegram_users SET trial_used = 0 WHERE telegram_id = ?",
                (telegram_user_id,)
            )

        # Ищем существующий аккаунт пользователя
        linked = conn.execute("""
            SELECT al.vpn_account_id, s.expires_at, s.status
            FROM account_links al
            JOIN vpn_accounts va ON al.vpn_account_id = va.id
            LEFT JOIN subscriptions s ON va.id = s.vpn_account_id
            WHERE al.telegram_user_id = ? AND va.status != 'deleted'
            ORDER BY al.linked_at DESC
            LIMIT 1
        """, (telegram_user_id,)).fetchone()

        if linked:
            # Продлеваем существующий аккаунт
            vpn_account_id = linked["vpn_account_id"]
            current_exp = linked["expires_at"] if linked["expires_at"] and linked["expires_at"] > now else now
            new_exp = current_exp + (hours * 3600)
            with conn:
                conn.execute(
                    "UPDATE subscriptions SET expires_at = ?, status = 'active' WHERE vpn_account_id = ?",
                    (new_exp, vpn_account_id)
                )
                conn.execute(
                    "UPDATE vpn_accounts SET status = 'active' WHERE id = ?",
                    (vpn_account_id,)
                )
                conn.execute(
                    """INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
                       VALUES ('telegram_admin', 'grant_trial', ?, 'ok', ?, ?)""",
                    (str(vpn_account_id), now, json.dumps({"hours": hours, "telegram_user_id": telegram_user_id}))
                )
            conn.close()
            return self.send_json({
                "ok": True,
                "action": "extended",
                "vpn_account_id": vpn_account_id,
                "new_expires_at": self.format_expiry(new_exp),
                "hours_added": hours,
            })
        else:
            conn.close()
            # Нет аккаунта — сообщаем что надо создать через панель или юзер сам нажмёт Trial
            return self.send_json({
                "ok": True,
                "action": "trial_reset",
                "message": "trial_used сброшен. Пользователь может активировать триал через бота.",
                "hours_configured": hours,
            })

def run_server():
    init_db()
    socketserver.TCPServer.allow_reuse_address = True
    server_address = ('127.0.0.1', PORT)
    httpd = socketserver.TCPServer(server_address, AppRequestHandler)
    print(f"Telegram Mini App backend running at http://127.0.0.1:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
