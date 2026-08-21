import sqlite3
import os
import secrets
import time

DB_PATH = os.environ.get("MINIAPP_DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))

def get_db():
    db_path = os.environ.get("MINIAPP_DB_PATH", os.path.join(os.path.dirname(__file__), "app.db"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_column(conn, table, column, definition):
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})").fetchall()
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

def init_db():
    conn = get_db()
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS telegram_users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            role TEXT DEFAULT 'user',
            created_at INTEGER,
            last_seen_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS vpn_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            server_type TEXT NOT NULL, -- 'hysteria' or 'xui'
            server_name TEXT NOT NULL,
            external_key TEXT NOT NULL, -- auth_str or email/uuid
            display_name TEXT,
            status TEXT DEFAULT 'active', -- 'active', 'disabled'
            created_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS account_links (
            telegram_user_id INTEGER NOT NULL,
            vpn_account_id INTEGER NOT NULL,
            linked_at INTEGER,
            link_method TEXT, -- 'auto_import', 'claim_code', 'admin'
            PRIMARY KEY (telegram_user_id, vpn_account_id),
            FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(telegram_id),
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vpn_account_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active', -- 'active', 'expired', 'suspended'
            starts_at INTEGER,
            expires_at INTEGER,
            plan_id TEXT,
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS subscription_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vpn_account_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            created_at INTEGER,
            revoked_at INTEGER,
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS plans (
            code TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            price REAL NOT NULL,
            currency TEXT DEFAULT 'RUB',
            is_active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            result TEXT,
            timestamp INTEGER,
            metadata TEXT
        );

        CREATE TABLE IF NOT EXISTS wallets (
            telegram_user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0,
            currency TEXT DEFAULT 'RUB',
            FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(telegram_id)
        );

        CREATE TABLE IF NOT EXISTS promocodes (
            code TEXT PRIMARY KEY,
            bonus_days INTEGER DEFAULT 0,
            discount_percent INTEGER DEFAULT 0,
            max_activations INTEGER DEFAULT 100,
            activations_count INTEGER DEFAULT 0,
            expires_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS manual_receipts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'RUB',
            receipt_note TEXT,
            status TEXT DEFAULT 'pending',
            created_at INTEGER,
            processed_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS payment_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            manual_enabled INTEGER DEFAULT 0,
            card_number TEXT,
            bank_name TEXT,
            recipient_name TEXT,
            sbp_phone TEXT,
            payment_comment TEXT,
            user_instructions TEXT,
            updated_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            created_at INTEGER
        );

        CREATE TABLE IF NOT EXISTS connection_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vpn_account_id INTEGER,
            source TEXT NOT NULL,
            event_type TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT,
            created_at INTEGER,
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS traffic_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vpn_account_id INTEGER NOT NULL,
            up_bytes INTEGER DEFAULT 0,
            down_bytes INTEGER DEFAULT 0,
            total_bytes INTEGER DEFAULT 0,
            source TEXT NOT NULL,
            captured_at INTEGER,
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id)
        );

        CREATE TABLE IF NOT EXISTS subscription_devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vpn_account_id INTEGER NOT NULL,
            device_key TEXT NOT NULL,
            hwid TEXT,
            device_model TEXT,
            platform TEXT,
            client_name TEXT,
            client_version TEXT,
            user_agent TEXT,
            ip TEXT,
            first_seen_at INTEGER,
            last_seen_at INTEGER,
            hits INTEGER DEFAULT 1,
            is_reset INTEGER DEFAULT 0,
            source TEXT DEFAULT 'subscription_headers',
            FOREIGN KEY (vpn_account_id) REFERENCES vpn_accounts(id),
            UNIQUE(vpn_account_id, device_key)
        );

        CREATE TABLE IF NOT EXISTS invite_tokens (
            token TEXT PRIMARY KEY,
            created_by INTEGER NOT NULL,
            created_at INTEGER NOT NULL,
            used_by INTEGER,
            used_at INTEGER,
            max_uses INTEGER DEFAULT 1,
            uses_count INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            note TEXT
        );
        """)

        ensure_column(conn, "telegram_users", "trial_used", "INTEGER DEFAULT 0")
        ensure_column(conn, "telegram_users", "is_whitelisted", "INTEGER DEFAULT 0")

        ensure_column(conn, "vpn_accounts", "traffic_up_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "vpn_accounts", "traffic_down_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "vpn_accounts", "traffic_total_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "vpn_accounts", "traffic_updated_at", "INTEGER")
        ensure_column(conn, "vpn_accounts", "traffic_source", "TEXT")
        ensure_column(conn, "vpn_accounts", "online_devices", "INTEGER DEFAULT 0")
        ensure_column(conn, "vpn_accounts", "routing_mode", "TEXT DEFAULT 'cascade'")
        ensure_column(conn, "vpn_accounts", "direct_config_uri", "TEXT")
        ensure_column(conn, "vpn_accounts", "direct_config_updated_at", "INTEGER")
        ensure_column(conn, "vpn_accounts", "direct_config_note", "TEXT")
        ensure_column(conn, "vpn_accounts", "direct_tcp_config_uri", "TEXT")
        ensure_column(conn, "vpn_accounts", "direct_xhttp_config_uri", "TEXT")
        ensure_column(conn, "vpn_accounts", "direct_hysteria_config_uri", "TEXT")
        ensure_column(conn, "vpn_accounts", "account_origin", "TEXT DEFAULT 'legacy'")
        ensure_column(conn, "vpn_accounts", "created_by_promocode", "TEXT")
        ensure_column(conn, "vpn_accounts", "auto_delete_at", "INTEGER")
        ensure_column(conn, "vpn_accounts", "deleted_at", "INTEGER")
        ensure_column(conn, "promocodes", "issue_key_on_activation", "INTEGER DEFAULT 0")
        ensure_column(conn, "manual_receipts", "currency", "TEXT DEFAULT 'RUB'")
        ensure_column(conn, "subscriptions", "traffic_limit_bytes", "INTEGER DEFAULT 0")
        ensure_column(conn, "subscriptions", "last_expiry_notified_at", "INTEGER")

        conn.execute("""
            INSERT OR IGNORE INTO payment_settings
              (id, manual_enabled, card_number, bank_name, recipient_name, sbp_phone,
               payment_comment, user_instructions, updated_at)
            VALUES (1, 0, '', '', '', '', '', '', ?)
        """, (int(time.time()),))

        conn.execute("""
            UPDATE vpn_accounts
            SET account_origin = 'legacy'
            WHERE account_origin IS NULL OR account_origin = ''
        """)
        conn.execute("""
            UPDATE vpn_accounts
            SET account_origin = 'miniapp'
            WHERE id IN (
                SELECT CAST(target AS INTEGER)
                FROM audit_log
                WHERE action IN ('hysteria_create', 'xui_direct_attach')
                  AND result = 'ok'
                  AND target GLOB '[0-9]*'
            )
        """)

        # Insert default plans if empty
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM plans")
        if cursor.fetchone()[0] == 0:
            conn.executemany("""
                INSERT INTO plans (code, title, duration_days, price, currency)
                VALUES (?, ?, ?, ?, ?)
            """, [
                ("1_month", "1 Месяц Premium", 30, 300, "RUB"),
                ("3_months", "3 Месяца Premium", 90, 800, "RUB"),
                ("1_year", "1 Год Premium", 365, 2500, "RUB")
            ])

        cursor.execute("SELECT COUNT(*) FROM promocodes")
        if cursor.fetchone()[0] == 0:
            conn.execute("""
                INSERT INTO promocodes (code, bonus_days, discount_percent, max_activations, expires_at)
                VALUES ('START2026', 7, 10, 1000, 1800000000)
            """)
    conn.close()

def get_or_create_sub_token(vpn_account_id: int, conn=None) -> str:
    close_conn = False
    if conn is None:
        conn = get_db()
        close_conn = True

    row = conn.execute(
        "SELECT token FROM subscription_tokens WHERE vpn_account_id = ? AND revoked_at IS NULL",
        (vpn_account_id,)
    ).fetchone()
    if row:
        token = row["token"]
        if close_conn:
            conn.close()
        return token
    
    token = secrets.token_urlsafe(16)
    conn.execute(
        "INSERT INTO subscription_tokens (vpn_account_id, token, created_at) VALUES (?, ?, ?)",
        (vpn_account_id, token, int(time.time()))
    )
    if close_conn:
        conn.commit()
        conn.close()
    return token

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")
