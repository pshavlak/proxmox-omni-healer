import os
import sys
import json
import urllib.parse
import urllib.request
import urllib.error
import time
import secrets
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.db import get_db, ensure_column, init_db
from backend.hysteria_users import create_hysteria_user
from backend.latvia_hysteria import LatviaHysteriaError, attach_user as attach_latvia_hysteria_user

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.environ.get("WEBAPP_URL", "https://hist.yupiterpro.ru/app/")
API_TIMEOUT = int(os.environ.get("TELEGRAM_API_TIMEOUT", "35"))
ADMIN_IDS_RAW = os.environ.get("TELEGRAM_ADMIN_IDS", "617281647")
STARS_RATE = float(os.environ.get("STARS_RATE", "2.0"))  # 1 Star = 2 RUB

SERVER_HOST = "hist.yupiterpro.ru"
SERVER_PORT = 8443


def parse_admin_ids():
    ids = []
    for item in ADMIN_IDS_RAW.split(","):
        item = item.strip()
        if item.isdigit():
            ids.append(int(item))
    return ids


ADMIN_IDS = parse_admin_ids()


def telegram_api(method: str, params: dict = None) -> dict:
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print(f"[Bot Mock] Calling Telegram API {method} with params: {params}")
        return {"ok": True, "result": True}

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{method}"
    data = json.dumps(params).encode("utf-8") if params else None
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Telegram API Error ({method}): {e}", flush=True)
        return {"ok": False, "error": str(e)}


def telegram_send_photo(
    chat_id: int, caption: str, image_bytes: bytes, reply_markup: dict = None
):
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print(f"[Bot Mock] Sending photo to {chat_id} with caption: {caption}")
        return {"ok": True}

    boundary = f"----WebKitFormBoundary{secrets.token_hex(8)}"
    body = []

    def add_field(name, val):
        body.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{val}\r\n'.encode(
                "utf-8"
            )
        )

    add_field("chat_id", str(chat_id))
    add_field("caption", caption)
    add_field("parse_mode", "Markdown")
    if reply_markup:
        add_field("reply_markup", json.dumps(reply_markup))

    body.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="photo"; filename="qr.png"\r\nContent-Type: image/png\r\n\r\n'.encode(
            "utf-8"
        )
    )
    body.append(image_bytes)
    body.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    payload = b"".join(body)
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data=payload,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Telegram sendPhoto Error: {e}", flush=True)
        return {"ok": False, "error": str(e)}


def make_qr_png(payload: str):
    try:
        import qrcode
    except Exception:
        return None
    img = qrcode.make(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def get_updates(offset=None, timeout=25):
    params = {
        "timeout": timeout,
        "allowed_updates": ["message", "callback_query", "pre_checkout_query"],
    }
    if offset is not None:
        params["offset"] = offset
    return telegram_api("getUpdates", params)


def get_main_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🚀 Открыть Кабинет VPN", "web_app": {"url": WEBAPP_URL}}],
            [
                {"text": "📊 Статус", "callback_data": "cmd_status"},
                {"text": "🛒 Купить", "callback_data": "cmd_buy"},
            ],
            [
                {"text": "📱 QR-код", "callback_data": "cmd_connect"},
                {"text": "🎁 Тест 1 час", "callback_data": "cmd_trial"},
            ],
            [{"text": "❓ Помощь", "callback_data": "cmd_help"}],
        ]
    }


