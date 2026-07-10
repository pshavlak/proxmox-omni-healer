#!/usr/bin/env python3
"""
Золотаревка — FastAPI приложение.
Запуск: uvicorn app:app --reload
"""
import os
import json
import sqlite3
import uuid
import bcrypt
import struct
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from collections import defaultdict

from fastapi import FastAPI, Request, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Секретный ключ для сессий
SECRET_KEY = os.getenv("ZOLO_SECRET")
if not SECRET_KEY:
    raise RuntimeError("ZOLO_SECRET не задан! Установите переменную окружения.")

import config as cfg
from database import get_db, init_db
from models import PageCreate, PageUpdate, BlockCreate, RoleCreate, SuggestionCreate, ReorderRequest, MenuGroupCreate, MenuGroupUpdate


# ====== Jinja2 шаблоны ======
jinja_env = Environment(
    loader=FileSystemLoader(cfg.TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)

# Добавляем фильтр from_json для парсинга JSON в шаблонах
jinja_env.filters["from_json"] = lambda v: json.loads(v) if isinstance(v, str) else (v or [])
jinja_env.filters["to_json"] = lambda v: json.dumps(v, ensure_ascii=False)
jinja_env.globals["now"] = datetime.now


def render(template_name: str, **kwargs) -> str:
    """Рендер Jinja2 шаблона с общими переменными."""
    tpl = jinja_env.get_template(template_name)
    return tpl.render(**kwargs)


# ====== Lifespan ======
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при запуске."""
    from database import init_db, seed_db, migrate_db
    init_db()
    migrate_db()
    seed_db()
    # Создаём директорию для загрузок
    os.makedirs(cfg.UPLOAD_DIR, exist_ok=True)
    yield


# ====== FastAPI ======
app = FastAPI(title="Золотаревка", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Статика
app.mount("/static", StaticFiles(directory=cfg.STATIC_DIR), name="static")

# Админка (отдельная SPA) — монтируем, доступ контролирует middleware
if cfg.ADMIN_ENABLED and os.path.isdir(cfg.ADMIN_DIR):
    app.mount("/admin", StaticFiles(directory=cfg.ADMIN_DIR, html=True), name="admin")


# ====== Health Check ======
@app.get("/health")
def health():
    return {"status": "ok"}


# ====== Rate limiter ======
class RateLimiter:
    """Простой in-memory rate limiter."""
    def __init__(self, max_requests=10, window_sec=60):
        self.max_requests = max_requests
        self.window_sec = window_sec
        self._requests = defaultdict(list)

    def check(self, key: str) -> bool:
        now = datetime.now()
        self._requests[key] = [t for t in self._requests[key] if (now - t).total_seconds() < self.window_sec]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True


login_limiter = RateLimiter(max_requests=10, window_sec=60)  # 10 попыток в минуту
suggest_limiter = RateLimiter(max_requests=5, window_sec=600)  # 5 за 10 минут
api_limiter = RateLimiter(max_requests=30, window_sec=60)  # 30 write-запросов в минуту


# ====== Auth middleware ======
PUBLIC_API_PREFIXES = ("/api/content/", "/api/feedback", "/api/menu")
PUBLIC_PATHS = {"/", "/login", "/logout", "/api/suggest"}

ADMIN_WRITE_METHODS = {"POST", "PUT", "DELETE", "PATCH"}

ADMIN_ROUTES = {  # пути, требующие роль admin
    "/api/users", "/api/users/",
    "/api/roles", "/api/roles/",
    "/api/settings",
    "/api/suggestions",
}

@app.middleware("http")
async def check_admin_auth(request: Request, call_next):
    path = request.url.path.rstrip("/") or "/"

    # Публичные пути — пропускаем
    if path in PUBLIC_PATHS:
        return await call_next(request)
    if path.startswith("/static/"):
        return await call_next(request)
    if path.startswith(PUBLIC_API_PREFIXES):
        return await call_next(request)
    if not path.startswith("/admin") and not path.startswith("/api/"):
        return await call_next(request)

    # CSRF: проверяем Origin/Referer для state-changing запросов
    if request.method in ADMIN_WRITE_METHODS:
        origin = request.headers.get("origin", "")
        referer = request.headers.get("referer", "")
        allowed_hosts = ["xn--80aaflivdxbvu.xn--p1ai", "www.xn--80aaflivdxbvu.xn--p1ai",
                         "золотаревка.рф", "www.золотаревка.рф",
                         "localhost", "127.0.0.1"]
        valid = False
        for h in [origin, referer]:
            for allowed in allowed_hosts:
                if allowed in h:
                    valid = True
                    break
        if not valid and origin:  # пропускаем запросы без Origin (прямые вызовы API)
            return JSONResponse({"error": "CSRF: invalid origin"}, status_code=403)

    # Проверяем сессию
    session_token = request.cookies.get("session")
    if not session_token:
        if path.startswith("/api/"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return RedirectResponse(url="/login", status_code=302)

    conn = None
    try:
        conn = get_db()
        row = conn.execute(
            "SELECT u.id, u.username, u.role FROM sessions s JOIN users u ON s.user_id = u.id "
            "WHERE s.token = ? AND s.expires_at > datetime('now')",
            (session_token,),
        ).fetchone()
    except sqlite3.Error as e:
        return JSONResponse({"error": "Database error"}, status_code=500)
    finally:
        if conn is not None:
            conn.close()

    if not row:
        if path.startswith("/api/"):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        return RedirectResponse(url="/login", status_code=302)

    # RBAC: write-операции на защищённых путях требуют роль admin
    user = dict(row)
    if request.method in ADMIN_WRITE_METHODS:
        is_admin_route = any(path == r.rstrip("/") or path.startswith(r.rstrip("/") + "/")
                             for r in ADMIN_ROUTES)
        if is_admin_route and user["role"] != "admin":
            return JSONResponse({"error": "Forbidden: admin only"}, status_code=403)

    # Всё хорошо
    return await call_next(request)


# ====== HELPERS ======
def row_to_dict(row):
    if row is None:
        return None
    return dict(row)


# ====== Auth routes ======
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    session_token = request.cookies.get("session")
    if session_token:
        conn = get_db()
        row = conn.execute(
            "SELECT 1 FROM sessions WHERE token = ? AND expires_at > datetime('now')",
            (session_token,),
        ).fetchone()
        conn.close()
        if row:
            return RedirectResponse(url="/admin/", status_code=302)
    return HTMLResponse(render("login.html"))


@app.post("/login")
def login_post(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not login_limiter.check(f"login:{client_ip}"):
        return HTMLResponse(
            render("login.html", error="Слишком много попыток. Попробуйте через минуту."),
            status_code=429,
        )

    conn = get_db()
    user = conn.execute(
        "SELECT id, username, role, password_hash FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if not user:
        conn.close()
        return HTMLResponse(
            render("login.html", error="Неверный логин или пароль"),
            status_code=401,
        )
    try:
        password_valid = bcrypt.checkpw(password.encode(), user['password_hash'].encode())
    except ValueError:
        password_valid = False
    if not password_valid:
        conn.close()
        return HTMLResponse(
            render("login.html", error="Неверный логин или пароль"),
            status_code=401,
        )

    # Создаём сессию
    token = uuid.uuid4().hex
    expires_at = (datetime.now() + timedelta(hours=24)).isoformat()
    conn.execute(
        "INSERT INTO sessions (token, user_id, expires_at) VALUES (?, ?, ?)",
        (token, user["id"], expires_at),
    )
    conn.commit()
    conn.close()

    # Устанавливаем cookie
    is_https = request.headers.get("x-forwarded-proto", "") == "https"
    response = RedirectResponse(url="/admin/", status_code=302)
    response.set_cookie(
        key="session",
        value=token,
        max_age=86400,  # 24 часа
        httponly=True,
        samesite="lax",
        secure=is_https,
    )
    return response


@app.get("/logout")
def logout(request: Request):
    session_token = request.cookies.get("session")
    if session_token:
        conn = get_db()
        conn.execute("DELETE FROM sessions WHERE token = ?", (session_token,))
        conn.commit()
        conn.close()

    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session")
    return response


def list_from_json(val, default=None):
    if not val:
        return default or []
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return default or []
    return val or default or []


def get_children_ids(page_id: str, conn) -> list:
    """Рекурсивно собирает ID всех дочерних страниц."""
    ids = []
    rows = conn.execute(
        "SELECT id FROM pages WHERE parent = ?", (page_id,)
    ).fetchall()
    for r in rows:
        ids.append(r["id"])
        ids.extend(get_children_ids(r["id"], conn))
    return ids


# ====== API: Pages ======
@app.get("/api/pages")
def api_get_pages():
    conn = get_db()
    rows = conn.execute("SELECT * FROM pages ORDER BY sort_order ASC, name ASC").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.post("/api/pages")
def api_create_page(data: PageCreate):
    if not api_limiter.check("api:create_page"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    data.id = data.id.strip().lower().replace(" ", "-").replace("--", "-")
    # Проверка уникальности
    existing = conn.execute("SELECT id FROM pages WHERE id = ?", (data.id,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Страница с таким ID уже существует")
    conn.execute(
        "INSERT INTO pages (id, name, icon, parent, sort_order, status) VALUES (?, ?, ?, ?, ?, 'draft')",
        (data.id, data.name, data.icon, data.parent, data.sort_order),
    )
    conn.commit()
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (data.id,)).fetchone()
    conn.close()
    return row_to_dict(page)


@app.put("/api/pages/{page_id}")
def api_update_page(page_id: str, data: PageUpdate):
    if not api_limiter.check("api:update_page"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    existing = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Страница не найдена")

    updates = {}
    if data.name is not None: updates["name"] = data.name
    if data.icon is not None: updates["icon"] = data.icon
    if data.parent is not None: updates["parent"] = data.parent or None
    if data.sort_order is not None: updates["sort_order"] = data.sort_order
    if data.status is not None: updates["status"] = data.status
    updates["updated_at"] = datetime.now().isoformat()

    allowed_columns = {"name", "icon", "parent", "sort_order", "status", "updated_at"}
    for k, v in updates.items():
        if k not in allowed_columns:
            continue
        conn.execute(f"UPDATE pages SET {k} = ? WHERE id = ?", (v, page_id))
    conn.commit()
    page = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    conn.close()
    return row_to_dict(page)


@app.delete("/api/pages/{page_id}")
def api_delete_page(page_id: str):
    if not api_limiter.check("api:delete_page"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    if page_id == "home":
        raise HTTPException(400, "Главную страницу нельзя удалить")
    conn = get_db()
    existing = conn.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Страница не найдена")
    # Каскадное удаление детей
    child_ids = get_children_ids(page_id, conn)
    for cid in child_ids:
        conn.execute("DELETE FROM blocks WHERE page_id = ?", (cid,))
        conn.execute("DELETE FROM pages WHERE id = ?", (cid,))
    conn.execute("DELETE FROM blocks WHERE page_id = ?", (page_id,))
    conn.execute("DELETE FROM pages WHERE id = ?", (page_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.put("/api/pages/reorder")
def api_reorder_pages(data: ReorderRequest):
    if not api_limiter.check("api:reorder_pages"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    for item in data.items:
        conn.execute("UPDATE pages SET sort_order = ? WHERE id = ?", (item.sort_order, item.id))
    conn.commit()
    conn.close()
    return {"success": True}


# ====== API: Blocks ======
@app.get("/api/pages/{page_id}/blocks")
def api_get_blocks(page_id: str):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM blocks WHERE page_id = ? ORDER BY sort_order ASC", (page_id,)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = row_to_dict(r)
        d["config"] = json.loads(d.get("config", "{}"))
        result.append(d)
    return result


@app.put("/api/pages/{page_id}/blocks")
def api_save_blocks(page_id: str, blocks: list = Body(...)):
    """Сохраняет все блоки страницы (заменяет существующие)."""
    if not api_limiter.check("api:save_blocks"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    conn.execute("DELETE FROM blocks WHERE page_id = ?", (page_id,))
    for i, b in enumerate(blocks):
        bid = b.get("id")
        if not bid:
            bid = f"b{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
        btype = b.get("type", "text")
        bname = b.get("name", "Блок")
        bconfig = json.dumps(b.get("config", {}), ensure_ascii=False)

        # Если ID уже занят блоком другой страницы — генерируем уникальный
        existing = conn.execute(
            "SELECT id, page_id FROM blocks WHERE id = ?", (bid,)
        ).fetchone()
        if existing and existing["page_id"] != page_id:
            bid = f"b{hashlib.md5(f'{bid}_{datetime.now()}'.encode()).hexdigest()[:12]}"

        try:
            conn.execute(
                "INSERT INTO blocks (id, page_id, type, name, sort_order, config) VALUES (?, ?, ?, ?, ?, ?)",
                (bid, page_id, btype, bname, i, bconfig),
            )
        except sqlite3.IntegrityError as e:
            conn.close()
            raise HTTPException(400, f"Ошибка базы данных: {e}")
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/api/blocks/{block_id}/move")
def api_move_block(block_id: str, direction: str = "down"):
    """Переместить блок вверх или вниз."""
    if not api_limiter.check("api:move_block"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    block = conn.execute("SELECT * FROM blocks WHERE id = ?", (block_id,)).fetchone()
    if not block:
        conn.close()
        raise HTTPException(404, "Блок не найден")

    page_id = block["page_id"]
    current_order = block["sort_order"]

    if direction == "up":
        target = conn.execute(
            "SELECT * FROM blocks WHERE page_id = ? AND sort_order < ? ORDER BY sort_order DESC LIMIT 1",
            (page_id, current_order),
        ).fetchone()
    else:
        target = conn.execute(
            "SELECT * FROM blocks WHERE page_id = ? AND sort_order > ? ORDER BY sort_order ASC LIMIT 1",
            (page_id, current_order),
        ).fetchone()

    if target:
        conn.execute("UPDATE blocks SET sort_order = ? WHERE id = ?", (target["sort_order"], block_id))
        conn.execute("UPDATE blocks SET sort_order = ? WHERE id = ?", (current_order, target["id"]))
        conn.commit()

    conn.close()
    return {"success": True}


# ====== API: Roles ======
@app.get("/api/roles")
def api_get_roles():
    conn = get_db()
    rows = conn.execute("SELECT * FROM roles ORDER BY name ASC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = row_to_dict(r)
        d["sections"] = list_from_json(d["sections"], [])
        d["caps"] = list_from_json(d["caps"], {})
        # Имитация счётчика пользователей (на MVP всё в 0)
        d["users"] = 0
        result.append(d)
    return result


@app.post("/api/roles")
def api_create_role(data: RoleCreate):
    if not api_limiter.check("api:create_role"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    rid = data.id or f"role_{data.name.lower().replace(' ', '_')}"
    conn.execute(
        "INSERT INTO roles (id, name, icon, sections, caps) VALUES (?, ?, ?, ?, ?)",
        (rid, data.name, data.icon, json.dumps(data.sections, ensure_ascii=False), json.dumps(data.caps, ensure_ascii=False)),
    )
    conn.commit()
    role = conn.execute("SELECT * FROM roles WHERE id = ?", (rid,)).fetchone()
    conn.close()
    return row_to_dict(role)


@app.put("/api/roles/{role_id}")
def api_update_role(role_id: str, data: RoleCreate):
    if not api_limiter.check("api:update_role"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    existing = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(404, "Роль не найдена")
    conn.execute(
        "UPDATE roles SET name=?, icon=?, sections=?, caps=? WHERE id=?",
        (data.name, data.icon, json.dumps(data.sections, ensure_ascii=False), json.dumps(data.caps, ensure_ascii=False), role_id),
    )
    conn.commit()
    role = conn.execute("SELECT * FROM roles WHERE id = ?", (role_id,)).fetchone()
    conn.close()
    return row_to_dict(role)


@app.delete("/api/roles/{role_id}")
def api_delete_role(role_id: str):
    if not api_limiter.check("api:delete_role"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    if role_id == "admin":
        raise HTTPException(400, "Роль администратора нельзя удалить")
    conn = get_db()
    conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ====== API: Users ======
def _get_current_user(request: Request):
    """Возвращает user_id из сессионной куки."""
    token = request.cookies.get("session")
    if not token:
        raise HTTPException(401, "Unauthorized")
    conn = get_db()
    row = conn.execute(
        "SELECT u.id, u.username, u.role FROM sessions s JOIN users u ON s.user_id = u.id "
        "WHERE s.token = ? AND s.expires_at > datetime('now')",
        (token,),
    ).fetchone()
    conn.close()
    if not row:
        raise HTTPException(401, "Unauthorized")
    return dict(row)


@app.get("/api/users")
def api_get_users(request: Request):
    current = _get_current_user(request)
    conn = get_db()
    rows = conn.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/api/users")
def api_create_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("admin"),
):
    if not api_limiter.check(f"api:create_user"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    current = _get_current_user(request)
    if current["role"] != "admin":
        raise HTTPException(403, "Только администратор может создавать пользователей")

    if len(username) < 3 or len(password) < 8:
        raise HTTPException(400, "Логин минимум 3 символа, пароль — 8")

    conn = get_db()
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        conn.close()
        raise HTTPException(400, "Пользователь с таким логином уже существует")

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, pw_hash, role),
    )
    conn.commit()
    user = conn.execute(
        "SELECT id, username, role, created_at FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    conn.close()
    return dict(user)


@app.delete("/api/users/{user_id}")
def api_delete_user(user_id: int, request: Request):
    if not api_limiter.check("api:delete_user"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    current = _get_current_user(request)
    if current["role"] != "admin":
        raise HTTPException(403, "Только администратор может удалять пользователей")
    if current["id"] == user_id:
        raise HTTPException(400, "Нельзя удалить самого себя")

    conn = get_db()
    conn.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"success": True}


@app.post("/api/change-password")
def api_change_password(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
):
    if not api_limiter.check("api:change_password"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    current = _get_current_user(request)
    if len(new_password) < 8:
        raise HTTPException(400, "Новый пароль должен быть минимум 8 символов")

    conn = get_db()
    user = conn.execute(
        "SELECT id, password_hash FROM users WHERE id = ?",
        (current["id"],),
    ).fetchone()
    if not user or not bcrypt.checkpw(old_password.encode(), user['password_hash'].encode()):
        conn.close()
        raise HTTPException(400, "Неверный текущий пароль")

    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_hash, current["id"]))
    # Сбрасываем все сессии пользователя, кроме текущей
    token = request.cookies.get("session")
    conn.execute(
        "DELETE FROM sessions WHERE user_id = ? AND token != ?",
        (current["id"], token),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Пароль изменён"}


# ====== API: Settings ======
@app.get("/api/settings")
def api_get_settings():
    conn = get_db()
    rows = conn.execute("SELECT * FROM settings").fetchall()
    conn.close()
    result = {}
    for r in rows:
        val = r["value"]
        # Try to parse as JSON if it looks like a dict or list
        if val and val.strip().startswith(("{", "[")):
            try:
                parsed = json.loads(val)
                if isinstance(parsed, (dict, list)):
                    val = parsed
            except (json.JSONDecodeError, TypeError):
                pass
        result[r["key"]] = val
    return result


@app.put("/api/settings")
def api_update_settings(settings: dict):
    if not api_limiter.check("api:update_settings"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    for k, v in settings.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        elif v is None:
            v = ""
        conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
    return {"success": True}


# ====== API: Media ======
@app.get("/api/media")
def api_get_media():
    conn = get_db()
    rows = conn.execute("SELECT * FROM media ORDER BY created_at DESC").fetchall()
    conn.close()
    result = []
    for r in rows:
        d = row_to_dict(r)
        d["url"] = f"/static/uploads/{d['filename']}"
        result.append(d)
    return result


@app.post("/api/media/upload")
async def api_upload_media(file: UploadFile = File(...), alt_text: str = Form("")):
    if not api_limiter.check("api:upload_media"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    ext = Path(file.filename).suffix.lower()
    if ext not in cfg.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Недопустимый тип файла: {ext}")
    # Читаем содержимое
    content = await file.read()
    if len(content) > cfg.MAX_UPLOAD_SIZE:
        raise HTTPException(400, "Файл слишком большой")
    # Уникальное имя
    file_hash = hashlib.md5(content).hexdigest()[:12]
    new_filename = f"{file_hash}{ext}"
    save_path = Path(cfg.UPLOAD_DIR) / new_filename
    # Сохраняем
    save_path.write_bytes(content)
    # В БД
    conn = get_db()
    conn.execute(
        "INSERT INTO media (filename, original_name, mime_type, size, alt_text) VALUES (?, ?, ?, ?, ?)",
        (new_filename, file.filename, file.content_type or "application/octet-stream", len(content), alt_text),
    )
    conn.commit()
    mid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return {"id": mid, "filename": new_filename, "url": f"/static/uploads/{new_filename}"}


@app.post("/api/feedback")
def api_feedback(request: Request, data: SuggestionCreate):
    """Обратная связь — сохраняет как suggestion."""
    if not api_limiter.check("api:feedback"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    conn.execute(
        "INSERT INTO suggestions (name, email, category, text) VALUES (?, ?, ?, ?)",
        (data.name, data.email, "Обратная связь", data.text),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Спасибо! Ваше сообщение отправлено."}


@app.delete("/api/media/{media_id}")
def api_delete_media(media_id: int):
    if not api_limiter.check("api:delete_media"):
        raise HTTPException(429, "Слишком много запросов. Попробуйте позже.")
    conn = get_db()
    item = conn.execute("SELECT * FROM media WHERE id = ?", (media_id,)).fetchone()
    if not item:
        conn.close()
        raise HTTPException(404, "Файл не найден")
    # Удаляем файл
    file_path = Path(cfg.UPLOAD_DIR) / item["filename"]
    if file_path.exists():
        file_path.unlink()
    conn.execute("DELETE FROM media WHERE id = ?", (media_id,))
    conn.commit()
    conn.close()
    return {"success": True}


# ====== API: Suggestions ======
@app.post("/api/suggest")
def api_suggest(request: Request, data: SuggestionCreate):
    # Rate limiting
    client_ip = request.client.host if request.client else "unknown"
    if not suggest_limiter.check(f"suggest:{client_ip}"):
        return JSONResponse(
            {"error": "Слишком много запросов. Попробуйте позже."},
            status_code=429,
        )
    conn = get_db()
    conn.execute(
        "INSERT INTO suggestions (name, email, category, text) VALUES (?, ?, ?, ?)",
        (data.name, data.email, data.category, data.text),
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Спасибо! Ваша новость отправлена на модерацию."}


@app.get("/api/suggestions")
def api_get_suggestions():
    conn = get_db()
    rows = conn.execute("SELECT * FROM suggestions ORDER BY created_at DESC LIMIT 50").fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


# ====== API: Content (для публичного сайта) ======
@app.get("/api/content/pages")
def api_content_pages():
    """Публичные страницы с иерархией для навигации."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, icon, parent, sort_order FROM pages WHERE status='published' ORDER BY sort_order ASC"
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


@app.get("/api/content/recent")
def api_content_recent(limit: int = 6):
    """Последние опубликованные страницы (имитация новостной ленты)."""
    limit = min(max(limit, 1), 50)  # ограничение 1-50
    conn = get_db()
    rows = conn.execute(
        "SELECT id, name, icon, updated_at FROM pages WHERE status='published' ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [row_to_dict(r) for r in rows]


# ====== Публичный сайт (Jinja2) ======
def get_nav_tree(conn):
    """Строит дерево навигации для меню."""
    pages = conn.execute(
        "SELECT id, name, icon, parent FROM pages WHERE status='published' ORDER BY sort_order"
    ).fetchall()
    roots = [row_to_dict(p) for p in pages if not p["parent"]]
    children = {}
    for p in pages:
        pid = p["parent"]
        if pid:
            children.setdefault(pid, []).append(row_to_dict(p))
    for root in roots:
        root["children"] = children.get(root["id"], [])
        for child in root["children"]:
            child["children"] = children.get(child["id"], [])
    return roots


def get_page_with_blocks(slug: str, conn):
    """Возвращает страницу с блоками."""
    page = conn.execute(
        "SELECT * FROM pages WHERE id = ? AND status='published'", (slug,)
    ).fetchone()
    if not page:
        # Пробуем draft для предпросмотра
        page = conn.execute(
            "SELECT * FROM pages WHERE id = ?", (slug,)
        ).fetchone()
        if not page:
            return None, None
    blocks = conn.execute(
        "SELECT * FROM blocks WHERE page_id = ? ORDER BY sort_order ASC", (slug,)
    ).fetchall()
    blocks_data = []
    for b in blocks:
        bd = row_to_dict(b)
        bd["config"] = json.loads(bd.get("config", "{}"))
        blocks_data.append(bd)
    return row_to_dict(page), blocks_data


def get_breadcrumbs(page_id: str, conn) -> list:
    """Строит хлебные крошки."""
    crumbs = []
    current = conn.execute("SELECT id, name, parent FROM pages WHERE id = ?", (page_id,)).fetchone()
    while current:
        crumbs.insert(0, {"id": current["id"], "name": current["name"]})
        if current["parent"]:
            current = conn.execute(
                "SELECT id, name, parent FROM pages WHERE id = ?", (current["parent"],)
            ).fetchone()
        else:
            current = None
    return crumbs


@app.get("/", response_class=HTMLResponse)
def web_index(request: Request):
    conn = get_db()
    pages = get_nav_tree(conn)
    _page, blocks = get_page_with_blocks("home", conn)
    settings = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}
    # Публичные разделы (без подразделов, для бенто-сетки)
    sections = [
        row_to_dict(r) for r in conn.execute(
            "SELECT id, name, icon FROM pages WHERE parent IS NULL AND status='published' ORDER BY sort_order"
        ).fetchall()
    ]
    conn.close()
    return HTMLResponse(render(
        "index.html",
        pages=pages,
        blocks=blocks,
        settings=settings,
        sections=sections,
        recent_news=sections[:3],
        page_title="Главная",
    ))


@app.get("/{slug:path}", response_class=HTMLResponse)
def web_page(slug: str, request: Request):
    # Если API-путь не обработан другими маршрутами — JSON 404
    if slug.startswith("api/"):
        return JSONResponse({"error": "Not found"}, status_code=404)

    # Если админский путь не обработан монтированием — редирект на логин
    if slug.startswith("admin"):
        session_token = request.cookies.get("session")
        if session_token:
            # Есть сессия, но путь не найден — 404
            return HTMLResponse(render("errors/404.html", slug=slug))

        return RedirectResponse(url="/login", status_code=302)

    slug = slug.rstrip("/").split("/")[-1]  # last segment
    conn = get_db()
    page, blocks = get_page_with_blocks(slug, conn)
    if not page:
        # 404
        pages = get_nav_tree(conn)
        settings = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}
        conn.close()
        return HTMLResponse(render("errors/404.html", pages=pages, settings=settings, slug=slug))

    pages = get_nav_tree(conn)
    settings = {r["key"]: r["value"] for r in conn.execute("SELECT * FROM settings").fetchall()}
    breadcrumbs = get_breadcrumbs(slug, conn)
    conn.close()

    return HTMLResponse(render(
        "page.html",
        page=page,
        blocks=blocks,
        pages=pages,
        settings=settings,
        breadcrumbs=breadcrumbs,
        page_title=page["name"],
    ))


# ====== Запуск ======
if __name__ == "__main__":
    import uvicorn
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    reload_mode = debug_mode # Only reload if debug mode is true
    port = int(os.getenv("PORT", 8000)) # Allow port to be configurable via env var
    host = os.getenv("HOST", "0.0.0.0")

    uvicorn.run("app:app", host=host, port=port, reload=reload_mode)
