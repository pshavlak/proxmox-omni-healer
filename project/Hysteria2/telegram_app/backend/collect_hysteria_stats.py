import json
import os
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db, init_db

STATS_URL = os.environ.get("HYSTERIA_STATS_URL", "http://127.0.0.1:9999")
STATS_SECRET = os.environ.get("HYSTERIA_STATS_SECRET", "")


def fetch_json(path):
    req = urllib.request.Request(STATS_URL.rstrip("/") + path)
    if STATS_SECRET:
        req.add_header("Authorization", STATS_SECRET)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def collect():
    init_db()
    traffic = fetch_json("/traffic")
    online = fetch_json("/online")
    now = int(time.time())

    conn = get_db()
    updated = 0
    with conn:
        for username, counters in traffic.items():
            row = conn.execute(
                "SELECT id FROM vpn_accounts WHERE server_type = 'hysteria' AND display_name = ?",
                (username,),
            ).fetchone()
            if not row:
                continue
            account_id = row["id"]
            up = int(counters.get("tx") or 0)
            down = int(counters.get("rx") or 0)
            devices = int(online.get(username) or 0)
            conn.execute(
                """UPDATE vpn_accounts
                   SET traffic_up_bytes = ?, traffic_down_bytes = ?, traffic_total_bytes = 0,
                       traffic_updated_at = ?, traffic_source = 'hysteria/trafficStats',
                       online_devices = ?
                   WHERE id = ?""",
                (up, down, now, devices, account_id),
            )
            conn.execute(
                """INSERT INTO traffic_snapshots
                   (vpn_account_id, up_bytes, down_bytes, total_bytes, source, captured_at)
                   VALUES (?, ?, ?, 0, 'hysteria/trafficStats', ?)""",
                (account_id, up, down, now),
            )
            updated += 1

        # Users can be online before they produce traffic.
        for username, devices in online.items():
            row = conn.execute(
                "SELECT id FROM vpn_accounts WHERE server_type = 'hysteria' AND display_name = ?",
                (username,),
            ).fetchone()
            if row:
                conn.execute(
                    "UPDATE vpn_accounts SET online_devices = ?, traffic_updated_at = ? WHERE id = ?",
                (int(devices or 0), now, row["id"]),
                )
        pending_rows = conn.execute(
            """SELECT id
               FROM vpn_accounts
               WHERE server_type = 'hysteria'
                 AND account_origin = 'miniapp'
                 AND (traffic_source IS NULL OR traffic_source = '')
                 AND display_name NOT IN ({})""".format(",".join("?" for _ in traffic.keys()) or "''"),
            tuple(traffic.keys()),
        ).fetchall()
        for row in pending_rows:
            conn.execute(
                """UPDATE vpn_accounts
                   SET traffic_source = 'hysteria/trafficStats/pending',
                       traffic_up_bytes = COALESCE(traffic_up_bytes, 0),
                       traffic_down_bytes = COALESCE(traffic_down_bytes, 0),
                       traffic_total_bytes = COALESCE(traffic_total_bytes, 0),
                       traffic_updated_at = ?,
                       online_devices = COALESCE(online_devices, 0)
                   WHERE id = ?""",
                (now, row["id"]),
            )
            exists = conn.execute(
                "SELECT id FROM traffic_snapshots WHERE vpn_account_id = ? LIMIT 1",
                (row["id"],),
            ).fetchone()
            if not exists:
                conn.execute(
                    """INSERT INTO traffic_snapshots
                       (vpn_account_id, up_bytes, down_bytes, total_bytes, source, captured_at)
                       VALUES (?, 0, 0, 0, 'hysteria/trafficStats/pending', ?)""",
                    (row["id"], now),
                )
    conn.close()
    print(f"Collected hysteria_users={updated} online_users={len(online)} pending_users={len(pending_rows)}")


if __name__ == "__main__":
    collect()