def is_user_allowed(telegram_id: int) -> bool:
    """Checks if a user has access: admin, whitelisted, has existing VPN link, or accepted invite."""
    if telegram_id in ADMIN_IDS:
        return True

    conn = get_db()
    user = conn.execute(
        "SELECT role, is_whitelisted FROM telegram_users WHERE telegram_id=?",
        (telegram_id,),
    ).fetchone()
    if user and (user["role"] == "admin" or user["is_whitelisted"] == 1):
        conn.close()
        return True

    has_link = conn.execute(
        "SELECT 1 FROM account_links WHERE telegram_user_id=? LIMIT 1",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return bool(has_link)


def try_attach_latvia_hysteria(username: str, auth_secret: str):
    try:
        return attach_latvia_hysteria_user(username, auth_secret)["uri"]
    except LatviaHysteriaError as e:
        print(f"Latvia Hysteria attach skipped/failed for {username}: {e}", flush=True)
    except Exception as e:
        print(f"Latvia Hysteria attach unexpected error for {username}: {type(e).__name__}", flush=True)
    return None


def check_and_use_invite(telegram_id: int, invite_token: str) -> bool:
    """Validates and claims an invite token for a user."""
    conn = get_db()
    now = int(time.time())
    token_row = conn.execute(
        "SELECT * FROM invite_tokens WHERE token=? AND is_active=1", (invite_token,)
    ).fetchone()

    if not token_row:
        conn.close()
        return False

    if (
        token_row["max_uses"] > 0
        and token_row["uses_count"] >= token_row["max_uses"]
    ):
        conn.close()
        return False

    new_count = token_row["uses_count"] + 1
    is_active = 0 if (token_row["max_uses"] > 0 and new_count >= token_row["max_uses"]) else 1

    conn.execute(
        """
        UPDATE invite_tokens
        SET uses_count=?, used_by=?, used_at=?, is_active=?
        WHERE token=?
    """,
        (new_count, telegram_id, now, is_active, invite_token),
    )

    conn.execute(
        """
        UPDATE telegram_users
        SET is_whitelisted=1
        WHERE telegram_id=?
    """,
        (telegram_id,),
    )

    conn.commit()
    conn.close()
    return True


def get_user_linked_account(telegram_id: int):
    conn = get_db()
    row = conn.execute(
        """
        SELECT v.id, v.display_name, v.external_key, v.server_type, s.expires_at, s.status as sub_status
        FROM account_links al
        JOIN vpn_accounts v ON al.vpn_account_id = v.id
        LEFT JOIN subscriptions s ON v.id = s.vpn_account_id
        WHERE al.telegram_user_id = ? AND (v.deleted_at IS NULL)
        ORDER BY s.expires_at DESC
        LIMIT 1
    """,
        (telegram_id,),
    ).fetchone()
    conn.close()
    return row


def handle_start_command(
    chat_id: int, user_data: dict, deep_link_payload: str = None
):
    conn = get_db()
    now = int(time.time())

    ensure_column(conn, "telegram_users", "trial_used", "INTEGER DEFAULT 0")
    ensure_column(conn, "telegram_users", "is_whitelisted", "INTEGER DEFAULT 0")

    conn.execute(
        """
        INSERT INTO telegram_users (telegram_id, username, first_name, role, created_at, last_seen_at)
        VALUES (?, ?, ?, 'user', ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            last_seen_at = excluded.last_seen_at
    """,
        (
            chat_id,
            user_data.get("username", ""),
            user_data.get("first_name", "User"),
            now,
            now,
        ),
    )
    conn.commit()
    conn.close()

    # Handle claim code
    claim_msg = ""
    if deep_link_payload and deep_link_payload.startswith("claim_"):
        token = deep_link_payload[len("claim_") :].strip()
        conn = get_db()
        row = conn.execute(
            """
            SELECT st.vpn_account_id, va.display_name
            FROM subscription_tokens st
            JOIN vpn_accounts va ON st.vpn_account_id = va.id
            WHERE st.token = ?
        """,
            (token,),
        ).fetchone()

        if row:
            conn.execute(
                """
                INSERT OR REPLACE INTO account_links (telegram_user_id, vpn_account_id, linked_at, link_method)
                VALUES (?, ?, ?, 'claim_code')
            """,
                (chat_id, row["vpn_account_id"], now),
            )
            conn.execute(
                "UPDATE telegram_users SET is_whitelisted=1 WHERE telegram_id=?",
                (chat_id,),
            )
            conn.commit()
            claim_msg = f"✅ Ваш аккаунт **{row['display_name']}** успешно привязан!\n\n"
        else:
            claim_msg = "⚠️ Код привязки недействителен или устарел.\n\n"
        conn.close()

    # Handle invite token
    if deep_link_payload and deep_link_payload.startswith("inv_"):
        inv_code = deep_link_payload[len("inv_") :].strip()
        if check_and_use_invite(chat_id, inv_code):
            claim_msg = "🎉 **Приглашение успешно активировано!** Добро пожаловать.\n\n"
        else:
            claim_msg = "⚠️ Ссылка-приглашение недействительна или уже была использована.\n\n"

    # Check if user has access
    if not is_user_allowed(chat_id):
        text = (
            "🔒 **Доступ ограничен**\n\n"
            "Этот VPN-сервис является приватным и работает только по персональным приглашениям.\n\n"
            "Если у вас есть ссылка-приглашение, перейдите по ней для активации доступа."
        )
        return telegram_api(
            "sendMessage",
            {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        )

    text = (
        f"👋 Здравствуйте, {user_data.get('first_name', 'пользователь')}!\n\n"
        f"{claim_msg}"
        f"Добро пожаловать в **Cascade VPN**.\n\n"
        f"Управляйте VPN через меню ниже или открывайте полноценный клиентский кабинет."
    )

    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_create_invite(admin_id: int):
    """Admin command to generate invite link."""
    if admin_id not in ADMIN_IDS:
        return

    token = secrets.token_urlsafe(12)
    now = int(time.time())

    conn = get_db()
    conn.execute(
        """
        INSERT INTO invite_tokens (token, created_by, created_at, max_uses, uses_count, is_active)
        VALUES (?, ?, ?, 1, 0, 1)
    """,
        (token, admin_id, now),
    )
    conn.commit()
    conn.close()

    bot_info = telegram_api("getMe")
    bot_username = (
        bot_info.get("result", {}).get("username") or "YourVPNBot"
    )
    invite_url = f"https://t.me/{bot_username}?start=inv_{token}"

    text = (
        f"🎟 **Создано одноразовое приглашение:**\n\n"
        f"`{invite_url}`\n\n"
        f"Отправьте эту ссылку пользователю. После перехода бот откроет ему доступ."
    )
    return telegram_api(
        "sendMessage",
        {"chat_id": admin_id, "text": text, "parse_mode": "Markdown"},
    )


def handle_status_command(chat_id: int):
    if not is_user_allowed(chat_id):
        return

    acc = get_user_linked_account(chat_id)
    if not acc:
        text = "ℹ️ У вас пока нет привязанного VPN-аккаунта.\n\nНажмите *🎁 Тест 1 час* или *🛒 Купить*, чтобы получить доступ!"
    else:
        now = int(time.time())
        exp = acc["expires_at"] or 0
        if exp > now:
            days_left = round((exp - now) / 86400, 1)
            status_str = f"🟢 Активна (осталось {days_left} дн.)"
        else:
            status_str = "🔴 Истекла"

        text = (
            f"📊 **Статус вашего VPN:**\n\n"
            f"👤 Аккаунт: `{acc['display_name']}`\n"
            f"🛡 Протокол: {acc['server_type'].upper()}\n"
            f"📅 Подписка: {status_str}\n"
        )

    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_buy_command(chat_id: int):
    if not is_user_allowed(chat_id):
        return

    conn = get_db()
    plans = conn.execute(
        "SELECT code, title, duration_days, price FROM plans WHERE is_active=1"
    ).fetchall()
    conn.close()

    keyboard = {"inline_keyboard": []}
    for p in plans:
        stars = max(1, int(p["price"] / STARS_RATE))
        keyboard["inline_keyboard"].append(
            [
                {
                    "text": f"⭐ {p['title']} — {stars} Stars ({p['price']} ₽)",
                    "callback_data": f"buy_{p['code']}",
                }
            ]
        )
    keyboard["inline_keyboard"].append(
        [{"text": "🔙 В главное меню", "callback_data": "main_menu"}]
    )

    text = "🛒 **Выберите тарифный план для оплаты Telegram Stars:**\n\nОплата происходит мгновенно прямо в Telegram."
    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": keyboard,
        },
    )


