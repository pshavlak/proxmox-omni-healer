import os
import json
import sqlite3
import time
import urllib.parse
from .db import get_db, get_or_create_sub_token

def _normalize_epoch(value):
    if not value:
        return None
    value = int(value)
    if value > 10_000_000_000:
        return value // 1000
    return value

def _normalize_hysteria_user(username, value):
    """Return (display_name, auth_secret) for known users.json shapes."""
    if isinstance(value, str):
        return str(username), value
    if isinstance(value, dict):
        display_name = value.get("name") or value.get("username") or username
        auth_secret = value.get("auth") or value.get("password") or value.get("secret")
        if auth_secret:
            return str(display_name), str(auth_secret)
    return None, None


def import_hysteria_users(users_json_path: str, default_days: int = 30) -> int:
    """Read-only import of Hysteria users.json into local Mini App database.

    The production project stores Hysteria users as:
        {"username": "auth_password"}

    Older/generic fixtures may use:
        {"key": {"name": "Alice", "auth": "secret"}}
    """
    if not users_json_path or not os.path.exists(users_json_path):
        return 0

    with open(users_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = get_db()
    imported_count = 0
    now = int(time.time())
    default_expiry = now + (default_days * 86400)

    with conn:
        for username, user_info in data.items():
            display_name, auth_secret = _normalize_hysteria_user(username, user_info)
            if not auth_secret:
                continue

            # Check existing vpn_account
            row = conn.execute(
                "SELECT id FROM vpn_accounts WHERE server_type = 'hysteria' AND external_key = ?",
                (auth_secret,)
            ).fetchone()

            if row:
                account_id = row["id"]
                conn.execute(
                    "UPDATE vpn_accounts SET display_name = ?, status = 'active' WHERE id = ?",
                    (display_name, account_id)
                )
            else:
                cursor = conn.execute(
                    """INSERT INTO vpn_accounts (server_type, server_name, external_key, display_name, status, created_at, account_origin)
                       VALUES ('hysteria', 'main', ?, ?, 'active', ?, 'legacy')""",
                    (auth_secret, display_name, now)
                )
                account_id = cursor.lastrowid
                imported_count += 1

            # Ensure subscription exists
            sub = conn.execute("SELECT id FROM subscriptions WHERE vpn_account_id = ?", (account_id,)).fetchone()
            if not sub:
                conn.execute(
                    """INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
                       VALUES (?, 'active', ?, ?, '1_month')""",
                    (account_id, now, default_expiry)
                )

            # Ensure subscription token exists
            get_or_create_sub_token(account_id, conn)

    conn.close()
    return imported_count

def import_xui_clients(xui_db_path: str, default_days: int = 30) -> int:
    """Read-only import of x-ui SQLite db (client_traffics / inbounds) into vpn_accounts."""
    try:
        xui_conn = sqlite3.connect(xui_db_path)
        xui_conn.row_factory = sqlite3.Row
    except Exception as e:
        print(f"Skipping x-ui import: {e}")
        return 0

    conn = get_db()
    imported_count = 0
    now = int(time.time())
    default_expiry = now + (default_days * 86400)
    direct_profiles = _load_xui_direct_profiles(xui_conn)

    try:
        cursor = xui_conn.execute("SELECT id, email, enable, up, down, expiry_time, total FROM client_traffics")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"Error querying x-ui db: {e}")
        rows = []

    with conn:
        for r in rows:
            email = r["email"] if r["email"] else f"client_{r['id']}"
            external_key = f"xui_{r['id']}_{email}"
            status = "active" if int(r["enable"] or 0) else "disabled"
            up = int(r["up"] or 0)
            down = int(r["down"] or 0)
            total = int(r["total"] or 0)
            expiry = _normalize_epoch(r["expiry_time"]) or default_expiry
            direct_uri = direct_profiles.get(email.lower())

            existing = conn.execute(
                "SELECT id FROM vpn_accounts WHERE server_type = 'xui' AND external_key = ?",
                (external_key,)
            ).fetchone()

            if existing:
                acc_id = existing["id"]
                conn.execute(
                    """UPDATE vpn_accounts
                       SET display_name = ?, status = ?, traffic_up_bytes = ?, traffic_down_bytes = ?,
                           traffic_total_bytes = ?, traffic_updated_at = ?, traffic_source = 'x-ui/client_traffics',
                           direct_config_uri = ?, direct_config_updated_at = ?, direct_config_note = ?
                       WHERE id = ?""",
                    (email, status, up, down, total, now, direct_uri, now if direct_uri else None, "x-ui/vless-reality" if direct_uri else None, acc_id)
                )
            else:
                c = conn.execute(
                    """INSERT INTO vpn_accounts (
                           server_type, server_name, external_key, display_name, status, created_at,
                           traffic_up_bytes, traffic_down_bytes, traffic_total_bytes, traffic_updated_at, traffic_source,
                           direct_config_uri, direct_config_updated_at, direct_config_note, account_origin
                       )
                       VALUES ('xui', 'cascade', ?, ?, ?, ?, ?, ?, ?, ?, 'x-ui/client_traffics', ?, ?, ?, 'legacy')""",
                    (external_key, email, status, now, up, down, total, now, direct_uri, now if direct_uri else None, "x-ui/vless-reality" if direct_uri else None)
                )
                acc_id = c.lastrowid
                imported_count += 1

            sub = conn.execute("SELECT id FROM subscriptions WHERE vpn_account_id = ?", (acc_id,)).fetchone()
            if sub:
                conn.execute(
                    "UPDATE subscriptions SET expires_at = ?, status = ? WHERE vpn_account_id = ?",
                    (expiry, "active" if status == "active" else "suspended", acc_id)
                )
            else:
                conn.execute(
                    """INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
                       VALUES (?, 'active', ?, ?, '1_month')""",
                    (acc_id, now, expiry)
                )
            get_or_create_sub_token(acc_id, conn)
            if direct_uri:
                conn.execute(
                    """UPDATE vpn_accounts
                       SET direct_config_uri = ?, direct_config_updated_at = ?, direct_config_note = ?
                       WHERE server_type = 'hysteria' AND lower(display_name) = lower(?)""",
                    (direct_uri, now, f"x-ui direct profile: {email}", email)
                )
            conn.execute(
                """INSERT INTO traffic_snapshots
                   (vpn_account_id, up_bytes, down_bytes, total_bytes, source, captured_at)
                   VALUES (?, ?, ?, ?, 'x-ui/client_traffics', ?)""",
                (acc_id, up, down, total, now)
            )

    xui_conn.close()
    conn.close()
    return imported_count


