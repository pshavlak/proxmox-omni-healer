"""
База данных SQLite для сайта села Золотаревка.
"""
import sqlite3
import json
import os
from datetime import datetime
from config import DATABASE_PATH


def migrate_db():
    """Миграции для существующих БД (Фаза 2)."""
    conn = get_db()
    cur = conn.cursor()
    
    # blocks_history
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocks_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id    TEXT,
            config_snapshot TEXT NOT NULL,
            user_id     INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # captcha_config
    cur.execute("""
        CREATE TABLE IF NOT EXISTS captcha_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Добавляем колонку turnstile_site_key в settings, если нет
    try:
        cur.execute("SELECT turnstile_site_key FROM settings LIMIT 1")
    except sqlite3.OperationalError:
        # settings — key-value, колонки не добавляем
        pass
    
    # Миграция: пересоздаём blocks_history с правильным FK (без CASCADE)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocks_history_new (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id    TEXT,
            config_snapshot TEXT NOT NULL,
            user_id     INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='blocks_history'")
    if cur.fetchone()[0] > 0:
        cur.execute("INSERT OR IGNORE INTO blocks_history_new SELECT * FROM blocks_history")
        cur.execute("DROP TABLE blocks_history")
        cur.execute("ALTER TABLE blocks_history_new RENAME TO blocks_history")
    
    conn.commit()
    conn.close()


def save_block_version(block_id: str, config_snapshot: dict, user_id: int = None):
    """Сохраняет версию блока в history."""
    conn = get_db()
    conn.execute(
        "INSERT INTO blocks_history (block_id, config_snapshot, user_id) VALUES (?, ?, ?)",
        (block_id, json.dumps(config_snapshot, ensure_ascii=False), user_id),
    )
    conn.commit()
    conn.close()


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS pages (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            icon        TEXT DEFAULT '📄',
            parent      TEXT REFERENCES pages(id) ON DELETE SET NULL,
            sort_order  INTEGER DEFAULT 99,
            status      TEXT DEFAULT 'draft' CHECK(status IN ('draft','published')),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS blocks (
            id          TEXT PRIMARY KEY,
            page_id     TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
            type        TEXT NOT NULL CHECK(type IN ('hero','text','image','gallery','video','table','cards','documents','form','divider')),
            name        TEXT DEFAULT 'Блок',
            sort_order  INTEGER DEFAULT 0,
            config      TEXT DEFAULT '{}',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS roles (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            icon        TEXT DEFAULT '🛡️',
            sections    TEXT DEFAULT '[]',
            caps        TEXT DEFAULT '{}',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS media (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            filename        TEXT NOT NULL,
            original_name   TEXT NOT NULL,
            mime_type       TEXT NOT NULL,
            size            INTEGER NOT NULL,
            alt_text        TEXT DEFAULT '',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS suggestions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            email       TEXT NOT NULL,
            category    TEXT DEFAULT 'Новость',
            text        TEXT NOT NULL,
            status      TEXT DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role        TEXT DEFAULT 'admin',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            token       TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at  TIMESTAMP NOT NULL
        );

        CREATE TABLE IF NOT EXISTS menu_groups (
            id          TEXT PRIMARY KEY,
            name        TEXT NOT NULL,
            icon        TEXT DEFAULT '📁',
            sort_order  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS menu_group_items (
            group_id    TEXT NOT NULL REFERENCES menu_groups(id) ON DELETE CASCADE,
            page_id     TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
            sort_order  INTEGER DEFAULT 0,
            PRIMARY KEY (group_id, page_id)
        );

        -- Фаза 2: Версионирование блоков
        CREATE TABLE IF NOT EXISTS blocks_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            block_id    TEXT,
            config_snapshot TEXT NOT NULL,
            user_id     INTEGER,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Фаза 2: CAPTCHA настройки
        CREATE TABLE IF NOT EXISTS captcha_config (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """)

    conn.commit()
    conn.close()