def handle_connect_command(chat_id: int):
    if not is_user_allowed(chat_id):
        return

    acc = get_user_linked_account(chat_id)
    if not acc:
        return telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "❌ У вас нет активного VPN-аккаунта. Воспользуйтесь кнопкой *🎁 Тест 1 час* или *🛒 Купить*.",
                "parse_mode": "Markdown",
                "reply_markup": get_main_keyboard(),
            },
        )

    link = f"hysteria2://{acc['external_key']}@{SERVER_HOST}:{SERVER_PORT}?sni={SERVER_HOST}#{acc['display_name']}"

    caption = (
        f"📱 **Ссылка подключения:**\n\n"
        f"`{link}`\n\n"
        f"Отсканируйте QR-код в приложении v2rayNG, Streisand, Happ или Hysteria2."
    )
    qr_bytes = make_qr_png(link)
    if qr_bytes:
        return telegram_send_photo(
            chat_id, caption, qr_bytes, reply_markup=get_main_keyboard()
        )
    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": caption,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_trial_command(chat_id: int, user_data: dict):
    if not is_user_allowed(chat_id):
        return

    conn = get_db()
    ensure_column(conn, "telegram_users", "trial_used", "INTEGER DEFAULT 0")

    row = conn.execute(
        "SELECT trial_used FROM telegram_users WHERE telegram_id=?", (chat_id,)
    ).fetchone()
    if row and row["trial_used"]:
        conn.close()
        return telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "⚠️ Вы уже использовали бесплатный тестовый период.",
                "parse_mode": "Markdown",
                "reply_markup": get_main_keyboard(),
            },
        )

    now = int(time.time())
    username = f"tg_{chat_id}_trial"

    try:
        hys = create_hysteria_user(username)
        auth_secret = hys["auth_secret"]
    except Exception:
        auth_secret = secrets.token_urlsafe(16)
    direct_hysteria_uri = try_attach_latvia_hysteria(username, auth_secret)

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO vpn_accounts
          (server_type, server_name, external_key, display_name, status, created_at,
           account_origin, direct_hysteria_config_uri)
        VALUES ('hysteria', 'Main Hysteria', ?, ?, 'active', ?, 'bot_trial', ?)
    """,
        (auth_secret, f"Test-{user_data.get('first_name','User')}", now, direct_hysteria_uri),
    )
    vpn_id = cursor.lastrowid

    expires_at = now + 3600  # 1 hour test without limits
    cursor.execute(
        """
        INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
        VALUES (?, 'active', ?, ?, 'trial_1h')
    """,
        (vpn_id, now, expires_at),
    )

    cursor.execute(
        """
        INSERT OR REPLACE INTO account_links (telegram_user_id, vpn_account_id, linked_at, link_method)
        VALUES (?, ?, ?, 'trial')
    """,
        (chat_id, vpn_id, now),
    )

    cursor.execute(
        "UPDATE telegram_users SET trial_used=1 WHERE telegram_id=?", (chat_id,)
    )
    conn.commit()
    conn.close()

    link = f"hysteria2://{auth_secret}@{SERVER_HOST}:{SERVER_PORT}?sni={SERVER_HOST}#Test-{user_data.get('first_name','User')}"

    caption = (
        f"🎁 **Тестовый доступ на 1 час активирован!**\n\n"
        f"Ссылка:\n`{link}`\n\n"
        f"Без ограничений по трафику и скорости."
    )
    qr_bytes = make_qr_png(link)
    if qr_bytes:
        return telegram_send_photo(
            chat_id, caption, qr_bytes, reply_markup=get_main_keyboard()
        )
    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": caption,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_help_command(chat_id: int):
    if not is_user_allowed(chat_id):
        return

    text = (
        "❓ **Частые вопросы (FAQ):**\n\n"
        "**1. Какие приложения использовать?**\n"
        "• iOS: Streisand, Happ, Shadowrocket\n"
        "• Android: v2rayNG, NekoBox\n"
        "• Windows / Mac: Hysteria2 GUI Client, v2rayN\n\n"
        "**2. Какая скорость и лимиты?**\n"
        "Без ограничений по трафику и скорости.\n\n"
        "**3. Нужна помощь?**\n"
        "Обратитесь к администратору."
    )
    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_stars_invoice(chat_id: int, plan_code: str):
    conn = get_db()
    plan = conn.execute(
        "SELECT code, title, duration_days, price FROM plans WHERE code=?",
        (plan_code,),
    ).fetchone()
    conn.close()

    if not plan:
        return telegram_api(
            "sendMessage", {"chat_id": chat_id, "text": "❌ Тариф не найден."}
        )

    stars_amount = max(1, int(plan["price"] / STARS_RATE))
    payload = json.dumps({"plan": plan_code, "user_id": chat_id})

    return telegram_api(
        "sendInvoice",
        {
            "chat_id": chat_id,
            "title": f"VPN: {plan['title']}",
            "description": f"Подписка Cascade VPN на {plan['duration_days']} дней",
            "payload": payload,
            "currency": "XTR",
            "prices": [{"label": plan["title"], "amount": stars_amount}],
        },
    )


def handle_pre_checkout(pre_checkout_query: dict):
    query_id = pre_checkout_query.get("id")
    return telegram_api(
        "answerPreCheckoutQuery",
        {"pre_checkout_query_id": query_id, "ok": True},
    )


def handle_successful_payment(message: dict):
    chat_id = message["chat"]["id"]
    payment = message["successful_payment"]
    payload_raw = payment.get("invoice_payload", "{}")

    try:
        payload = json.loads(payload_raw)
        plan_code = payload.get("plan")
    except Exception:
        plan_code = "1_month"

    conn = get_db()
    plan = conn.execute(
        "SELECT code, title, duration_days, price FROM plans WHERE code=?",
        (plan_code,),
    ).fetchone()
    if not plan:
        conn.close()
        return

    now = int(time.time())
    days = plan["duration_days"]

    acc = get_user_linked_account(chat_id)
    if acc:
        vpn_id = acc["id"]
        exp = acc["expires_at"] or now
        new_exp = max(now, exp) + (days * 86400)
        conn.execute(
            "UPDATE subscriptions SET expires_at=?, status='active' WHERE vpn_account_id=?",
            (new_exp, vpn_id),
        )
        conn.execute(
            "UPDATE vpn_accounts SET status='active' WHERE id=?", (vpn_id,)
        )
    else:
        username = f"tg_{chat_id}_{secrets.token_hex(4)}"
        try:
            hys = create_hysteria_user(username)
            auth_secret = hys["auth_secret"]
        except Exception:
            auth_secret = secrets.token_urlsafe(16)
        direct_hysteria_uri = try_attach_latvia_hysteria(username, auth_secret)

        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO vpn_accounts
              (server_type, server_name, external_key, display_name, status, created_at,
               account_origin, direct_hysteria_config_uri)
            VALUES ('hysteria', 'Main Hysteria', ?, ?, 'active', ?, 'stars_purchase', ?)
        """,
            (auth_secret, f"User-{chat_id}", now, direct_hysteria_uri),
        )
        vpn_id = cursor.lastrowid

        new_exp = now + (days * 86400)
        cursor.execute(
            """
            INSERT INTO subscriptions (vpn_account_id, status, starts_at, expires_at, plan_id)
            VALUES (?, 'active', ?, ?, ?)
        """,
            (vpn_id, now, new_exp, plan_code),
        )

        cursor.execute(
            """
            INSERT OR REPLACE INTO account_links (telegram_user_id, vpn_account_id, linked_at, link_method)
            VALUES (?, ?, ?, 'stars_purchase')
        """,
            (chat_id, vpn_id, now),
        )

    conn.execute(
        """
        INSERT INTO transactions (telegram_user_id, type, amount, description, created_at)
        VALUES (?, 'stars_payment', ?, ?, ?)
    """,
        (chat_id, plan["price"], f"Stars payment for {plan['title']}", now),
    )

    conn.execute(
        """
        INSERT INTO audit_log (actor, action, target, result, timestamp, metadata)
        VALUES (?, 'stars_payment', ?, 'ok', ?, ?)
    """,
        (
            str(chat_id),
            str(vpn_id),
            now,
            json.dumps(
                {
                    "plan": plan_code,
                    "amount_stars": payment.get("total_amount"),
                }
            ),
        ),
    )

    conn.commit()
    conn.close()

    text = f"🎉 **Оплата прошла успешно!**\n\nПодписка по тарифу *{plan['title']}* продлена до <t:{new_exp}:D>."
    return telegram_api(
        "sendMessage",
        {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "reply_markup": get_main_keyboard(),
        },
    )


