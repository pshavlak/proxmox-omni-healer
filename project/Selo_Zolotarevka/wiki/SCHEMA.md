---
title: Schema
updated: 2026-07-10
type: concept
tags: [fastapi, sqlite, api, architecture]
---

# Архитектура сайта Золотаревка

## Стек

- **Backend**: FastAPI (Python 3.9+)
- **Database**: SQLite (WAL mode, FTS5 для поиска)
- **Templates**: Jinja2 (серверный рендеринг)
- **Admin**: SPA (HTML + CSS + JS, без фреймворков)
- **Auth**: Cookie-based сессии с bcrypt
- **Rate Limiting**: In-memory (словарь defaultdict)

## Структура проекта

```
site/
  app.py              # FastAPI приложение (все роутеры)
  config.py           # Конфигурация (пути, лимиты)
  database.py         # SQLite: инициализация, миграции, seed
  models.py           # Pydantic модели
  models/__init__.py  # Альтернативные модели
  start.sh            # Script запуска
  install.sh          # Установка зависимостей
  requirements.txt    # Python зависимости
  zolotarevka.db      # SQLite база данных (создаётся автоматически)

  admin/              # SPA админ-панель
    index.html
    css/admin.css
    js/admin.js, api.js

  static/
    css/style.css     # Основной стиль сайта
    js/main.js        # Основной JavaScript
    uploads/          # Загруженные файлы

  templates/
    base.html         # Базовый шаблон
    index.html        # Главная страница
    page.html         # Страница с блоками
    login.html        # Страница входа
    search.html       # Страница поиска
    blocks/           # Шаблоны блоков (hero, text, image, и т.д.)
    errors/           # 404.html
    partials/         # header.html, footer.html, top_bar.html, suggest_modal.html

  server_routers/     # Legacy роутеры (серверная копия)
  server_main.py      # Legacy main (серверная копия)

deploy/
  backup.sh           # Резервное копирование
  check_db.sh         # Мониторинг SQLite
  healthcheck.sh      # Health check скрипт
  telegram-alert.sh   # Telegram уведомления
  setup-ufw.sh        # Настройка UFW
  nginx-zolotarevka.conf
  ssl/                # SSL конфиги
  vps/                # VPS: nginx + systemd

Makefile              # Автоматизация деплоя
RECOMMENDATION_PLAN.md # План развития
SECURITY_AUDIT.md     # Аудит безопасности
```

## База данных

| Таблица | Назначение |
|---------|-----------|
| pages | Страницы (id, name, icon, parent, sort_order, status) |
| blocks | Блоки контента (id, page_id, type, config JSON) |
| blocks_history | История версий блоков (block_id, config_snapshot, user_id) |
| roles | Роли пользователей (sections, caps) |
| users | Пользователи (username, password_hash bcrypt, role) |
| sessions | Сессии (token, user_id, expires_at) |
| settings | Настройки сайта (key-value) |
| media | Медиа-файлы (filename, original_name, mime_type, size) |
| suggestions | Предложенные новости (name, email, category, text, status) |
| menu_groups | Группы меню |
| menu_group_items | Страницы в группах меню |
| captcha_config | Настройки Cloudflare Turnstile |

## API Endpoints

### Публичные (без аутентификации)
| Method | Path | Описание |
|--------|------|----------|
| GET | / | Главная страница |
| GET | /{slug} | Страница по slug |
| GET | /health | Health check |
| GET | /login | Страница входа |
| GET | /api/content/pages | Публичные страницы (дерево) |
| GET | /api/content/recent | Последние обновления |
| GET | /api/content/random-media | Случайное медиа |
| GET | /api/captcha/config | Turnstile site key |
| POST | /api/suggest | Отправить новость |
| POST | /api/feedback | Обратная связь |

### Админ-API (требуется сессия)
| Method | Path | Описание |
|--------|------|----------|
| GET/POST | /api/pages | CRUD страниц |
| PUT/DELETE | /api/pages/{id} | Обновление/удаление страницы |
| GET | /api/pages/{id}/blocks | Блоки страницы |
| PUT | /api/pages/{id}/blocks | Сохранение блоков |
| GET | /api/blocks/{id}/history | История версий блока |
| POST | /api/blocks/{id}/restore/{v} | Восстановление версии |
| POST | /api/blocks/{id}/move | Перемещение блока |
| GET/POST | /api/roles | CRUD ролей |
| GET/POST | /api/users | Управление пользователями |
| GET/PUT | /api/settings | Настройки сайта |
| GET/POST/DELETE | /api/media | Медиа-файлы |
| POST | /api/media/upload-multiple | Загрузка нескольких файлов |
| GET | /api/suggestions | Предложенные новости |

## Фазы разработки

- **Фаза 1** ✅ — Безопасность (HTTPS, UFW, rate limiting, health check)
- **Фаза 2** ✅ — Функционал (поиск, sitemap, кеш, версионирование, CAPTCHA, виджеты)
- **Фаза 3** ✅ — Дизайн (адаптивность, шрифт Inter, микроанимации, 404)
- **Фаза 4** 🔄 — Автоматизация (бэкап, мониторинг, Makefile, документация)