def seed_db():
    """Первичное наполнение БД, если она пуста."""
    conn = get_db()
    cur = conn.cursor()

    # Проверяем, есть ли уже страницы
    existing = cur.execute("SELECT COUNT(*) FROM pages").fetchone()[0]
    if existing > 0:
        conn.close()
        return

    # ---- Настройки по умолчанию ----
    default_settings = {
        "site_name": "Золотаревка",
        "site_description": "Неофициальный портал села",
        "logo_text": "Золотаревка",
        "logo_icon": "🌾",
        "header_bg_color": "#1b4332",
        "footer_bg_color": "#1b4332",
        "primary_color": "#2d6a4f",
        "accent_color": "#d4a373",
        "hero_title": "Добро пожаловать в Золотаревку!",
        "hero_subtitle": "Неофициальный портал нашего села. Новости, события, спорт, история и многое другое.",
        "hero_btn_text": "Исследовать разделы →",
        "hero_bg_color": "#1b4332",
        "social_vk": "#",
        "social_telegram": "#",
        "social_ok": "#",
        "contact_email": "info@zolotarevka.ru",
        "suggest_title": "💡 Хотите предложить новость?",
        "suggest_text": "Жители села могут присылать свои фото и истории.",
        "footer_copyright": "© 2026 Неофициальный портал села Золотаревка. Сделано с ❤️ для земляков.",
        "menu_groups_config": '[{"id":"organizations","name":"Организации","icon":"🏢","pages":["school","kindergarten","farm"]},{"id":"sports","name":"Спорт","icon":"⚽","pages":["sports"]},{"id":"village-life","name":"Жизнь села","icon":"🏘️","pages":["village-life"]}]',
    }
    for k, v in default_settings.items():
        cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # ---- Страницы (из прототипа site-builder-v2.html) ----
    pages_data = [
        ("home",            "Главная",       "🏠", None,   0,  "published"),
        ("school",          "Школа",         "📚", None,   1,  "published"),
        ("school-news",     "Новости школы", "📰", "school", 0, "published"),
        ("school-docs",     "Документы",     "📄", "school", 1, "published"),
        ("kindergarten",    "Детский сад",   "🧸", None,   2,  "published"),
        ("farm",            "Совхоз",        "🌾", None,   3,  "published"),
        ("farm-products",   "Продукция",     "📦", "farm", 0,  "draft"),
        ("farm-vacancies",  "Вакансии",      "💼", "farm", 1,  "published"),
        ("sports",          "Спорт",         "⚽", None,   4,  "published"),
        ("sports-team",     "Команда",       "👥", "sports", 0, "published"),
        ("sports-matches",  "Матчи",         "🏆", "sports", 1, "draft"),
        ("village-life",    "Жизнь села",    "🏘️", None,   5,  "published"),
        ("village-history", "История",       "📜", "village-life", 0, "published"),
        ("village-culture", "Дом Культуры",  "🎭", "village-life", 1, "draft"),
        ("bulletin",        "Объявления",    "📋", "village-life", 2, "published"),
        ("media",           "Медиа",         "📸", None,   6,  "published"),
        ("news",            "Новости",       "📰", None,   7,  "published"),
    ]
    for p in pages_data:
        cur.execute(
            "INSERT INTO pages (id, name, icon, parent, sort_order, status) VALUES (?, ?, ?, ?, ?, ?)",
            (p[0], p[1], p[2], p[3], p[4], p[5])
        )

    # ---- Блоки для главной ----
    home_blocks = [
        ("hero-home", "home", "hero", 0, json.dumps({
            "title": "Добро пожаловать в Золотаревку!",
            "subtitle": "Неофициальный портал нашего села",
            "btn_text": "Исследовать разделы →",
            "btn_url": "#bento",
            "bg_color": "#1b4332",
            "bg_image": ""
        }, ensure_ascii=False)),
        ("bento-home", "home", "cards", 1, json.dumps({
            "auto_from_tree": True,
            "columns": 3,
            "all_link_text": "Все разделы →",
            "card_overrides": {
                "school": {"image": "", "text": "Новости, расписание, достижения учеников"},
                "kindergarten": {"image": "", "text": "Жизнь групп, советы, фотоотчеты"},
                "farm": {"image": "", "text": "Продукция, вакансии, история"},
                "sports": {"image": "", "text": "Команда, матчи, турнирная таблица"},
                "village-life": {"image": "", "text": "События, объявления, история села"},
                "media": {"image": "", "text": "Фото и видео из жизни села"},
                "news": {"image": "", "text": "Все новости одним потоком"},
            }
        }, ensure_ascii=False)),
        ("welcome-home", "home", "text", 2, json.dumps({
            "content": "<p>Добро пожаловать на наш портал! Здесь вы найдёте всё самое важное о жизни села Золотаревка. Новости школы и детского сада, жизнь совхоза, спортивные события, история села и многое другое.</p>"
        }, ensure_ascii=False)),
        ("suggest-home", "home", "form", 3, json.dumps({
            "form_type": "suggest",
            "title": "💡 Хотите предложить новость?"
        }, ensure_ascii=False)),
    ]
    for b in home_blocks:
        cur.execute(
            "INSERT INTO blocks (id, page_id, type, sort_order, config) VALUES (?, ?, ?, ?, ?)",
            (b[0], b[1], b[2], b[3], b[4])
        )

    # ---- Блоки для школы ----
    school_blocks = [
        ("hero-school", "school", "hero", 0, json.dumps({
            "title": "📚 Школа села Золотаревка",
            "subtitle": "Новости учебной жизни, достижения учеников",
            "btn_text": "",
            "bg_color": "#4a90d9"
        }, ensure_ascii=False)),
        ("text-school", "school", "text", 1, json.dumps({
            "content": "<p>Наша школа — центр образования и воспитания подрастающего поколения. Мы гордимся нашими учениками и учителями.</p>"
        }, ensure_ascii=False)),
        ("docs-school", "school", "documents", 2, json.dumps({
            "docs": [
                {"title": "Устав школы", "url": "#", "description": "Основной документ"},
                {"title": "Расписание звонков", "url": "#", "description": ""}
            ]
        }, ensure_ascii=False)),
    ]
    for b in school_blocks:
        cur.execute(
            "INSERT INTO blocks (id, page_id, type, sort_order, config) VALUES (?, ?, ?, ?, ?)",
            (b[0], b[1], b[2], b[3], b[4])
        )

    # ---- Роли ----
    roles_data = [
        ("admin",            "Администратор", "👑", '"__all__"',         '{"moderation":true,"upload":true,"publish":true}'),
        ("school_editor",    "Редактор школы", "📚", '["school","school-news","school-docs","kindergarten"]', '{"moderation":true,"upload":true,"publish":true}'),
        ("sports_editor",    "Редактор спорта", "⚽", '["sports","sports-team","sports-matches"]', '{"moderation":false,"upload":true,"publish":true}'),
        ("farm_editor",      "Редактор совхоза", "🌾", '["farm","farm-products","farm-vacancies"]', '{"moderation":false,"upload":true,"publish":true}'),
        ("content_moderator","Модератор", "🛡️", '[]', '{"moderation":true,"upload":false,"publish":false}'),
        ("community_author", "Автор", "✍️", '[]', '{"moderation":false,"upload":false,"publish":false}'),
    ]
    for r in roles_data:
        cur.execute(
            "INSERT INTO roles (id, name, icon, sections, caps) VALUES (?, ?, ?, ?, ?)",
            (r[0], r[1], r[2], r[3], r[4])
        )

    # ---- Admin user (создаётся только если нет) ----
    import hashlib, bcrypt
    admin_exists = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if admin_exists == 0:
        pw_hash = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", pw_hash, "admin")
        )
        print("✅ Admin user created")

    conn.commit()
    conn.close()
    print("✅ База данных заполнена начальными данными.")


# Инициализация при импорте
if not os.path.exists(DATABASE_PATH):
    init_db()
    seed_db()
    print("✅ База данных создана и заполнена.")
