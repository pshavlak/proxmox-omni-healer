# Change Log

## 2026-07-10 — Фаза 4: Автоматизация (бэкап, мониторинг, Makefile, документация)
### Добавлено
- **Резервное копирование** — `deploy/backup.sh`
  - Бэкап SQLite (с VACUUM) + uploads + конфиги
  - Архивация в tar.gz, хранение 30 дней
  - Telegram уведомления
- **Мониторинг SQLite** — `deploy/check_db.sh`
  - Проверка размера (предупреждение 300MB, VACUUM 500MB)
  - Проверка целостности (PRAGMA integrity_check)
  - Статистика по таблицам
  - Мониторинг WAL файла
- **Makefile** — полная автоматизация
  - `make deploy` — rsync на сервер
  - `make restart` — systemctl restart
  - `make deploy-full` — файлы + перезапуск
  - `make backup / check-db / test / logs / clean`
- **Обновление документации**
  - `wiki/SCHEMA.md` — полная архитектура, таблицы, эндпоинты, фазы
  - `wiki/deployment.md` — гайд по деплою с Makefile
  - `CHANGELOG.md` — создан

## 2026-07-10 — Фаза 3: Дизайн и UX (адаптивность, шрифт, hero, микроанимации, 404)
### Добавлено
- Off-canvas мобильное меню (выезжает слева, overlay)
- Google Fonts Inter (700, 800, 900)
- Параллакс на hero (background-attachment: fixed)
- Анимация heroFadeIn + пульсация кнопки
- Микроанимации для соц-иконок и карточек
- Форма поиска на странице 404
- animate-on-scroll классы в блоках text, image, form

### Изменено
- Рефакторинг CSS: удалены дублирующиеся классы (.bento-grid, .news-section, .news-grid)
- Шаблон index.html переведён на .bento__grid
- Мобильное меню: закрытие по Escape, клик по overlay, при resize
- Hero min-height: 320px / 260px на мобильных

## 2026-07-10 — Фаза 2: Версионирование, CAPTCHA, загрузка, виджеты
### Добавлено
- **Версионирование блоков** — таблица `blocks_history`, история изменений
  - `GET /api/blocks/{block_id}/history` — получить историю
  - `POST /api/blocks/{block_id}/restore/{version_id}` — восстановить версию
  - Авто-сохранение текущей версии при перезаписи блоков страницы
- **Cloudflare Turnstile CAPTCHA** — бесплатная защита от ботов
  - Виджет в форме "Предложить новость" (`suggest_modal.html`)
  - Виджет в блочной форме (`form.html`)
  - Эндпоинт `/api/captcha/config` — получение site key
  - Эндпоинт `/api/captcha/verify` — проверка токена
  - Настройка через `captcha_config` таблицу (turnstile_site_key, turnstile_secret_key)
- **Множественная загрузка файлов**
  - `/api/media/upload-multiple` — загрузка до 20 файлов за раз
  - `/api/media/upload` — сохранён для совместимости
  - Уникальные имена через MD5 хеш
- **Виджеты на главной (динамическая подгрузка)**
  - `GET /api/content/random-media` — случайное фото/видео
  - Виджет "Случайное фото" на главной (AJAX)
  - Виджет "Последние новости" (динамическая замена через AJAX)

### Изменено
- `database.py` — добавлены таблицы `blocks_history`, `captcha_config`, функция `migrate_db()`
- `app.py` — добавлены эндпоинты истории, CAPTCHA, множественной загрузки, виджетов
- `requirements.txt` — добавлен `httpx>=0.27.0`
- `base.html` — подключён Cloudflare Turnstile API скрипт
- `suggest_modal.html` — Turnstile виджет, обработка в JS
- `form.html` — Turnstile виджет в форму
- `index.html` — секция случайного фото
- `main.js` — динамические виджеты (random-media, recent news)
- `style.css` — стили для random-media-widget, cf-turnstile

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
