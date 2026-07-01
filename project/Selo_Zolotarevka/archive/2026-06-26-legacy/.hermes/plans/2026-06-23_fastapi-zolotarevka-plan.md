# 🌾 Золотаревка — FastAPI Сайт с Админ-Панелью

> **Goal:** Создать динамический сайт села Золотаревка, управляемый из админ-панели (на основе `site-builder-v2.html`).  
> **Архитектура:** FastAPI бэкенд + SQLite БД + Jinja2 шаблоны + админ-панель на чистом HTML/CSS/JS.  
> **Стек:** Python 3.11+, FastAPI, SQLite (aiosqlite), Jinja2, uvicorn, nginx (прокси).  
> **Дирректория:** `/Users/phavlak/Documents/project/Selo_Zolotarevka/`

---

## 🗂️ Структура проекта

```
site/
├── app.py                  # FastAPI приложение (запуск)
├── config.py               # Настройки (пути, секреты)
├── database.py             # SQLite инициализация + миграции
│
├── models/                 # Pydantic модели
│   ├── __init__.py
│   ├── page.py             # Page, PageBlock
│   ├── role.py             # Role, RoleCaps
│   └── settings.py         # SiteSettings
│
├── api/                    # FastAPI роутеры
│   ├── __init__.py
│   ├── pages.py            # /api/pages - CRUD страниц
│   ├── blocks.py           # /api/blocks - CRUD блоков
│   ├── roles.py            # /api/roles - CRUD ролей
│   ├── media.py            # /api/media - загрузка/список файлов
│   ├── settings.py         # /api/settings - настройки сайта
│   ├── gallery.py          # /api/gallery - галерея
│   ├── videos.py           # /api/videos - видео
│   └── content.py          # /api/content - публичные данные для сайта
│
├── web/                    # FastAPI роутеры — публичный сайт
│   ├── __init__.py
│   └── routes.py           # GET /, /{slug} — рендер страниц
│
├── templates/              # Jinja2 шаблоны
│   ├── base.html           # Базовый шаблон (head, header, nav, footer)
│   ├── index.html          # Главная страница
│   ├── page.html           # Обычная страница
│   ├── blocks/             # Рендеры блоков
│   │   ├── hero.html
│   │   ├── text.html
│   │   ├── image.html
│   │   ├── gallery.html
│   │   ├── video.html
│   │   ├── table.html
│   │   ├── cards.html
│   │   ├── documents.html
│   │   ├── form.html
│   │   └── divider.html
│   ├── partials/           # Переиспользуемые части
│   │   ├── header.html     # Шапка + навигация (из БД)
│   │   ├── footer.html     # Подвал
│   │   ├── top_bar.html    # Верхняя панель
│   │   └── suggest_modal.html
│   └── errors/
│       └── 404.html
│
├── static/                 # Статические файлы
│   ├── css/
│   │   └── style.css       # Стили сайта (из site/css/style.css)
│   ├── js/
│   │   └── main.js         # JS сайта (из site/js/main.js)
│   └── uploads/            # Загруженные файлы (фото, документы)
│       └── .gitkeep
│
├── admin/                  # Админ-панель (статическая SPA)
│   ├── index.html          # Админ-панель (переработанный site-builder-v2.html)
│   ├── css/
│   │   └── admin.css       # Стили админки
│   └── js/
│       └── admin.js        # JS админки с API-вызовами
│
└── scripts/                # Скрипты
    └── seed.py             # Первичное наполнение БД
```

---

## 🗄️ База данных (SQLite)

