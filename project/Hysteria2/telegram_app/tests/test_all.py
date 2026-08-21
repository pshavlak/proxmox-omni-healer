import unittest
import os
import sys
import tempfile
import json
import sqlite3
import time
import hmac
import hashlib
import urllib.parse

# Ensure path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import db, importers, hysteria_users, latvia_hysteria, telegram_auth

def signed_init_data(bot_token, user):
    params = {
        "auth_date": str(int(time.time())),
        "user": json.dumps(user, separators=(",", ":")),
    }
    data_check_string = "\n".join(f"{k}={params[k]}" for k in sorted(params))
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urllib.parse.urlencode(params)

class TestMiniAppBackend(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.tmp_dir.name, "test_app.db")
        os.environ["MINIAPP_DB_PATH"] = self.db_path
        db.init_db()

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_db_initialization(self):
        conn = db.get_db()
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        conn.close()
        self.assertIn("telegram_users", tables)
        self.assertIn("vpn_accounts", tables)
        self.assertIn("subscriptions", tables)
        self.assertIn("subscription_tokens", tables)
        self.assertIn("traffic_snapshots", tables)
        self.assertIn("subscription_devices", tables)
        self.assertIn("payment_settings", tables)
        conn = db.get_db()
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(vpn_accounts)").fetchall()]
        self.assertIn("online_devices", columns)
        self.assertIn("routing_mode", columns)
        self.assertIn("direct_config_uri", columns)
        self.assertIn("direct_hysteria_config_uri", columns)
        self.assertIn("created_by_promocode", columns)
        self.assertIn("auto_delete_at", columns)
        self.assertIn("deleted_at", columns)
        promo_columns = [r["name"] for r in conn.execute("PRAGMA table_info(promocodes)").fetchall()]
        receipt_columns = [r["name"] for r in conn.execute("PRAGMA table_info(manual_receipts)").fetchall()]
        pay = conn.execute("SELECT * FROM payment_settings WHERE id = 1").fetchone()
        conn.close()
        self.assertIn("issue_key_on_activation", promo_columns)
        self.assertIn("currency", receipt_columns)
        self.assertIsNotNone(pay)
        self.assertEqual(pay["manual_enabled"], 0)

    def test_hysteria_import(self):
        # Create mock users.json in the production project shape:
        # {"username": "auth_password"}
        users_path = os.path.join(self.tmp_dir.name, "users.json")
        mock_users = {
            "Alice": "user_secret_token_1",
            "Bob": "user_secret_token_2"
        }
        with open(users_path, "w", encoding="utf-8") as f:
            json.dump(mock_users, f)

        count = importers.import_hysteria_users(users_path)
        self.assertEqual(count, 2)

        conn = db.get_db()
        accounts = conn.execute("SELECT * FROM vpn_accounts WHERE server_type = 'hysteria'").fetchall()
        self.assertEqual(len(accounts), 2)
        alice = conn.execute("SELECT * FROM vpn_accounts WHERE display_name = 'Alice'").fetchone()
        self.assertIsNotNone(alice)
        self.assertEqual(alice["external_key"], "user_secret_token_1")
        conn.close()

    def test_hysteria_import_legacy_dict_shape(self):
        users_path = os.path.join(self.tmp_dir.name, "legacy-users.json")
        mock_users = {
            "legacy_key": {"name": "Legacy Alice", "auth": "legacy_secret"}
        }
        with open(users_path, "w", encoding="utf-8") as f:
            json.dump(mock_users, f)

        count = importers.import_hysteria_users(users_path)
        self.assertEqual(count, 1)

        conn = db.get_db()
        account = conn.execute("SELECT * FROM vpn_accounts WHERE display_name = 'Legacy Alice'").fetchone()
        conn.close()
        self.assertIsNotNone(account)
        self.assertEqual(account["external_key"], "legacy_secret")

    def test_safe_hysteria_user_create_and_delete(self):
        users_path = os.path.join(self.tmp_dir.name, "users.json")
        backup_dir = os.path.join(self.tmp_dir.name, "backups")
        with open(users_path, "w", encoding="utf-8") as f:
            json.dump({"existing": "old_secret"}, f)

        created = hysteria_users.create_hysteria_user(
            "new-client_1",
            users_file=users_path,
            backup_dir=backup_dir,
        )
        self.assertEqual(created["username"], "new-client_1")
        self.assertTrue(len(created["auth_secret"]) >= 20)
        self.assertTrue(os.path.exists(created["backup_path"]))

        with open(users_path, "r", encoding="utf-8") as f:
            users = json.load(f)
        self.assertEqual(users["existing"], "old_secret")
        self.assertEqual(users["new-client_1"], created["auth_secret"])

        with self.assertRaises(hysteria_users.HysteriaUsersError):
            hysteria_users.create_hysteria_user(
                "new-client_1",
                users_file=users_path,
                backup_dir=backup_dir,
            )

        self.assertTrue(hysteria_users.delete_hysteria_user(
            "new-client_1",
            users_file=users_path,
            backup_dir=backup_dir,
        ))
        with open(users_path, "r", encoding="utf-8") as f:
            users = json.load(f)
        self.assertNotIn("new-client_1", users)
        self.assertEqual(users["existing"], "old_secret")

    def test_hysteria_username_validation(self):
        self.assertEqual(hysteria_users.validate_username("client.01-test"), "client.01-test")
        with self.assertRaises(hysteria_users.HysteriaUsersError):
            hysteria_users.validate_username("bad user")

    def test_xui_import(self):
        # Create mock x-ui.db
        xui_path = os.path.join(self.tmp_dir.name, "x-ui.db")
        xui_conn = sqlite3.connect(xui_path)
        xui_conn.execute("""
            CREATE TABLE client_traffics (
                id INTEGER PRIMARY KEY,
                inbound_id INTEGER,
                enable NUMERIC,
                email TEXT,
                up INTEGER,
                down INTEGER,
                expiry_time INTEGER,
                total INTEGER,
                reset INTEGER DEFAULT 0
            )
        """)
        xui_conn.execute("""
            CREATE TABLE inbounds (
                id INTEGER PRIMARY KEY,
                enable NUMERIC,
                port INTEGER,
                protocol TEXT,
                settings TEXT,
                stream_settings TEXT
            )
        """)
        inbound_settings = {
            "clients": [{
                "email": "cascade_client_1",
                "enable": True,
                "id": "11111111-1111-4111-8111-111111111111",
                "flow": "xtls-rprx-vision"
            }]
        }
        stream_settings = {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "serverNames": ["finavia.fi"],
                "shortIds": ["abcd"],
                "settings": {
                    "publicKey": "pubkey123",
                    "fingerprint": "chrome",
                    "spiderX": "/"
                }
            }
        }
        xui_conn.execute(
            "INSERT INTO inbounds (id, enable, port, protocol, settings, stream_settings) VALUES (1, 1, 443, 'vless', ?, ?)",
            (json.dumps(inbound_settings), json.dumps(stream_settings))
        )
        xui_conn.execute("""
            INSERT INTO client_traffics (id, inbound_id, enable, email, up, down, expiry_time, total)
            VALUES (1, 1, 1, 'cascade_client_1', 1073741824, 2147483648, 1800000000000, 10737418240)
        """)
        xui_conn.commit()
        xui_conn.close()

        count = importers.import_xui_clients(xui_path)
        self.assertEqual(count, 1)

        conn = db.get_db()
        acc = conn.execute("SELECT * FROM vpn_accounts WHERE server_type = 'xui'").fetchone()
        self.assertIsNotNone(acc)
        self.assertEqual(acc["display_name"], "cascade_client_1")
        self.assertEqual(acc["traffic_up_bytes"], 1073741824)
        self.assertEqual(acc["traffic_down_bytes"], 2147483648)
        self.assertEqual(acc["traffic_total_bytes"], 10737418240)
        self.assertIn("vless://11111111-1111-4111-8111-111111111111@193.164.155.153:443", acc["direct_config_uri"])
        self.assertIn("security=reality", acc["direct_config_uri"])
        snap = conn.execute("SELECT * FROM traffic_snapshots WHERE vpn_account_id = ?", (acc["id"],)).fetchone()
        self.assertIsNotNone(snap)
        self.assertEqual(snap["up_bytes"], 1073741824)
        conn.close()

    def test_subscription_token_generation(self):
        token = db.get_or_create_sub_token(1)
        self.assertTrue(len(token) > 10)
        # Check idempotency
        token2 = db.get_or_create_sub_token(1)
        self.assertEqual(token, token2)

    def test_subscription_device_registry_from_headers(self):
        from backend import server

        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts (server_type, server_name, external_key, display_name)
            VALUES ('hysteria', 'main', 'secret', 'Device User')
        """)
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        conn.close()

        handler = object.__new__(server.AppRequestHandler)
        handler.headers = {
            "User-Agent": "Happ/1.2.3 (iOS)",
            "X-Hwid": "device-uuid-1",
            "X-Device-Model": "iPhone 11 Pro",
            "X-Platform": "iOS",
            "X-Client-Version": "1.2.3",
            "X-Real-IP": "198.51.100.10",
        }
        handler.client_address = ("127.0.0.1", 12345)
        handler.record_subscription_device(account_id)
        handler.record_subscription_device(account_id)

        conn = db.get_db()
        device = conn.execute(
            "SELECT * FROM subscription_devices WHERE vpn_account_id = ?",
            (account_id,)
        ).fetchone()
        conn.close()

        self.assertIsNotNone(device)
        self.assertEqual(device["hwid"], "device-uuid-1")
        self.assertEqual(device["device_model"], "iPhone 11 Pro")
        self.assertEqual(device["platform"], "iOS")
        self.assertEqual(device["client_name"], "Happ")
        self.assertEqual(device["hits"], 2)

    def test_subscription_device_reset_hides_devices(self):
        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts (server_type, server_name, external_key, display_name)
            VALUES ('hysteria', 'main', 'secret', 'Reset User')
        """)
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO subscription_devices (
                vpn_account_id, device_key, device_model, platform, first_seen_at, last_seen_at
            )
            VALUES (?, 'dev-key', 'MacBook', 'macOS', 1000, 1000)
        """, (account_id,))
        conn.commit()
        conn.close()

        from backend import server
        handler = object.__new__(server.AppRequestHandler)
        conn = db.get_db()
        devices = handler.list_account_devices(conn, account_id)
        conn.execute("UPDATE subscription_devices SET is_reset = 1 WHERE vpn_account_id = ?", (account_id,))
        hidden = handler.list_account_devices(conn, account_id)
        conn.close()

        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["name"], "MacBook (macOS)")
        self.assertEqual(hidden, [])

    def test_promocode_activation(self):
        conn = db.get_db()
        promo = conn.execute("SELECT * FROM promocodes WHERE code = 'START2026'").fetchone()
        conn.close()
        self.assertIsNotNone(promo)
        self.assertEqual(promo["bonus_days"], 7)

    def test_promocode_without_subscription_issues_key(self):
        from backend import server

        class PromoHandler(server.AppRequestHandler):
            def __init__(self):
                pass

            def get_telegram_user(self):
                return {"id": 555, "first_name": "New"}

            def send_json(self, payload, status=200):
                return {"status": status, "payload": payload}

            def issue_promocode_key(self, telegram_user, promo, code):
                return {"issued": True, "telegram_id": telegram_user["id"], "code": code}

        handler = PromoHandler()
        result = handler.handle_apply_promocode({"code": "START2026"})
        self.assertEqual(result, {"issued": True, "telegram_id": 555, "code": "START2026"})

    def test_payment_settings_payload(self):
        from backend import server

        conn = db.get_db()
        conn.execute("""
            UPDATE payment_settings
            SET manual_enabled = 1, bank_name = 'Bank', recipient_name = 'Owner',
                card_number = '0000', sbp_phone = '+7000', payment_comment = 'VPN',
                user_instructions = 'Send transfer'
            WHERE id = 1
        """)
        conn.commit()
        row = conn.execute("SELECT * FROM payment_settings WHERE id = 1").fetchone()
        conn.close()

        payload = server.AppRequestHandler.payment_settings_payload(row)
        self.assertTrue(payload["manual_enabled"])
        self.assertEqual(payload["bank_name"], "Bank")

    def test_payment_requests_create_admin_items(self):
        from backend import server

        class PaymentHandler(server.AppRequestHandler):
            def __init__(self):
                pass

            def get_telegram_user(self):
                return {"id": 777, "first_name": "Pay"}

            def send_json(self, payload, status=200):
                return {"status": status, "payload": payload}

        handler = PaymentHandler()
        stars = handler.handle_stars_payment_request({"amount": 150})
        self.assertTrue(stars["payload"]["ok"])

        conn = db.get_db()
        with conn:
            conn.execute("UPDATE payment_settings SET manual_enabled = 1 WHERE id = 1")
        conn.close()

        card = handler.handle_manual_receipt({"amount": 300, "note": "card check"})
        self.assertTrue(card["payload"]["ok"])

        conn = db.get_db()
        rows = conn.execute("SELECT amount, currency, status FROM manual_receipts ORDER BY id").fetchall()
        conn.close()
        self.assertEqual([(r["amount"], r["currency"], r["status"]) for r in rows], [
            (150.0, "STARS", "pending"),
            (300.0, "RUB", "pending"),
        ])

    def test_unlinked_telegram_user_gets_no_account(self):
        from backend import server

        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts (server_type, server_name, external_key, display_name)
            VALUES ('hysteria', 'main', 'secret', 'Owner Account')
        """)
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
            VALUES (?, 'active', 1000, 2000000000, '1_month')
        """, (account_id,))
        conn.execute("""
            INSERT INTO subscription_tokens (vpn_account_id, token, created_at)
            VALUES (?, 'owner_token', 1000)
        """, (account_id,))
        conn.commit()

        handler = object.__new__(server.AppRequestHandler)
        self.assertIsNone(handler.get_user_account(conn, {"id": 404, "first_name": "New"}))
        conn.close()

    def test_client_payload_includes_origin(self):
        from backend import server

        now = int(time.time())
        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts
              (server_type, server_name, external_key, display_name, account_origin, status)
            VALUES ('hysteria', 'main', 'secret', 'Mini User', 'miniapp', 'active')
        """)
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
            VALUES (?, 'active', ?, ?, '30_days')
        """, (account_id, now, now + 86400))
        conn.execute("""
            INSERT INTO subscription_tokens (vpn_account_id, token, created_at)
            VALUES (?, 'mini_token', ?)
        """, (account_id, now))
        conn.execute("""
            INSERT INTO telegram_users (telegram_id, username, first_name, role, created_at, last_seen_at)
            VALUES (777, 'buyer', 'Buyer Name', 'user', ?, ?)
        """, (now, now))
        conn.execute("""
            INSERT INTO account_links (telegram_user_id, vpn_account_id, linked_at, link_method)
            VALUES (777, ?, ?, 'payment')
        """, (account_id, now))
        conn.commit()

        handler = object.__new__(server.AppRequestHandler)
        payload = handler.build_client_payload(conn, account_id)
        conn.close()
        self.assertEqual(payload["origin"], "miniapp")
        self.assertEqual(payload["name"], "Buyer Name (@buyer)")
        self.assertEqual(payload["technical_name"], "Mini User")

    def test_deleted_client_detail_is_hidden(self):
        from backend import server

        now = int(time.time())
        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts
              (server_type, server_name, external_key, display_name, account_origin, status, deleted_at)
            VALUES ('hysteria', 'main', 'secret', 'Deleted User', 'miniapp', 'deleted', ?)
        """, (now,))
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
            VALUES (?, 'expired', ?, ?, '30_days')
        """, (account_id, now - 86400, now + 86400))
        conn.execute("""
            INSERT INTO subscription_tokens (vpn_account_id, token, created_at)
            VALUES (?, 'deleted_token', ?)
        """, (account_id, now))
        conn.commit()

        handler = object.__new__(server.AppRequestHandler)
        self.assertIsNone(handler.build_client_payload(conn, account_id))
        conn.close()

    def test_admin_promocode_helpers(self):
        from backend import server

        self.assertEqual(server.AppRequestHandler.normalize_promocode(" start_15 "), "START_15")
        expiry = server.AppRequestHandler.parse_promocode_expiry("2026-08-12")
        self.assertGreaterEqual(expiry, 1786478400)
        username = server.AppRequestHandler.promo_username({"id": 777}, "BONUS30")
        self.assertTrue(username.startswith("tg777_BONUS30_"))
        with self.assertRaises(ValueError):
            server.AppRequestHandler.normalize_promocode("подарок")
        with self.assertRaises(ValueError):
            server.AppRequestHandler.parse_promocode_expiry("12.08.2026")

    def test_xui_add_client_payload_and_uri_builder(self):
        from backend import xui_api

        self.assertEqual(xui_api.transport_email("Test_app", "tcp"), "Test_app__tcp")
        self.assertEqual(xui_api.transport_email("Test_app", "xhttp"), "Test_app__xhttp")
        self.assertEqual(xui_api.transport_email("Test_app", "hysteria"), "Test_app__hysteria")
        self.assertEqual(
            xui_api.vless_client_uuid("vless://22222222-2222-4222-8222-222222222222@example.com:443#Name"),
            "22222222-2222-4222-8222-222222222222",
        )

        client = xui_api.build_client_payload(
            "new-direct",
            expiry_time_seconds=1800000000,
            client_uuid="22222222-2222-4222-8222-222222222222",
        )
        self.assertEqual(client["email"], "new-direct")
        self.assertEqual(client["expiryTime"], 1800000000000)
        body = xui_api.add_client_request_body(9, client)
        self.assertEqual(body["id"], 9)
        self.assertIn("new-direct", body["settings"])

        inbound = {
            "port": 443,
            "streamSettings": json.dumps({
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "serverNames": ["finavia.fi"],
                    "shortIds": ["abcd"],
                    "settings": {
                        "publicKey": "pubkey123",
                        "fingerprint": "chrome",
                        "spiderX": "/"
                    }
                }
            })
        }
        uri = xui_api.build_vless_uri(inbound, client, "193.164.155.153", label="Латвия TCP")
        self.assertIn("vless://22222222-2222-4222-8222-222222222222@193.164.155.153:443", uri)
        self.assertIn("security=reality", uri)
        self.assertIn("pbk=pubkey123", uri)
        self.assertTrue(uri.endswith("#%D0%9B%D0%B0%D1%82%D0%B2%D0%B8%D1%8F%20TCP"))

        hysteria_inbound = {
            "port": 55446,
            "settings": json.dumps({"version": 2, "clients": []}),
            "streamSettings": json.dumps({
                "network": "hysteria",
                "security": "tls",
                "tlsSettings": {"alpn": ["h3"], "settings": {}},
            }),
        }
        hysteria_uri = xui_api.build_hysteria_uri(
            hysteria_inbound,
            {"auth": "hysteria-secret", "email": "hys"},
            "193.164.155.153",
            label="Латвия Hysteria",
        )
        self.assertEqual(
            hysteria_uri,
            "hysteria2://hysteria-secret@193.164.155.153:55446?security=tls&alpn=h3#%D0%9B%D0%B0%D1%82%D0%B2%D0%B8%D1%8F%20Hysteria",
        )

    def test_latvia_hysteria_uri_builder(self):
        os.environ["XUI_PUBLIC_HOST"] = "193.164.155.153"
        os.environ["XUI_HYSTERIA_PUBLIC_PORT"] = "55446"
        uri = latvia_hysteria.build_hysteria_uri("secret", label="Латвия Hysteria")
        self.assertEqual(
            uri,
            "hysteria2://secret@193.164.155.153:55446?security=tls&alpn=h3#%D0%9B%D0%B0%D1%82%D0%B2%D0%B8%D1%8F%20Hysteria",
        )

    def test_subscription_includes_latvia_hysteria_direct(self):
        from backend import server

        now = int(time.time())
        conn = db.get_db()
        conn.execute("""
            INSERT INTO vpn_accounts
              (server_type, server_name, external_key, display_name,
               direct_tcp_config_uri, direct_xhttp_config_uri, direct_hysteria_config_uri)
            VALUES (
              'hysteria', 'main', 'secret', 'Sub User',
              'vless://tcp@example.com:443#old',
              'vless://xhttp@example.com:443#old',
              'hysteria2://secret@193.164.155.153:55446?security=tls&alpn=h3#old'
            )
        """)
        account_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("""
            INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
            VALUES (?, 'active', ?, ?, '30_days')
        """, (account_id, now, now + 86400))
        conn.execute("""
            INSERT INTO subscription_tokens (vpn_account_id, token, created_at)
            VALUES (?, 'sub_token', ?)
        """, (account_id, now))
        conn.commit()
        conn.close()

        class SubHandler(server.AppRequestHandler):
            def __init__(self):
                self.headers = {}
                self.client_address = ("127.0.0.1", 12345)

            def send_text(self, text, content_type='text/plain', status=200):
                return {"status": status, "text": text}

        result = SubHandler().handle_subscription("sub_token")
        lines = result["text"].splitlines()
        self.assertEqual(len(lines), 4)
        self.assertIn("hist.yupiterpro.ru:8443", lines[0])
        self.assertTrue(lines[3].startswith("hysteria2://secret@193.164.155.153:55446?"))
        self.assertTrue(lines[3].endswith("#%D0%9B%D0%B0%D1%82%D0%B2%D0%B8%D1%8F%20Hysteria"))

    def test_cleanup_selects_only_expired_promocode_keys(self):
        from backend.cleanup_expired_promocode_keys import expired_promocode_accounts

        now = int(time.time())
        conn = db.get_db()
        with conn:
            conn.execute("""
                INSERT INTO vpn_accounts
                  (server_type, server_name, external_key, display_name, status, created_at,
                   account_origin, created_by_promocode, auto_delete_at)
                VALUES ('hysteria', 'main', 'secret1', 'promo_expired', 'active', ?,
                        'miniapp', 'PROMO', ?)
            """, (now - 100, now - 1))
            conn.execute("""
                INSERT INTO vpn_accounts
                  (server_type, server_name, external_key, display_name, status, created_at,
                   account_origin, created_by_promocode, auto_delete_at)
                VALUES ('hysteria', 'main', 'secret2', 'promo_active', 'active', ?,
                        'miniapp', 'PROMO', ?)
            """, (now - 100, now + 3600))
            conn.execute("""
                INSERT INTO vpn_accounts
                  (server_type, server_name, external_key, display_name, status, created_at,
                   account_origin, created_by_promocode, auto_delete_at)
                VALUES ('hysteria', 'main', 'secret3', 'legacy_expired', 'active', ?,
                        'legacy', 'PROMO', ?)
            """, (now - 100, now - 1))
        conn.close()

        names = [r["display_name"] for r in expired_promocode_accounts(now)]
        self.assertEqual(names, ["promo_expired"])

    def test_bot_start_and_account_linking(self):
        from bot.bot import handle_start_command
        # Create a vpn account with sub token 'claim_token_123'
        conn = db.get_db()
        conn.execute("INSERT INTO vpn_accounts (server_type, server_name, external_key, display_name) VALUES ('hysteria', 'main', 'secret', 'User1')")
        acc_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute("INSERT INTO subscription_tokens (vpn_account_id, token, created_at) VALUES (?, 'claim_token_123', 1000)", (acc_id,))
        conn.commit()
        conn.close()

        res = handle_start_command(999, {"username": "linked_user", "first_name": "Link"}, "claim_claim_token_123")
        self.assertTrue(res.get("ok"))

        conn = db.get_db()
        link = conn.execute("SELECT * FROM account_links WHERE telegram_user_id = 999").fetchone()
        conn.close()
        self.assertIsNotNone(link)
        self.assertEqual(link["vpn_account_id"], acc_id)

    def test_parse_start_payload(self):
        from bot.bot import parse_start_payload

        self.assertEqual(parse_start_payload("/start"), "")
        self.assertEqual(parse_start_payload("/start claim_abc"), "claim_abc")
        self.assertEqual(parse_start_payload("/start@kaskad_yupiter_bot claim_abc"), "claim_abc")
        self.assertIsNone(parse_start_payload("/help"))

    def test_handle_update_handles_help(self):
        from bot.bot import handle_update

        handled = handle_update({
            "update_id": 1,
            "message": {
                "chat": {"id": 100},
                "from": {"id": 100, "first_name": "Noop"},
                "text": "/help"
            }
        })
        self.assertTrue(handled)

    def test_telegram_init_data_admin_detection(self):
        from backend import server

        self.assertEqual(server.parse_admin_ids("123, 456;bad"), {123, 456})
        original = server.ADMIN_IDS
        try:
            server.ADMIN_IDS = {123}
            self.assertTrue(server.is_admin_user({"id": 123}))
            self.assertFalse(server.is_admin_user({"id": 456}))
        finally:
            server.ADMIN_IDS = original

    def test_telegram_auth_signature(self):
        init_data = signed_init_data("test-token", {"id": 123, "first_name": "Admin"})
        parsed = telegram_auth.parse_and_verify_init_data(init_data, "test-token")
        self.assertEqual(parsed["id"], 123)

        with self.assertRaises(ValueError):
            telegram_auth.parse_and_verify_init_data(init_data, "wrong-token")

if __name__ == "__main__":
    unittest.main()
