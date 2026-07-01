# 🔐 Security Audit Report — Zolotarevka Site
**Date:** 2026-07-01  
**Auditor:** Hermes Agent  
**Scope:** FastAPI + SQLite + Jinja2 + SPA Admin Panel

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 Critical | 5 |
| 🟠 High | 5 |
| 🟡 Medium | 9 |
| 🟢 Low | 6 |
| **Total** | **25** |

---

## 🔴 CRITICAL

### C1. No Role-Based Access Control (RBAC) on Admin APIs
**Files:** `app.py` (middleware L89-124), all `/api/*` handlers  
**Risk:** ⚠️ Any authenticated user can perform all admin operations  

The auth middleware only checks **presence** of a valid session — it never checks `user.role`. All admin API endpoints (create/update/delete pages, blocks, roles, settings, media, suggestions) are accessible to ANY logged-in user. Only `api_create_user` (L479) and `api_delete_user` (L508) verify `current["role"] != "admin"`.

**Fix:** Add role-checking middleware or FastAPI dependency that ensures `user.role == 'admin'` for all write operations.

### C2. Rate Limiting Defined But Not Implemented
**Files:** `config.py` (L24-25), `app.py` `/api/suggest` (L639-648), `/login` (L143-183)  
**Risk:** ⚠️ Unrestricted brute-force and spam  

`SUGGEST_RATE_LIMIT = 5` and `SUGGEST_RATE_WINDOW = 600` are defined in config but **never referenced** in `app.py`. Both the suggest form and login endpoint accept unlimited requests.

**Fix:** Implement rate limiting (slowapi, Redis-based, or in-memory dict with timestamps).

### C3. SHA256 Password Hashing Without Salt
**Files:** `app.py` (L149, L491, L531, L541), `database.py` (L258)  
**Risk:** ⚠️ Instant password cracking on DB leak  

```python
pw_hash = hashlib.sha256(password.encode()).hexdigest()
```
No salt, no key stretching. Default password `admin123` is recoverable in milliseconds. Minimum password length is only 4 characters (L483).

**Fix:** Use `bcrypt` or `argon2-cffi`. Set minimum password length to 8+.

### C4. Dynamic Column Name in SQL UPDATE
**File:** `app.py` (L268)  
**Risk:** ⚠️ SQL injection via column name (partially mitigated by Pydantic)  

```python
conn.execute(f"UPDATE pages SET {k} = ? WHERE id = ?", (v, page_id))
```
Keys come from `PageUpdate` Pydantic model fields only, but dynamic column interpolation is an anti-pattern.

**Fix:** Build column list explicitly from a whitelist.

### C5. No CSRF Protection Anywhere
**Files:** All forms, all API endpoints  
**Risk:** ⚠️ Cross-Site Request Forgery on state-changing operations  

- No CSRF tokens  
- No Origin/Referer validation  
- `SameSite=Lax` on session cookie partially mitigates (POST/PUT/DELETE from external sites blocked, but GET is vulnerable)  
- CORS `allow_origins=["*"]` with `allow_credentials=True` violates CORS spec

**Fix:** Add CSRF middleware (e.g., `starlette-csrf`). Validate Origin/Referer headers.

---

## 🟠 HIGH

### H1. `/api/feedback` Endpoint Doesn't Exist
**Files:** `templates/blocks/form.html` (L38 → submits to `/api/feedback`), `app.py` (no route)  
**Risk:** Broken functionality + confusion  
The feedback form posts to `/api/feedback` which has no route handler in `app.py` and is not in `PUBLIC_API_PREFIXES`. Users get 401 or 404.

**Fix:** Implement the route or remove the form option.

### H2. Template Path Traversal via `block.type`
**Files:** `templates/index.html` (L7), `templates/page.html` (L56), `app.py` (L331)  
**Risk:** Limited path traversal in Jinja2 template loader  

```jinja2
{% include 'blocks/' + block.type + '.html' ignore missing %}
```
`block.type` is stored with NO validation (L331: `btype = b.get("type", "text")` with no allowed-list check). The `ignore missing` modifier limits impact, but traversal into other template paths is possible.

**Fix:** Validate `block.type` against the database CHECK constraint list.

### H3. Stored XSS via Block Config Content (HTML mode)
**File:** `templates/blocks/text.html` (L3)  
**Risk:** XSS on all site visitors  

```jinja2
{{ block.config.content|safe }}
```
The `|safe` filter renders raw HTML. Any admin can inject `<script>` tags via the text block editor. While "by design", this is a stored XSS vector.

**Fix:** Document as risk, enforce DOMPurify on frontend, consider rendering through a sandboxed iframe.

