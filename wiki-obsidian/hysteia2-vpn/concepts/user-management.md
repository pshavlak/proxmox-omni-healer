---
title: User Management
created: 2026-06-08
updated: 2026-06-08
type: concept
tags: [управление, пользователи, flask, аутентификация]
sources: [manager/app.py, manager/hysteria-users.sh, config/users.json, README.md]
confidence: high
---

# User Management

Управление пользователями VPN-инфраструктуры. Два интерфейса: веб-панель (Flask) и CLI-скрипт.

## Список пользователей

19 пользователей (по состоянию на 28.05.2026):

| Имя пользователя | Роль / примечание |
|-----------------|-------------------|
| `myphone` | Владелец (телефон) |
| `Senya` | Семья |
| `Mama` | Семья |
| `my_mac` | Владелец (Mac) |
| `Mal-FedPA` | Семья |
| `TV` | Телевизор |
| `home-pc` | Домашний ПК |
| `Zlata` | Семья |
| `ShavkutaAV` | Знакомый |
| `NatcenkoD` | Знакомый |
| `bolendr` | Знакомый |
| `ArtamonovaI` | Знакомый |
| `KichanL_ot_BorisenkoN` | Знакомый |
| `Veryayskiy` | Знакомый |
| `Re4er` | Знакомый |
| `PC-Home` | Домашний ПК |
| `HohlachevS` | Знакомый |
| `HohlachevaNM` | Знакомый |

## Формат аутентификации

Hysteria 2 использует HTTP-бекенд для проверки паролей. Пароли хранятся в `users.json` в формате:

```json
{
  "username": "base64-password"
}
```

При клиентском подключении Hysteria сервер отправляет пароль на `/auth` эндпоинт Flask-панели, которая проверяет его по `users.json`.

## Веб-панель (Flask)

См. [[hist-yupiterpro-ru]] для деталей. Доступна по скрытому пути:
```
https://hist.yupiterpro.ru/44169d2dba4d0fd5/
```
Пароль администратора: `_wk28wOuAf8`

Функции:
- Просмотр всех пользователей
- Добавление нового пользователя (генерирует пароль)
- Удаление пользователя
- Генерация JSON-конфига и hysteria2:// URI

## CLI-скрипт

Скрипт `/opt/hysteria-manager/hysteria-users.sh` — bash-интерфейс для управления через SSH:

```bash
# Список пользователей
/opt/hysteria-manager/hysteria-users.sh list

# Добавить пользователя
/opt/hysteria-manager/hysteria-users.sh add username

# Удалить пользователя
/opt/hysteria-manager/hysteria-users.sh delete username
```

CLI-скрипт работает напрямую с `users.json` и генерирует пароль через `openssl rand` (base64, 20 символов).

## URI для подключения

Формат:
```
hysteria2://<password>@hist.yupiterpro.ru:443?insecure=0&sni=hist.yupiterpro.ru
```

**Важно:** URI указывает порт `:443`, хотя сервер слушает на `:8443`. Это не ошибка — nginx на `:443` пробрасывает трафик Hysteria 2 на `:8443` (через stream-прокси или напрямую ACL). Или же :8443 остался от старой конфигурации — уточнить.

## Связанные страницы

- [[hist-yupiterpro-ru]] — веб-панель и домен
- [[hysteria-2-server]] — сервер аутентификации
