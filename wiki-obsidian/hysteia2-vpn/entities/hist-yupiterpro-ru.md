---
title: hist.yupiterpro.ru — Domain & Web Panel
created: 2026-06-08
updated: 2026-06-08
type: entity
tags: [сервер, nginx, flask, управление, сертификаты]
sources: [nginx/hist.yupiterpro.ru, manager/app.py, README.md]
confidence: high
---

# hist.yupiterpro.ru — Domain & Web Panel

Домен, привязанный к [[hysteria-2-server]]. Через него доступна веб-панель управления пользователями и, опционально, сайт-заглушка. SSL-сертификаты от Let's Encrypt.

## Nginx (Reverse Proxy)

Nginx настроен на порту 443 с SSL-терминацией. Выполняет две роли:

1. **Сайт-заглушка** — корень `/` отдаёт статический `index.html`
2. **Reverse proxy** для Flask-панели по скрытому пути `/44169d2dba4d0fd5/`

```
HTTP (80) → 301 HTTPS (443)
  → / → статический index.html (заглушка)
  → /44169d2dba4d0fd5/ → proxy_pass http://127.0.0.1:8081/ (Flask)
```

### Важные детали конфигурации nginx

- **Прямые маршруты Flask заблокированы:** `/login`, `/logout`, `/add`, `/delete` возвращают 404 при прямом обращении
- **sub_filter** переписывает пути в HTML, чтобы панель работала из-под скрытого пути
- **proxy_cookie_path** — корректировка пути для cookies сессии

## Flask Web Panel (Hysteria 2 Manager)

Веб-панель на Flask (Python 3), запущенная на `127.0.0.1:8081`. Предоставляет управления пользователями через браузер.

### Функции

- **Аутентификация:** HTTP-эндпоинт `/auth` для Hysteria 2 (POST, принимает пароль, проверяет по `users.json`)
- **Управление пользователями:** добавление, удаление, просмотр списка
- **Генерация конфигураций:** для каждого пользователя отображает JSON-конфиг и `hysteria2://` URI
- **Админ-пароль:** хранится в `/etc/hysteria/admin_password.txt`, значение `_wk28wOuAf8`

### Маршруты

| Маршрут | Метод | Описание |
|---------|-------|----------|
| `/44169d2dba4d0fd5/` | GET | Главная страница (логин или список пользователей) |
| `/44169d2dba4d0fd5/login` | POST | Вход с паролем администратора |
| `/44169d2dba4d0fd5/add` | POST | Добавление пользователя |
| `/44169d2dba4d0fd5/delete/<username>` | POST | Удаление пользователя |
| `/44169d2dba4d0fd5/logout` | GET | Выход |

### Systemd

Сервис: `hysteria-manager.service`
- `ExecStart=/usr/bin/python3 /opt/hysteria-manager/app.py`
- `After=network.target hysteria-server.service`
- Auto-restart on failure

## SSL-сертификаты

Let's Encrypt через certbot. Путь: `/etc/letsencrypt/live/hist.yupiterpro.ru-0001/`. Сертификаты **не включены** в бэкап — при восстановлении на новом сервере нужно перевыпускать через `certbot certonly --nginx -d hist.yupiterpro.ru`.

## Связанные страницы

- [[hysteria-2-server]] — Hysteria 2 сервер, на котором работает домен
- [[user-management]] — управление пользователями
