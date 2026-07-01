# Сайт села Золотаревка

Актуальная версия проекта: FastAPI + SQLite + Jinja2 + SPA-админка.

## Структура

- `site/` — приложение для переноса на сервер.
- `site/admin/` — админ-панель.
- `site/templates/` — публичный сайт.
- `site/static/` — CSS, JS, uploads.
- `deploy/` — инструкции, systemd unit и nginx config.
- `wiki/` — актуальная проектная вики.
- `archive/2026-06-26-legacy/` — WordPress legacy, sketches, старые документы и сгенерированные локальные файлы.

## Локальный запуск

```bash
cd site
chmod +x install.sh start.sh
./install.sh
PORT=8000 ./start.sh
```

Адреса:

- сайт: `http://127.0.0.1:8000/`
- админка: `http://127.0.0.1:8000/admin/`
- API: `http://127.0.0.1:8000/api/pages`

## Деплой

См. `deploy/README_DEPLOY.md`.
