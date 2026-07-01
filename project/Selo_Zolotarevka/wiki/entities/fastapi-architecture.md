---
title: FastAPI архитектура
created: 2026-06-25
updated: 2026-06-30
type: concept
tags: [fastapi, python, sqlite, jinja2, архитектура, админка, реализовано, bugs]
sources: [site/app.py, site/database.py, site/config.py, site/models.py]
---

# FastAPI архитектура

## Текущий статус
✅ **Разработано и работает локально.** Планируется деплой на Proxmox LXC.

## Стек

| Компонент | Технология |
|-----------|-----------|
| Backend | Python 3.11 + FastAPI |
| База данных | SQLite (WAL-mode) |
| Шаблонизатор | Jinja2 |
| Валидация | Pydantic v2 |
| Админ-панель | SPA на ванильном JS |
| Запуск | uvicorn |
| Сервер | Proxmox LXC (в плане) |

Зависимости: `fastapi`, `uvicorn[standard]`, `jinja2`, `python-multipart`, `pydantic`.

## Структура проекта

```
site/
├── app.py                  # FastAPI приложение + все маршруты
├── config.py               # Конфигурация (пути, лимиты)
├── database.py             # SQLite подключение, инициализация, seed
├── models.py               # Pydantic-модели для API
├── requirements.txt        # Зависимости
├── zolotarevka.db          # SQLite база данных
│
├── admin/                  # Админ-панель SPA
│   ├── index.html          # SPA-приложение
│   ├── css/admin.css       # Стили админки
│   └── js/
│       ├── admin.js        # Основной JS (навигация, блоки, роли)
│       └── api.js          # API-клиент
│
├── templates/              # Jinja2 шаблоны публичного сайта
│   ├── base.html           # Базовый шаблон
│   ├── index.html          # Главная страница
│   ├── page.html           # Шаблон страницы-раздела
│   ├── errors/             # Страницы ошибок
│   │   └── 404.html
│   ├── blocks/             # Шаблоны блоков (10 типов)
│   │   ├── hero.html, text.html, image.html, gallery.html,
│   │   ├── video.html, table.html, cards.html, documents.html,
│   │   ├── form.html, divider.html
│   └── partials/           # Фрагменты
│       ├── header.html, footer.html, top_bar.html, suggest_modal.html
│
├── static/                 # Статика (css, js, uploads)
| pages/                  # HTML-прототипы страниц
├── ДИАЛОГ_СОЗДАНИЯ_САЙТА.md  # Исходный диалог создания
│
sketches/
├── site-builder-v2.html     # Прототип админ-панели (исходная логика)
├── site-builder-prototype.html
├── admin-panel-structure.html
└── DIALOG_REDESIGN_2026-06-09.md
```

## API Маршруты

### Публичный сайт (Jinja2)
| Маршрут | Описание |
|---------|----------|
| `GET /` | Главная страница |
| `GET /{slug}` | Страница раздела/подраздела |
| `GET /static/*` | Статические файлы |

### Публичное API
| Маршрут | Описание |
|---------|----------|
| `GET /api/content/pages` | Дерево опубликованных страниц |
| `GET /api/content/recent` | Последние обновлённые страницы |

### Управление страницами
| Маршрут | Описание |
|---------|----------|
| `GET /api/pages` | Все страницы |
| `POST /api/pages` | Создать страницу |
| `PUT /api/pages/{id}` | Обновить страницу |
| `DELETE /api/pages/{id}` | Удалить страницу (каскадно с детьми) |
| `PUT /api/pages/reorder` | Изменить порядок страниц |

### Управление блоками
| Маршрут | Описание |
|---------|----------|
| `GET /api/pages/{id}/blocks` | Блоки страницы |
| `PUT /api/pages/{id}/blocks` | Сохранить все блоки (замена) |
| `POST /api/blocks/{id}/move` | Переместить блок (up/down) |

### Роли и настройки
| Маршрут | Описание |
|---------|----------|
| `GET/POST/PUT/DELETE /api/roles` | CRUD ролей |
| `GET/PUT /api/settings` | Настройки сайта |

### Медиа
| Маршрут | Описание |
|---------|----------|
| `GET /api/media` | Список загруженных файлов |
| `POST /api/media/upload` | Загрузить файл (до 10MB) |
| `DELETE /api/media/{id}` | Удалить файл |

