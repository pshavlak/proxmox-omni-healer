# Change Log

## 2026-07-10 — Фазы 1-2: Безопасность + Поиск
### Добавлено
- `/health` endpoint для мониторинга
- **Rate limiting** middleware (60 запросов/мин на write API)
- **HSTS + OCSP Stapling** на nginx
- **UFW** на LXC (22,80,443)
- **nginx кеширование** (static: 7d, uploads: 30d)
- **FTS5 полнотекстовый поиск** (`/api/search`, `/search`)
- **Sitemap.xml** (динамический) + **Robots.txt**
- Форма поиска в шапке сайта
- Debug mode через `DEBUG=false` env

### Изменено
- `app/main.py` — реструктуризация, добавлены SEO-маршруты до catch-all
- `partials/header.html` — добавлена форма поиска
- `base.html` — добавлен `<link rel="sitemap">`
- `/etc/zolotarevka/env` — добавлен `DEBUG=false`

### Структура deploy/
```
deploy/
  healthcheck.sh         # Скрипт мониторинга
  setup-ufw.sh           # Настройка фаервола
  telegram-alert.sh      # Telegram алерты
  ssl/
    setup-ssl.sh         # Выпуск SSL сертификата
    nginx-ssl.conf       # Nginx конфиг с HTTPS
  vps/
    nginx/zolotarevka-ssl.conf  # Актуальный nginx с VPS
    systemd/zolotarevka-fastapi.service  # systemd unit
```

## 2026-07-05 — Миграция на модульную архитектуру
- Переход с монолитного `app.py` на пакетную структуру `app/`
- SQLAlchemy ORM вместо raw SQLite
- Jinja2Templates вместо самописного render
- SessionMiddleware вместо самодельной cookie-аутентификации
- Роутеры: auth, menu, page, public, admin_tools, users
- Сервисы: auth, media, menu, page, users

## 2026-06-28 — Первоначальный запуск
- FastAPI приложение на LXC wordpress
- Nginx reverse proxy на VPS
- Let's Encrypt SSL сертификат
- Cloudflare прокси
