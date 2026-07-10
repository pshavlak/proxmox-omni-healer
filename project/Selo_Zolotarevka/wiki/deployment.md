# Фаза 1: Базовая безопасность и стабильность (✅ Выполнено 10.07.2026)

## 1.1 HTTPS/SSL
- **На VPS**: Let's Encrypt (ECDSA), сертификат действителен до 29.09.2026
- Добавлен **HSTS** (max-age=31536000; includeSubDomains; preload)
- Добавлен **OCSP Stapling** (предупреждение — нет OCSP responder в сертификате, игнорируется)
- HTTP → HTTPS редирект (через nginx)
- Security headers: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, Permissions-Policy

## 1.2 UFW (Фаервол)
- Установлен `ufw` на LXC wordpress
- Разрешены порты: 22/tcp (SSH), 80/tcp (HTTP), 443/tcp (HTTPS)
- Дефолт: deny incoming, allow outgoing
- Скрипт: `deploy/setup-ufw.sh`

## 1.3 Health Check
- Эндпоинт `GET /health` → `{"status": "ok", "timestamp": "..."}`
- Скрипт мониторинга: `deploy/healthcheck.sh` (проверяет /health, /, /admin/, /api/pages)
- Telegram алерты: `deploy/telegram-alert.sh`

## 1.4 Rate Limiting
- Глобальный middleware: 60 POST/PUT/DELETE/PATCH запросов/мин к `/api/`
- In-memory `RateLimiter` класс (чистка устаревших записей)

## 1.5 Debug Mode
- Переменная окружения `DEBUG=false` в `/etc/zolotarevka/env`
- Uvicorn reload только при DEBUG=true

## 1.6 Кеширование
- nginx: static/ — 7d, uploads/ — 30d
- Прокси-кеш для публичных страниц (1 час, bypass по cookie session)

# Фаза 2: Улучшение функционала (✅ Частично выполнено 10.07.2026)

## 2.1 Полнотекстовый поиск (FTS5) ✅
- Виртуальная таблица `pages_fts` с триггерами синхронизации
- Эндпоинт `GET /api/search?q=...` (JSON)
- Страница `GET /search?q=...` (Jinja2 шаблон)
- Поиск: `unicode61` токенайзер, подсветка результатов через `snippet()`

## 2.2 Sitemap & Robots ✅
- `GET /sitemap.xml` — динамический XML со всеми published страницами
- `GET /robots.txt` — с Disallow для /admin/ и /api/
- `<link rel="sitemap">` в base.html

## 2.3 Форма поиска в шапке ✅
- Поле поиска в `partials/header.html`
- Отправляет GET /search?q=...

## 2.4-2.7 ❌ Не выполнены
- Версионирование блоков
- CAPTCHA (Cloudflare Turnstile)
- Множественная загрузка файлов
- Виджеты на главной

# Структура сервера

## LXC wordpress (192.168.1.64)
- FastAPI: `/var/www/zolotarevka-fastapi/`
- База: `site.db` (SQLite)
- systemd: `zolotarevka-fastapi.service`
- Запуск: uvicorn app.main:app --host 0.0.0.0 --port 8000

## VPS (31.56.208.248)
- Nginx reverse proxy: `xn--80aaflivdxbvu.xn--p1ai` → 127.0.0.1:8000
- Cloudflare поверх
- WordPress legacy: `zolotarevka.yupiterpro.ru` → 127.0.0.1:8080 (через reverse tunnel)

# Следующие шаги
1. Версионирование блоков (history)
2. CAPTCHA Cloudflare Turnstile
3. Множественная загрузка медиа
4. Виджеты на главной