### H4. Stored XSS via `javascript:` URIs in Gallery
**File:** `templates/blocks/gallery.html` (L7-8)  
**Risk:** Click-based XSS  

```html
<a href="{{ image.src }}" ...>
```
Jinja2 autoescape does NOT filter `javascript:` protocol in href attributes.

**Fix:** Validate URLs in block config (must start with `http://`, `https://`, or `/`). Strip `javascript:` scheme.

### H5. DOM XSS in Admin SPA — Unescaped `page.icon` and User Fields
**File:** `admin/js/admin.js`  
- `renderTree()` (L87): `page.icon` interpolated without `escapeHtml()`  
- `loadUsers()` (L992): `u.id`, `u.username`, `u.role` interpolated without `escapeHtml()`  
- `renderRoles()` (L796): `role.icon` interpolated without `escapeHtml()`  

**Fix:** Wrap ALL dynamic values in `escapeHtml()` when using `innerHTML`.

---

## 🟡 MEDIUM

### M1. Session Cookie `secure=False`
**File:** `app.py` (L181). Cookie sent over HTTP. With Cloudflare proxy, HTTPS terminates at Cloudflare edge. Cookie could be intercepted on internal network.

### M2. No Expired Session Cleanup
Sessions never cleaned up (no cron job). Growing DB table over time.

### M3. Minimum Password Length = 4 Characters
**File:** `app.py` (L483). Combined with SHA256, trivially brute-forced.

### M4. Upload: No Content-Type Validation
**File:** `app.py` (L596-598). Only checks file extension, not file magic bytes. `.jpg` with malicious payload accepted.

### M5. Uploaded Files Served Without MIME Restrictions
StaticFiles serves everything from `/static/uploads/`. HTML files with JS execute in site origin.

### M6. Uvicorn Binds to 0.0.0.0 in Dev Mode
**File:** `app.py` (L799). FastAPI accessible on all interfaces, bypassing nginx reverse proxy.

### M7. No `limit` Bounds on `/api/content/recent`
**File:** `app.py` (L672). `limit: int = 6` with no `max` constraint. DoS via `?limit=1000000`.

### M8. Error Messages Reveal Internals
API returns descriptive messages: "Страница с ID 'X' уже существует", "Роль не найдена", "Файл не найден". Helps attacker enumerate valid IDs.

### M9. Multiple `innerHTML` Injection Points Without Escape in Admin SPA
Additional spots in `admin/js/admin.js`:
- `renderRoles()` role icon (L796)  
- `loadUsers()` user fields (L992)  
- Various others  

---

## 🟢 LOW

### L1. Nginx: `server_tokens` Not Disabled
**File:** `deploy/nginx-zolotarevka.conf`. Version disclosed in Server headers.

### L2. Nginx: No Security Headers
Missing: `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`, `Strict-Transport-Security`, `Referrer-Policy`.

### L3. Default `SECRET_KEY` Hardcoded
**File:** `app.py` (L22). Falls back to `"zolotarevka-secret-change-me-in-prod"` if env var not set.

### L4. Misleading Comment in Config
**File:** `config.py` (L27): `# Админ-панель (без пароля на MVP)`. Admin panel DOES have a password. Comment is confusing.

### L5. Seed Debug Output
**File:** `database.py` (L263): `print("✅ Admin user created (admin / admin123)")` — leaks default credentials to stdout.

### L6. No Session TTL Refresh on Activity
24-hour fixed TTL, never extended by user activity.

---

## Recommended Immediate Actions

| # | Action | Severity | Effort |
|---|--------|----------|--------|
| 1 | Add RBAC to middleware — verify `user.role == 'admin'` for all admin APIs | 🔴 Critical | 1-2h |
| 2 | Implement rate limiting on `/api/suggest` and `/login` | 🔴 Critical | 1-2h |
| 3 | Replace SHA256 with bcrypt for password hashing | 🔴 Critical | 1-2h |
| 4 | Add CSRF protection | 🔴 Critical | 2-4h |
| 5 | Fix `/api/feedback` or remove the form option | 🟠 High | 0.5h |
| 6 | Escape all user data in admin SPA (`escapeHtml`) | 🟠 High | 1h |
| 7 | Validate `javascript:` scheme in block URLs | 🟠 High | 0.5h |
| 8 | Validate `block.type` against allowed values | 🟠 High | 0.5h |
| 9 | Add security headers to nginx config | 🟡 Medium | 0.5h |
| 10 | Add `server_tokens off` to nginx | 🟡 Medium | 0.5h |

---

*Report generated by Hermes Agent — full code audit of `/Users/phavlak/Documents/project/Selo_Zolotarevka/site/`*
