import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy import select

from app.database import Base, engine
from app.models import MenuItem, Page, MediaItem, Setting, Suggestion, Role, User  # noqa: F401 — register models with Base
from app.routers import auth, menu, page, public, admin_tools, users
from app.services.auth import is_authenticated

app = FastAPI(title="Золотаревка-сайт", version="0.1.0")

# ── Session middleware (for admin auth) ──────────────────────────────────
_SESSION_SECRET = os.environ.get(
    "SESSION_SECRET",
    "change-me-in-production-use-a-long-random-string",
)
app.add_middleware(SessionMiddleware, secret_key=_SESSION_SECRET)

BASE_DIR = Path(__file__).resolve().parent

# ── Static files ─────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ── Jinja2 templates ─────────────────────────────────────────────────────
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Register a template global so all templates can access the menu without
# each route handler having to pass it manually.
def _inject_menu() -> list[dict]:
    """Template-callable: returns the active menu tree as nested dicts."""
    return _load_menu_dicts()

templates.env.globals["get_menu"] = _inject_menu


# (startup handler is defined below with FTS initialization)


# ── Template context helpers ─────────────────────────────────────────────
def _load_menu_dicts() -> list[dict]:
    """Load the active menu tree as a list of nested dicts for Jinja2."""
    from app.database import SessionLocal
    from app.services.menu import get_active_menu_tree

    db = SessionLocal()
    try:
        tree = get_active_menu_tree(db)
        return _tree_to_dicts(tree)
    finally:
        db.close()


def _tree_to_dicts(nodes) -> list[dict]:
    """Convert MenuItemTreeNode Pydantic objects to plain dicts."""
    result = []
    for node in nodes:
        result.append({
            "id": node.id,
            "title": node.title,
            "url": node.url,
            "type": node.type,
            "children": _tree_to_dicts(node.children),
        })
    return result


# ── Health Check ─────────────────────────────────────────────────────────
@app.get("/health", include_in_schema=False)
def health():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ── Rate Limiter ─────────────────────────────────────────────────────────
class RateLimiter:
    """Простой in-memory rate limiter."""
    def __init__(self, max_requests=30, window_sec=60):
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