def handle_callback_query(cb: dict):
    cb_id = cb.get("id")
    data = cb.get("data", "")
    message = cb.get("message") or {}
    chat_id = message.get("chat", {}).get("id")

    telegram_api("answerCallbackQuery", {"callback_query_id": cb_id})

    if not chat_id:
        return

    if data == "cmd_status":
        handle_status_command(chat_id)
    elif data == "cmd_buy":
        handle_buy_command(chat_id)
    elif data == "cmd_connect":
        handle_connect_command(chat_id)
    elif data == "cmd_trial":
        handle_trial_command(chat_id, cb.get("from", {}))
    elif data == "cmd_help":
        handle_help_command(chat_id)
    elif data == "main_menu":
        telegram_api(
            "sendMessage",
            {
                "chat_id": chat_id,
                "text": "Главное меню:",
                "reply_markup": get_main_keyboard(),
            },
        )
    elif data.startswith("buy_"):
        plan_code = data[len("buy_") :]
        handle_stars_invoice(chat_id, plan_code)
    elif data.startswith("receipt_approve_") or data.startswith("receipt_reject_"):
        handle_admin_receipt_callback(chat_id, data)


def handle_admin_receipt_callback(admin_id: int, data: str):
    if admin_id not in ADMIN_IDS:
        return

    is_approve = data.startswith("receipt_approve_")
    receipt_id = int(data.split("_")[-1])

    conn = get_db()
    receipt = conn.execute(
        "SELECT * FROM manual_receipts WHERE id=?", (receipt_id,)
    ).fetchone()
    if not receipt or receipt["status"] != "pending":
        conn.close()
        return telegram_api(
            "sendMessage",
            {"chat_id": admin_id, "text": f"Чек #{receipt_id} уже обработан."},
        )

    now = int(time.time())
    new_status = "approved" if is_approve else "rejected"
    conn.execute(
        "UPDATE manual_receipts SET status=?, processed_at=? WHERE id=?",
        (new_status, now, receipt_id),
    )

    user_id = receipt["telegram_user_id"]
    if is_approve:
        acc = get_user_linked_account(user_id)
        if acc:
            vpn_id = acc["id"]
            exp = acc["expires_at"] or now
            new_exp = max(now, exp) + (30 * 86400)
            conn.execute(
                "UPDATE subscriptions SET expires_at=?, status='active' WHERE vpn_account_id=?",
                (new_exp, vpn_id),
            )
            conn.execute(
                "UPDATE vpn_accounts SET status='active' WHERE id=?", (vpn_id,)
            )
        telegram_api(
            "sendMessage",
            {
                "chat_id": user_id,
                "text": "✅ Ваш платёж подтверждён! Подписка продлена на 30 дней.",
            },
        )
    else:
        telegram_api(
            "sendMessage",
            {
                "chat_id": user_id,
                "text": "❌ Ваш чек по оплате был отклонён администратором.",
            },
        )

    conn.commit()
    conn.close()

    return telegram_api(
        "sendMessage",
        {
            "chat_id": admin_id,
            "text": f"Чек #{receipt_id} статус изменён на: *{new_status}*",
            "parse_mode": "Markdown",
        },
    )


