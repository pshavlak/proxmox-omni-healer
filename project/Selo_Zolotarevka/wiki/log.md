---
title: Журнал изменений
created: 2026-05-26
updated: 2026-06-28
type: concept
tags: [wiki]
---

# Журнал изменений

## 2026-07-01
- **Сайт:** http://золотаревка.рф — FastAPI работает через reverse SSH tunnel (LXC→VPS)
- **Reverse tunnel:** systemd сервис на LXC, порт 8000. Стабильнее WG через CGNAT
- **WireGuard:** нестабилен — CGNAT блокирует data-пакеты
- **nginx:** прокси на localhost:8000 (через reverse tunnel вместо WG)
- **Cloudflare DNS:** добавлен домен, A proxied, AAAA удалена. NS: ada/gordon.ns.cloudflare.com (ждём propagation)
- **SSL:** acme.sh + CF API — ждёт NS. Крон каждые 30 мин
- **UFW:** включён. SSH заблокирован — восстановить через консоль: `ufw allow 22/tcp`
- **Деплой:** новый FastAPI-проект перенесён в LXC `wordpress` в отдельную папку `/var/www/zolotarevka-fastapi`.
- **WordPress:** `/var/www/html/wordpress` не изменялся; Apache на `:80` продолжает обслуживать текущий сайт.
- **Бэкап:** предыдущая FastAPI-папка сохранена как `/var/www/zolotarevka-fastapi.backup-20260628_172214`.
- **Проверено:** FastAPI `/`, `/admin/`, `/api/pages` отвечают `200`; WordPress `/` отвечает `200`, `/wp-admin/` отвечает `302`.
- **Домен:** nginx на VPS `62.113.105.38` настроен: `золотаревка.рф` и `www.золотаревка.рф` → FastAPI `10.0.0.2:8000`, `zolotarevka.yupiterpro.ru` → WordPress `10.0.0.2:80`.
- **DNS:** добавлены требуемые A-записи `золотаревка.рф` и `www.золотаревка.рф` на `62.113.105.38`; SSL выпускать после распространения DNS.
- **Документация:** шаги подключения, DNS, nginx, SSL и проверки добавлены в `entities/fastapi-architecture.md`.
- **Проверка DNS/SSL:** правильный punycode `золотаревка.рф` — `xn--80aaflivdxbvu.xn--p1ai`; DNS пока возвращает `31.31.196.17`, поэтому SSL для основного домена ещё не выпускался.

## 2026-06-25 (вечер)
- **entities/fastapi-architecture.md**: добавлен раздел «Известные баги и исправления»
- **app.py**: исправлен вызов `seed_db()` в `lifespan`, создание `static/uploads/`
- **app.py**: `api_save_blocks` — `blocks: list = Body(...)` для приёма массива
- **app.py**: `api_save_blocks` — защита от коллизий ID блоков между страницами
- **footer.html**: исправлены битые ссылки (`/sport → /sports`, `/life → /village-life` и др.)
- **admin/js/admin.js**: ID блоков генерируется через `Date.now()` — уникален после перезагрузки
- **admin/js/admin.js**: счётчик ID обновляется при загрузке блоков с сервера
- **Проверено:** API → Админка → Публичный сайт — полный цикл сохранения/отображения

## 2026-06-25
- **SCHEMA.md**: обновлён — FastAPI-стек, новые теги (fastapi, python, sqlite), legacy-статус для WordPress
- **entities/fastapi-architecture.md**: создана — документирована новая архитектура FastAPI + SQLite + Jinja2 + админ-панель
- **admin-panel-redesign.md**: помечен как `legacy` — заменён новой FastAPI админ-панелью
- **log.md**: создана — этот файл

## 2026-06-09
- **admin-panel-redesign.md**: создана — документирован редизайн WordPress админ-панели
- **SCHEMA.md**: создана — первоначальная схема вики

## 2026-05-26
- Начало проекта, создание первоначальных markdown-документов
