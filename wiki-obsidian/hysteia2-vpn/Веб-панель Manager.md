# Веб-панель Manager

**Путь на сервере:** `/opt/hysteria-manager/app.py`
**Порт:** `127.0.0.1:8081`
**Доступ:** `/44169d2dba4d0fd5/` через [[Nginx]]
**Пароль админа:** `_wk28wOuAf8`

## Функции

- Просмотр списка пользователей
- Добавление пользователя (генерирует пароль через `token_urlsafe(16)`)
- Удаление пользователя
- Копирование конфигурации клиента (JSON + hysteria2:// URI)

## Endpoint'ы

| URL | Метод | Описание |
|-----|-------|----------|
| `/` | GET | Главная (логин или список) |
| `/auth` | POST | Проверка пароля пользователя (вызов из Hysteria) |
| `/login` | POST | Вход администратора |
| `/logout` | GET | Выход |
| `/add` | POST | Добавить пользователя |
| `/delete/<user>` | POST | Удалить пользователя |

## Аутентификация

- **Пользовательская:** Hysteria отправляет POST с `{"auth": "password"}` → поиск в `users.json`
- **Админская:** cookie `admin_session` после ввода пароля из `/etc/hysteria/admin_password.txt`

## Запуск через systemd

```ini
[Unit]
Description=Hysteria 2 Manager Panel
After=network.target hysteria-server.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/hysteria-manager/app.py
Restart=on-failure
RestartSec=5s
```

См. [[Systemd-сервисы]].

## Источники
- `sources/Hysteria2/manager/app.py`
- `sources/Hysteria2/systemd/hysteria-manager.service`