def _load_xui_direct_profiles(xui_conn):
    profiles = {}
    try:
        rows = xui_conn.execute("""
            SELECT id, port, protocol, settings, stream_settings
            FROM inbounds
            WHERE enable = 1 AND lower(protocol) = 'vless'
            ORDER BY CASE WHEN port = 443 THEN 0 ELSE 1 END, id ASC
        """).fetchall()
    except Exception:
        return profiles

    for row in rows:
        try:
            settings = json.loads(row["settings"] or "{}")
            stream = json.loads(row["stream_settings"] or "{}")
        except Exception:
            continue
        reality = stream.get("realitySettings") or {}
        reality_settings = reality.get("settings") or {}
        public_key = reality_settings.get("publicKey")
        if stream.get("security") != "reality" or not public_key:
            continue
        network = stream.get("network") or "tcp"
        fingerprint = reality_settings.get("fingerprint") or "chrome"
        spider_x = reality_settings.get("spiderX") or "/"
        server_names = reality.get("serverNames") or []
        sni = reality_settings.get("serverName") or (server_names[0] if server_names else "")
        short_ids = reality.get("shortIds") or [""]
        sid = short_ids[0] if short_ids else ""
        port = int(row["port"] or 443)
        for client in settings.get("clients") or []:
            if not client.get("enable", True):
                continue
            email = (client.get("email") or "").strip()
            uuid = (client.get("id") or "").strip()
            if not email or not uuid or email.lower() in profiles:
                continue
            query = {
                "type": network,
                "security": "reality",
                "pbk": public_key,
                "fp": fingerprint,
                "sni": sni,
                "sid": sid,
                "spx": spider_x,
            }
            flow = (client.get("flow") or "").strip()
            if flow:
                query["flow"] = flow
            profiles[email.lower()] = (
                f"vless://{uuid}@193.164.155.153:{port}?"
                f"{urllib.parse.urlencode(query, safe=':/')}"
                f"#{urllib.parse.quote(email)}"
            )
    return profiles