### Таблица `pages`
```sql
CREATE TABLE pages (
    id          TEXT PRIMARY KEY,    -- slug: 'home', 'school', 'school-news'
    name        TEXT NOT NULL,       -- Отображаемое имя
    icon        TEXT DEFAULT '📄',  -- Эмодзи-иконка
    parent      TEXT REFERENCES pages(id) ON DELETE CASCADE,
    sort_order  INTEGER DEFAULT 99,
    status      TEXT DEFAULT 'draft' CHECK(status IN ('draft','published')),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `blocks`
```sql
CREATE TABLE blocks (
    id          TEXT PRIMARY KEY,    -- 'b1', 'hero-home'
    page_id     TEXT NOT NULL REFERENCES pages(id) ON DELETE CASCADE,
    type        TEXT NOT NULL CHECK(type IN ('hero','text','image','gallery','video','table','cards','documents','form','divider')),
    name        TEXT DEFAULT 'Блок',
    sort_order  INTEGER DEFAULT 0,
    config      TEXT DEFAULT '{}',  -- JSON с конфигурацией блока
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `roles`
```sql
CREATE TABLE roles (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    icon        TEXT DEFAULT '🛡️',
    sections    TEXT DEFAULT '[]',  -- JSON: ['school', 'sports'] или '"__all__"'
    caps        TEXT DEFAULT '{}',  -- JSON: {"moderation":false,"upload":true,"publish":true}
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Таблица `settings`
```sql
CREATE TABLE settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL            -- JSON value
);
```

### Таблица `media`
```sql
CREATE TABLE media (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    filename    TEXT NOT NULL,
    original_name TEXT NOT NULL,
    mime_type   TEXT NOT NULL,
    size        INTEGER NOT NULL,
    alt_text    TEXT DEFAULT '',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 📡 API Эндпоинты

### Админские (с префиксом `/api`)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/api/pages` | Список всех страниц |
| POST | `/api/pages` | Создать страницу |
| PUT | `/api/pages/{id}` | Обновить страницу |
| DELETE | `/api/pages/{id}` | Удалить страницу (с каскадом блоков и детей) |
| PUT | `/api/pages/reorder` | Массовое обновление порядка |
| GET | `/api/pages/{id}/blocks` | Блоки страницы |
| PUT | `/api/pages/{id}/blocks` | Сохранить все блоки страницы |
| POST | `/api/blocks/{id}/move` | Переместить блок (вверх/вниз) |
| GET | `/api/roles` | Список ролей |
| POST | `/api/roles` | Создать роль |
| PUT | `/api/roles/{id}` | Обновить роль |
| DELETE | `/api/roles/{id}` | Удалить роль |
| GET | `/api/settings` | Все настройки сайта |
| PUT | `/api/settings` | Обновить настройки |
| GET | `/api/media` | Список медиа-файлов |
| POST | `/api/media/upload` | Загрузить файл |
| DELETE | `/api/media/{id}` | Удалить файл |
| GET | `/api/gallery` | Элементы галереи |
| POST | `/api/gallery` | Добавить элемент |
| DELETE | `/api/gallery/{id}` | Удалить элемент |
| GET | `/api/videos` | Список видео |
| POST | `/api/videos` | Добавить видео |
| PUT | `/api/videos/{id}` | Обновить видео |
| DELETE | `/api/videos/{id}` | Удалить видео |

### Публичные (без префикса)

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/` | Главная страница (HTML) |
| GET | `/{slug}` | Страница раздела (HTML) |
| GET | `/api/content/pages` | Публичные страницы (для навигации) |
| GET | `/api/content/recent` | Последние публикации (для виджетов) |

---

## 🧩 Фазы разработки

---

### Phase 1: Инфраструктура проекта
**Цель:** Создать скелет приложения, БД, модели данных.

**Task 1.1: Инициализация проекта**
- Создать `app.py` с FastAPI приложением
- Настроить CORS (для админки)
- Подключить Jinja2 templates
- Подключить статические файлы
- Создать `config.py`

**Task 1.2: База данных**
- Создать `database.py` с SQLite инициализацией
- Создать все таблицы (pages, blocks, roles, settings, media)
- Создать seed-данные из `site-builder-v2.html` (17 страниц + начальные блоки + роли)

**Task 1.3: Pydantic модели**
- `Page`: id, name, icon, parent, sort_order, status
- `Block`: id, page_id, type, name, sort_order, config
- `Role`: id, name, icon, sections, caps
- `SiteSettings` — все настройки сайта

---

### Phase 2: API эндпоинты
**Цель:** Полный CRUD для админ-панели.

**Task 2.1: API страниц**
- GET/POST/PUT/DELETE для `/api/pages`
- Каскадное удаление детей и блоков
- Перестановка порядка (reorder)

**Task 2.2: API блоков**
- GET/PUT для `/api/pages/{id}/blocks`
- POST `/api/blocks/{id}/move` — перемещение
- Валидация config под каждый тип блока

**Task 2.3: API ролей**
- Полный CRUD для `/api/roles`
- Подсчёт пользователей в роли

**Task 2.4: API настроек**
- GET/PUT `/api/settings`
- Настройки: site_name, site_description, logo, header_bg, footer_bg, hero_image, social_links, contacts

**Task 2.5: API медиа**
- Загрузка файлов (POST `/api/media/upload`)
- Список файлов
- Удаление
- Валидация типов (jpg, png, gif, webp, pdf, doc)

---

### Phase 3: Админ-панель (фронтенд)
**Цель:** Оживить `site-builder-v2.html` — вместо in-memory данных — вызовы API.

**Task 3.1: API-клиент для админки**
- Создать `admin/js/api.js` с функциями:
  - `api.getPages()`, `api.savePages()`, `api.deletePage(id)`
  - `api.getBlocks(pageId)`, `api.saveBlocks(pageId, blocks)`
  - `api.getRoles()`, `api.createRole()`, `api.deleteRole(id)`
  - `api.getSettings()`, `api.saveSettings(settings)`
  - `api.uploadFile(file)`, `api.getMedia()`
- Использовать `fetch()` с JSON

**Task 3.2: Переписать `site-builder-v2.html` в `admin/index.html`**
- Взять весь HTML/CSS из прототипа
- Разделить: HTML → `admin/index.html`, CSS → `admin/css/admin.css`, JS → `admin/js/admin.js`
- JS переписать: вместо `const pages = [...]` → `let pages = await api.getPages()`
- Все `toast()` и рендеры остаются, но данные из API

**Task 3.3: Добавить настройки сайта в админку**
- Новая вкладка/кнопка «⚙️ Настройки сайта»
- Модалка с полями:
  - Название сайта, описание
  - Логотип (загрузка файла)
  - Цвета темы (primary, accent, header_bg, footer_bg)
  - Фоновое изображение шапки
  - Social ссылки (VK, Telegram, OK, RSS)
  - Контакты (email, phone)
  - Hero-настройки (текст, фон)

**Task 3.4: Медиа-галерея в админке**
- Вкладка/кнопка «🖼️ Медиа»
- Сетка загруженных изображений
- Drag & drop загрузка
- Выбор изображения для блоков

---

### Phase 4: Публичный сайт (Jinja2 шаблоны)
**Цель:** Сайт рендерится из БД через Jinja2.

**Task 4.1: Базовый шаблон**
- `templates/base.html` — DOCTYPE, head, meta, CSS, header, nav, footer
- Навигация строится из БД (страницы с parent=null)
- Header из настроек (лого, название, фон)
- Footer из настроек

**Task 4.2: Блок-рендеры**
Каждый тип блока — отдечный паршл:
- `hero.html` — баннер с фоном, заголовком, подзаголовком, кнопкой
- `text.html` — HTML-контент с typography
- `image.html` — изображение с подписью
- `gallery.html` — сетка изображений с lightbox
- `video.html` — Rutube/VK embed
- `table.html` — таблица
- `cards.html` — карточки/плитки (включая auto_from_tree — авто из структуры сайта)
- `documents.html` — список документов со ссылками
- `form.html` — форма (предложить новость / обратная связь)
- `divider.html` — разделитель

**Task 4.3: Главная страница**
- `templates/index.html` — наследует `base.html`
- Hero-блок
- Bento-сетка разделов (генерится из страниц первого уровня)
- Виджет матча (тестовые данные пока нет матчей)
- Лента последних новостей
- CTA «Предложить новость»
- Все динамически из БД

**Task 4.4: Страницы разделов**
- `templates/page.html` — универсальный шаблон
- Breadcrumbs из структуры
- Заголовок + иконка
- Рендер блоков по порядку
- Комментарии (заглушка/формы)
- Боковая навигация по подразделам (если есть дети)

**Task 4.5: 404 страница**
- Кастомная 404 с ссылками на основные разделы

---

### Phase 5: Медиа, Навигация, Формы
**Цель:** Функциональность для живого сайта.

**Task 5.1: Загрузка и управление медиа**
- Эндпоинт `/api/media/upload` — принимает файл, сохраняет в `static/uploads/`
- Возвращает URL для вставки в блоки
- Галерея с предпросмотром в админке
- Управление файлами (удаление)

**Task 5.2: Динамическая навигация**
- Мега-меню генерится из структуры страниц
- `groups = {"Организации": ["school","kindergarten","farm"], "Спорт": ["sports"], ...}`
- Группы настраиваются в настройках сайта
- Footer генерится из той же структуры

**Task 5.3: Форма «Предложить новость»**
- POST `/api/suggest` — принимает имя, email, категорию, текст
- Сохраняет в pending-статус
- Возвращает подтверждение
- Rate limiting (5 запросов / 10 минут)

**Task 5.4: Форма обратной связи**
- POST `/api/feedback`

---

### Phase 6: Запуск и деплой
**Цель:** Подготовить к запуску на Proxmox.

**Task 6.1: Dockerfile**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Task 6.2: nginx конфигурация**
```nginx
server {
    listen 80;
    server_name zolotarevka.ru;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /static/ {
        alias /opt/zolotarevka/static/;
        expires 30d;
    }
    
    location /admin/ {
        alias /opt/zolotarevka/admin/;
    }
}
```

**Task 6.3: Systemd сервис**
```ini
[Unit]
Description=Zolotarevka site
After=network.target

[Service]
WorkingDirectory=/opt/zolotarevka
ExecStart=/usr/local/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always
User=www-data

[Install]
WantedBy=multi-user.target
```

**Task 6.4: Seed-данные**
- Скрипт `scripts/seed.py` — заполняет БД:
  - 17 страниц из прототипа
  - Блоки для главной и ключевых разделов
  - Роли (админ, редакторы, модератор, автор)
  - Настройки по умолчанию

---

## 🚀 Распределение по субагентам

### Subagent 1: Бэкенд (Phase 1 + 2)
- `app.py`, `config.py`, `database.py` — каркас
- Pydantic модели
- Все API эндпоинты
- CORS, middleware

### Subagent 2: Админ-панель (Phase 3)
- `admin/index.html`, `admin/css/admin.css`, `admin/js/admin.js`, `admin/js/api.js`
- Переписать JS прототипа на API-вызовы
- Настройки сайта (модалка)
- Медиа-галерея

### Subagent 3: Шаблоны сайта (Phase 4)
- `templates/base.html` с Jinja2 навигацией из БД
- Все блок-рендеры (`templates/blocks/*.html`)
- `templates/index.html` — главная
- `templates/page.html` — страницы разделов
- CSS из существующего `site/css/style.css` → `static/css/style.css`

### Subagent 4: Интеграция (Phase 5 + 6)
- Веб-роуты `web/routes.py`
- Формы (suggest, feedback)
- Загрузка медиа
- Seed-данные
- Dockerfile, nginx config, systemd

---

## ✅ Проверка после реализации

1. **Админ-панель работает:**
   - Страницы создаются, редактируются, удаляются
   - Блоки добавляются, настраиваются, перемещаются
   - Роли создаются
   - Настройки сохраняются
   - Медиа загружаются

2. **Сайт отображает данные из админки:**
   - Главная — hero, bento, новости, виджеты
   - Страницы разделов — блоки в правильном порядке
   - Навигация — мега-меню из структуры
   - Настройки — цвета, шрифты, лого

3. **Развёртывание:**
   - `python app.py` → сайт работает на localhost:8000
   - Админка на /admin/
   - API на /api/

---

## ⚠️ Риски и вопросы

1. **Рендер блоков** — блок `cards` с `auto_from_tree` должен генерироваться из страниц, а не из manual items
2. **Мега-меню** — в прототипе нет модели групп меню. Нужно либо: (а) настраивать вручную в настройках, (б) группировать по категории страницы
3. **Изображения** — в прототипе их нет (все `#` url). Нужна система загрузки через медиа-галерею
4. **SEO** — meta-теги, og:title, og:image должны быть в base.html из настроек
5. **Админка без авторизации** — на MVP можно без пароля (слушается только на localhost), либо базовую HTTP Basic auth