### Предложения новостей
| Маршрут | Описание |
|---------|----------|
| `POST /api/suggest` | Отправить новость (публичная форма) |
| `GET /api/suggestions` | Список предложений (админка) |

## База данных SQLite

### Схема

```sql
-- Страницы (иерархическое дерево)
pages (id, name, icon, parent, sort_order, status, created_at, updated_at)
  -- status: 'draft' | 'published'

-- Блоки на страницах
blocks (id, page_id, type, name, sort_order, config)
  -- type: hero, text, image, gallery, video, table, cards, documents, form, divider
  -- config: JSON с настройками блока

-- Роли пользователей
roles (id, name, icon, sections, caps)
  -- sections: JSON-массив ID разделов
  -- caps: JSON-объект прав (moderation, upload, publish)

-- Настройки сайта
settings (key, value)

-- Медиафайлы
media (id, filename, original_name, mime_type, size, alt_text, created_at)

-- Предложения новостей
suggestions (id, name, email, category, text, status, created_at)
  -- status: 'pending' | 'approved' | 'rejected'

-- Группы меню (мега-меню)
menu_groups (id, name, icon, sort_order)
menu_group_items (group_id, page_id, sort_order)
```

### Seed-данные
При первом запуске БД заполняется:
- **17 страниц** (главная, школа, детсад, совхоз, спорт, жизнь села, медиа, новости + подразделы)
- **Блоки для главной** (hero, bento-сетка, текст, форма предложений)
- **Блоки для школы** (hero, текст, документы)
- **6 ролей** (admin, school_editor, sports_editor, farm_editor, content_moderator, community_author)
- **Настройки по умолчанию** (цвета, соцсети, контакты)

## Блочный редактор (10 типов блоков)

| Тип | Описание | Config |
|-----|----------|--------|
| hero | Баннер с заголовком/подзаголовком/CTA | title, subtitle, btn_text, btn_url, bg_color, bg_image |
| text | HTML-текст | content |
| image | Изображение с подписью | url, caption, alt |
| gallery | Сетка изображений | images[], columns |
| video | Видео Rutube/VK | url, embed, caption |
| table | Таблица с данными | headers[], rows[] |
| cards | Плитки/карточки | auto_from_tree, card_overrides, columns |
| documents | Список документов | docs[{title, url, description}] |
| form | Форма обратной связи | form_type, title |
| divider | Разделитель | (нет настроек) |

## Админ-панель

SPA-приложение (`/admin`), реализованное на ванильном JS (без фреймворков).

Разделы:
- 🗺️ **Страницы сайта** — дерево + блочный редактор, draft/live
- 🖼️ **Медиа-центр** — загрузка/удаление файлов
- 📰 **Контент** — все записи на сайте
- ⚙️ **Настройки** — соцсети, цвета, контакты
- 👥 **Пользователи и роли** — управление доступом

Архитектура админки следует тому же принципу, что и WordPress-версия, но на новом стеке:
- Данные через AJAX → API → SQLite
- Черновики (draft) → публикация (live)
- Роли привязаны к разделам через `sections`

## Инфраструктура и домен

### Схема подключения

```
🌍 DNS (золотаревка.рф)
    ↓
🖥️ VPS server-rm7kbp (31.56.208.248)
   ├── nginx :80/:443 → прокси
   └── WireGuard 10.0.0.1 ←→ 10.0.0.2
                             ↓
                      📦 LXC wordpress (192.168.1.64) — VMID 105
                         ├── FastAPI :8000
                         └── Apache/WordPress :80
                         ↑
                   🖥️ Proxmox p-home (192.168.1.110)
                      Ключ: ~/.ssh/proxmox_key
```

### LXC `wordpress` (VMID 105)

- **Контейнер**: `192.168.1.64` на Proxmox `p-home` (192.168.1.110), WireGuard IP `10.0.0.2`
- **SSH**: `ssh wordpress-lxc` (ключ `~/.ssh/id_ed25519`)
- **WordPress**: `/var/www/html/wordpress`, Apache `:80`
- **FastAPI**: `/var/www/zolotarevka-fastapi`, uvicorn `:8000`
- **Systemd**: `zolotarevka-fastapi.service`
- **Бэкап**: `/var/www/zolotarevka-fastapi.backup-20260628_172214`

Проверки в контейнере:

```bash
ssh wordpress-vm "systemctl status zolotarevka-fastapi.service"
ssh wordpress-vm "curl http://127.0.0.1:8000/"
ssh wordpress-vm "curl http://127.0.0.1:8000/admin/"
ssh wordpress-vm "curl http://127.0.0.1:8000/api/pages"
ssh wordpress-vm "curl http://127.0.0.1/"
```

### VPS `server-rm7kbp` (31.56.208.248) — основной

- **SSH**: `ssh zolotarevka-vps` (ключ `~/.ssh/id_ed25519`)
- **OC**: Ubuntu 24.04.4 LTS, nginx 1.24.0, Python 3.12.3
- **WireGuard**: VPS `10.0.0.1` → LXC `10.0.0.2`
- **nginx**: публичный вход `80/443`, прокси на LXC через WireGuard

Маршрутизация nginx:

| Домен | Upstream | Назначение |
|-------|----------|------------|
| `золотаревка.рф` / `xn--80aaflivdxbvu.xn--p1ai` | `10.0.0.2:8000` | FastAPI сайт |
| `www.золотаревка.рф` / `www.xn--80aaflivdxbvu.xn--p1ai` | `10.0.0.2:8000` | FastAPI сайт |
| `zolotarevka.yupiterpro.ru` | `10.0.0.2:80` | WordPress (legacy) |

### VPS `62.113.105.38` — старый (не используется для сайта)

- **SSH**: `ssh -i /Users/phavlak/.ssh/id_hysteria_rsa root@62.113.105.38`
- **Hysteria**: UDP `8443`
- Ранее направлял `золотаревка.рф` через nginx. Выведен из эксплуатации для сайта.

### DNS

Актуальные записи (проверено 2026-06-30):

| Тип | Хост | Значение | Статус |
|-----|------|----------|--------|
| A | `золотаревка.рф` / `xn--80aaflivdxbvu.xn--p1ai` | `31.56.208.248` | ✅ |
| A | `www.золотаревка.рф` / `www.xn--80aaflivdxbvu.xn--p1ai` | `31.56.208.248` | ✅ |

Проверка:

```bash
dig +short @8.8.8.8 xn--80aaflivdxbvu.xn--p1ai
dig +short @8.8.8.8 www.xn--80aaflivdxbvu.xn--p1ai
# Обе должны вернуть 31.56.208.248
```

### SSL

Сертификат выпускать после настройки nginx и WireGuard:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx \
  -d xn--80aaflivdxbvu.xn--p1ai \
  -d www.xn--80aaflivdxbvu.xn--p1ai \
  --non-interactive --agree-tos \
  -m admin@yupiterpro.ru \
  --redirect
```

### Проверка после SSL

```bash
nginx -t && systemctl reload nginx
curl -I https://xn--80aaflivdxbvu.xn--p1ai/
curl -I https://www.xn--80aaflivdxbvu.xn--p1ai/
curl -I https://zolotarevka.yupiterpro.ru/
```

## Запуск

```bash
cd site
source .venv/bin/activate
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

## Известные баги и исправления (2026-06-25)

### 1. Seed-данные не загружались при старте через uvicorn
`init_db()` вызывался в `lifespan`, но `seed_db()` — только при прямом импорте `database.py`.  
**Исправление:** `seed_db()` добавлен в `lifespan` в `app.py`.  
Также добавлено создание `static/uploads/` при старте.

### 2. Сломанные ссылки в footer
В `templates/partials/footer.html` были неверные slug'ы:
- `/sport` → `/sports`
- `/life` → `/village-life`
- `/bulletin-board` → `/bulletin`
- `/sovkhoz` → `/farm`

### 3. API сохранения блоков — 422 Validation Error
Параметр `blocks: list` без `Body()` заставлял FastAPI ожидать `{"blocks": [...]}`, а админ-панель отправляла `[...]`.  
**Исправление:** `blocks: list = Body(...)`.

### 4. UNIQUE constraint failed: blocks.id
Админ-панель генерировала ID блоков по счётчику `b1000`, `b1001`, ...  
При перезагрузке страницы счётчик сбрасывался → коллизия с блоками других страниц.  
**Исправление:**
- `admin/js/admin.js`: ID теперь `b<Date.now()_base36><counter_base36>` — всегда уникален
- `admin/js/admin.js`: счётчик обновляется при загрузке существующих блоков
- `app.py`: бэкенд проверяет конфликты ID и генерирует новый при коллизии

## Связанные страницы
- [[admin-panel-redesign]] — предыдущая WordPress версия (legacy)
- [[SCHEMA]] — схема вики и теги