def handle_update(update):
    if "pre_checkout_query" in update:
        handle_pre_checkout(update["pre_checkout_query"])
        return True

    if "callback_query" in update:
        handle_callback_query(update["callback_query"])
        return True

    message = update.get("message") or {}

    if "successful_payment" in message:
        handle_successful_payment(message)
        return True

    text = (message.get("text") or "").strip()
    chat = message.get("chat") or {}
    user = message.get("from") or {}
    chat_id = chat.get("id")
    if not chat_id:
        return False

    payload = parse_start_payload(text)
    if payload is not None or text.startswith("/start"):
        handle_start_command(chat_id, user, payload or "")
        return True

    if text in ("/invite", "/genlink", "/token"):
        handle_create_invite(chat_id)
        return True

    if text == "/status":
        handle_status_command(chat_id)
        return True
    elif text == "/buy":
        handle_buy_command(chat_id)
        return True
    elif text == "/connect":
        handle_connect_command(chat_id)
        return True
    elif text == "/trial":
        handle_trial_command(chat_id, user)
        return True
    elif text == "/help":
        handle_help_command(chat_id)
        return True
    elif text:
        handle_start_command(chat_id, user, "")
        return True

    return False


def parse_start_payload(text):
    if not text:
        return None
    parts = text.strip().split(maxsplit=1)
    if not parts or parts[0].split("@", 1)[0] != "/start":
        return None
    return parts[1].strip() if len(parts) > 1 else ""


def run_polling():
    if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not configured")

    init_db()
    telegram_api("deleteWebhook", {"drop_pending_updates": False})
    print(
        f"Telegram private bot polling started; webapp={WEBAPP_URL}", flush=True
    )
    offset = None

    while True:
        result = get_updates(offset=offset)
        if not result.get("ok"):
            print("Telegram polling error; retrying", flush=True)
            time.sleep(5)
            continue

        for update in result.get("result", []):
            update_id = update.get("update_id")
            if update_id is not None:
                offset = update_id + 1
            try:
                handled = handle_update(update)
                if handled and update_id is not None:
                    print(f"Handled update_id={update_id}", flush=True)
            except Exception as e:
                print(
                    f"Update handling error: {type(e).__name__}: {e}", flush=True
                )


if __name__ == "__main__":
    run_polling()