api_limiter = RateLimiter(max_requests=60, window_sec=60)  # 60 API запросов в минуту


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware for write API endpoints."""
    # Only rate-limit write operations on API routes
    if request.method in {"POST", "PUT", "DELETE", "PATCH"} and request.url.path.startswith("/api/"):
        client_ip = request.client.host if request.client else "unknown"
        if not api_limiter.check(f"api:{client_ip}:{request.url.path}"):
            return JSONResponse(
                {"error": "Слишком много запросов. Попробуйте позже."},
                status_code=429,
            )
    return await call_next(request)


# ── Routers ──────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(menu.router, prefix="/api")
app.include_router(page.router, prefix="/api")
app.include_router(public.router)
app.include_router(admin_tools.router)
app.include_router(users.router)


# ── Admin pages ───────────────────────────────────────────────────────────


@app.get("/admin", response_class=HTMLResponse, include_in_schema=False)
@app.get("/admin/", response_class=HTMLResponse, include_in_schema=False)
def admin_dashboard(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/", status_code=302)
    from app.database import SessionLocal
    from app.models import Page
    db = SessionLocal()
    try:
        pages = db.query(Page).order_by(Page.order).all()
    finally:
        db.close()
    return templates.TemplateResponse(request=request, name="admin/dashboard.html", context={"pages": pages})


@app.get("/admin/menu", response_class=HTMLResponse, include_in_schema=False)
def admin_menu_page(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/admin/menu", status_code=302)
    return templates.TemplateResponse(
        request=request, name="admin/menu.html"
    )


@app.get("/admin/media", response_class=HTMLResponse, include_in_schema=False)
def admin_media(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/media", status_code=302)
    from app.database import SessionLocal
    from app.models import MediaItem
    db = SessionLocal()
    try:
        items = db.query(MediaItem).order_by(MediaItem.created_at.desc()).all()
    finally:
        db.close()
    return templates.TemplateResponse(request=request, name="admin/media.html", context={"media_items": items})


@app.get("/admin/content", response_class=HTMLResponse, include_in_schema=False)
def admin_content(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/content", status_code=302)
    return templates.TemplateResponse(request=request, name="admin/content.html")


@app.get("/admin/settings-page", response_class=HTMLResponse, include_in_schema=False)
def admin_settings(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/settings", status_code=302)
    from app.database import SessionLocal
    from app.models import Setting
    db = SessionLocal()
    try:
        settings = db.query(Setting).order_by(Setting.key).all()
    finally:
        db.close()
    return templates.TemplateResponse(request=request, name="admin/settings.html", context={"settings": settings})


@app.get("/admin/roles-page", response_class=HTMLResponse, include_in_schema=False)
def admin_roles(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/admin/login?next=/roles", status_code=302)
    from app.database import SessionLocal
    from app.models import Role, User
    from app.services.users import get_users, get_roles
    db = SessionLocal()
    try:
        roles = get_roles(db)
        users = get_users(db)
    finally:
        db.close()
    return templates.TemplateResponse(request=request, name="admin/roles.html", context={"roles": roles, "users": users})


# ── SEO & Search ─────────────────────────────────────────────────────────
@app.get("/sitemap.xml", include_in_schema=False)
def sitemap():
    """Generate sitemap.xml from published pages."""
    import sqlite3
    import os
    # Database is in WorkingDirectory (/var/www/zolotarevka-fastapi)
    db_path = os.path.join(os.path.dirname(BASE_DIR), "site.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT slug, updated_at FROM pages WHERE is_published=1 ORDER BY slug"
        ).fetchall()
    finally:
        conn.close()

    base_url = "https://xn--80aaflivdxbvu.xn--p1ai"

    urls = [f"""  <url>
    <loc>{base_url}/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""]

    for r in rows:
        updated = str(r["updated_at"])[:10] if r["updated_at"] else ""
        urls.append(f"""  <url>
    <loc>{base_url}/{r['slug']}</loc>
    {"<lastmod>" + updated + "</lastmod>" if updated else ""}
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{chr(10).join(urls)}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


ROBOTS_TXT = """User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/

Sitemap: https://xn--80aaflivdxbvu.xn--p1ai/sitemap.xml
"""


@app.get("/robots.txt", include_in_schema=False)
def robots():
    return Response(content=ROBOTS_TXT, media_type="text/plain")


@app.get("/api/search", include_in_schema=False)
def api_search(q: str = "", limit: int = 10):
    """Full-text search API — returns JSON results."""
    if not q.strip():
        return []
    import sqlite3
    import os
    db_path = os.path.join(os.path.dirname(BASE_DIR), "site.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        limit = min(max(limit, 1), 50)
        rows = conn.execute(
            """SELECT p.id, p.slug, p.title,
                      snippet(pages_fts, 1, '<b>', '</b>', '...', 32) as snippet
               FROM pages_fts
               JOIN pages p ON p.slug = pages_fts.slug
               WHERE pages_fts MATCH ? AND p.is_published = 1
               ORDER BY rank
               LIMIT ?""",
            (q, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/search", response_class=HTMLResponse, include_in_schema=False)
def search_page(request: Request, q: str = ""):
    """Search results page — renders Jinja2 template."""
    results = []
    if q.strip():
        import sqlite3
        import os
        db_path = os.path.join(os.path.dirname(BASE_DIR), "site.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """SELECT p.id, p.slug, p.title,
                          snippet(pages_fts, 1, '<b>', '</b>', '...', 32) as snippet
                   FROM pages_fts
                   JOIN pages p ON p.slug = pages_fts.slug
                   WHERE pages_fts MATCH ? AND p.is_published = 1
                   ORDER BY rank
                   LIMIT 20""",
                (q,),
            ).fetchall()
            results = [dict(r) for r in rows]
        finally:
            conn.close()
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={"query": q, "results": results},
    )


# ── Public page routes (Jinja2) ──────────────────────────────────────────
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def web_index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"page_title": "Главная"},
    )


@app.get("/{slug:path}", response_class=HTMLResponse, include_in_schema=False)
def web_page(slug: str, request: Request):
    # Skip internal paths
    if slug.startswith("api/") or slug.startswith("static") or slug in ("admin/",):
        from fastapi.responses import JSONResponse
        return JSONResponse({"error": "Not found"}, status_code=404)

    slug = slug.rstrip("/").split("/")[-1]

    # Try to load page content from database
    from app.database import SessionLocal
    from app.models import Page as PageModel

    db = SessionLocal()
    try:
        page = db.query(PageModel).filter(PageModel.slug == slug, PageModel.is_published == True).first()
    finally:
        db.close()

    if page:
        return templates.TemplateResponse(
            request=request,
            name="page.html",
            context={
                "page_title": page.title,
                "slug": slug,
                "page_content": page.content,
            },
        )

    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={
            "page_title": slug.capitalize(),
            "slug": slug,
            "page_content": "",
        },
    )


# ── Catch-all for non-GET methods on unknown paths ───────────────────────
# Without this, POST/PUT/DELETE to e.g. /login returns 405 (from the
# catch-all GET route matching the path pattern). We want 404 instead.
from fastapi.responses import JSONResponse as _JsonResponse


@app.api_route("/{path:path}", methods=["POST", "PUT", "DELETE", "PATCH"], include_in_schema=False)
def method_not_allowed_fallback(path: str, request: Request):
    return _JsonResponse({"error": "Not found"}, status_code=404)
