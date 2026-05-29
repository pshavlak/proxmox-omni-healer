# CLI-скрипт управления пользователями

**Файл:** `/opt/hysteria-manager/hysteria-users.sh`

## Использование

```bash
./hysteria-users.sh add <username>    # Добавить пользователя
./hysteria-users.sh delete <username> # Удалить пользователя
./hysteria-users.sh list              # Список пользователей
```

## Хранение данных

Работает напрямую с `/etc/hysteria/users.json` — тем же файлом, что и [[Веб-панель Manager]].

Пароль генерируется через `openssl rand -base64 24 | tr -d '/+=' | head -c 20`.

## Источники
- `sources/Hysteria2/manager/hysteria-users.sh`
