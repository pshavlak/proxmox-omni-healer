#!/usr/bin/env python3
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db, init_db
from backend.hysteria_users import HysteriaUsersError, delete_hysteria_user
from backend.latvia_hysteria import LatviaHysteriaError, delete_user as delete_latvia_hysteria_user
from backend.xui_api import XUIAPIError, XUIConfigError, XUIClient


def expired_promocode_accounts(now):
    conn = get_db()
    rows = conn.execute("""
        SELECT va.id, va.display_name, va.created_by_promocode, va.auto_delete_at,
               va.direct_tcp_config_uri, va.direct_xhttp_config_uri,
               va.direct_hysteria_config_uri, s.expires_at
        FROM vpn_accounts va
        LEFT JOIN subscriptions s ON va.id = s.vpn_account_id
        WHERE va.account_origin = 'miniapp'
          AND va.created_by_promocode IS NOT NULL
          AND va.created_by_promocode != ''
          AND va.auto_delete_at IS NOT NULL
          AND va.auto_delete_at <= ?
          AND va.status != 'deleted'
    """, (now,)).fetchall()
    conn.close()
    return rows


def mark_deleted(account_id, result, metadata):
    now = int(time.time())
    conn = get_db()
    with conn:
        conn.execute(
            """UPDATE vpn_accounts
               SET status = 'deleted', deleted_at = ?
               WHERE id = ?""",
            (now, account_id),
        )
        conn.execute(
            """UPDATE subscriptions
               SET status = 'expired'
               WHERE vpn_account_id = ?""",
            (account_id,),
        )
        conn.execute(
            """UPDATE subscription_tokens
               SET revoked_at = ?
               WHERE vpn_account_id = ? AND revoked_at IS NULL""",
            (now, account_id),
        )
        conn.execute("DELETE FROM account_links WHERE vpn_account_id = ?", (account_id,))
        conn.execute(
            """INSERT INTO audit_log
               (actor, action, target, result, timestamp, metadata)
               VALUES ('system', 'promocode_key_cleanup', ?, ?, ?, ?)""",
            (str(account_id), result, now, json.dumps(metadata, ensure_ascii=False)),
        )
    conn.close()


def record_failure(account_id, metadata):
    now = int(time.time())
    conn = get_db()
    with conn:
        conn.execute(
            """INSERT INTO audit_log
               (actor, action, target, result, timestamp, metadata)
               VALUES ('system', 'promocode_key_cleanup', ?, 'failed', ?, ?)""",
            (str(account_id), now, json.dumps(metadata, ensure_ascii=False)),
        )
    conn.close()


def cleanup_account(row, xui):
    account_id = row["id"]
    name = row["display_name"]
    metadata = {
        "display_name": name,
        "code": row["created_by_promocode"],
        "auto_delete_at": row["auto_delete_at"],
        "hysteria_deleted": False,
        "latvia_hysteria_deleted": False,
        "xui_tcp_deleted": False,
        "xui_xhttp_deleted": False,
    }

    if not xui:
        metadata["xui_error"] = "xui_api_not_available"
        record_failure(account_id, metadata)
        return "failed", metadata

    for transport, key in (("tcp", "xui_tcp_deleted"), ("xhttp", "xui_xhttp_deleted")):
        try:
            result = xui.delete_direct_client(name, transport=transport)
            metadata[key] = bool(result.get("deleted"))
        except (XUIAPIError, XUIConfigError) as e:
            metadata[f"{transport}_error"] = str(e)

    if metadata.get("tcp_error") or metadata.get("xhttp_error"):
        record_failure(account_id, metadata)
        return "failed", metadata

    try:
        metadata["hysteria_deleted"] = bool(delete_hysteria_user(name))
    except HysteriaUsersError as e:
        metadata["hysteria_error"] = str(e)
        record_failure(account_id, metadata)
        return "failed", metadata

    try:
        metadata["latvia_hysteria_deleted"] = bool(delete_latvia_hysteria_user(name).get("changed"))
    except LatviaHysteriaError as e:
        metadata["latvia_hysteria_error"] = str(e)
        record_failure(account_id, metadata)
        return "failed", metadata

    mark_deleted(account_id, "ok", metadata)
    return "ok", metadata


def main():
    init_db()
    now = int(time.time())
    rows = expired_promocode_accounts(now)
    if not rows:
        print(json.dumps({"ok": True, "deleted": 0}, ensure_ascii=False))
        return 0

    try:
        xui = XUIClient()
    except (XUIConfigError, XUIAPIError) as e:
        xui = None

    results = []
    for row in rows:
        result, metadata = cleanup_account(row, xui)
        results.append({"account_id": row["id"], "result": result, "metadata": metadata})

    print(json.dumps({"ok": True, "deleted": len(results), "results": results}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
