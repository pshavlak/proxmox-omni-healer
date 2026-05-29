---
tags: [core, deployment, cli]
created: 2026-05-29
---

# Деплой и CLI Paperclip

## Режимы деплоя

Paperclip имеет два режима runtime:

| Режим | Аутентификация | Использование |
|-------|---------------|---------------|
| `local_trusted` | Нет логина | Локальный single-user |
| `authenticated` + private | Логин обязателен | Tailscale/VPN/LAN |
| `authenticated` + public | Логин обязателен | Продакшн / интернет |

**Reachability (server.bind):** loopback, lan (0.0.0.0), tailnet (автоопределение Tailscale), custom (явный host).

## CLI (`paperclipai`)

### Instance setup
```
onboard          # Интерактивная настройка (--yes для быстрого старта)
configure        # Редактирование конфига (--section server/storage)
doctor           # Диагностика с проверкой под режим
env              # Управление окружением
```

### Управление
```
company list/get/delete
agent list/get/local-cli
issue list/create/update/checkout/release
approval list/get/create/approve/reject
activity list/get
dashboard get
```

### Skills
```
skills browse/search/inspect/install/list
skills check/update/audit/reset/remove
agent skills list/sync/clear
```

### Secrets
```
secrets list/create (--value-env для безопасности)
```

## Локальное хранилище

Всё в `~/.paperclip/instances/default/`:
- `config/`, `env/`, `db/`, `data/`, `logs/`, `secrets/`
- `workspaces/`, `projects/`, `companies/`
- Override через `PAPERCLIP_HOME` и `PAPERCLIP_INSTANCE_ID`

### Storage providers
- `local_disk` — по умолчанию
- `s3` — S3-совместимое объектное хранилище (через `configure --section storage`)

## Первый запуск

### local_trusted
`npx paperclipai onboard --yes` → loopback, без логина, готов за минуту.

### Authenticated (+private)
`npx paperclipai onboard --yes --bind lan` → логин, board claim через `/board-claim/<token>?code=<code>`.

### Authenticated (+public)
Интернет-доступ. Bootstrap через `pnpm paperclipai auth bootstrap-ceo` (browser-claim отключён намеренно — только high-entropy invite).

## Board / User интеграция

- Board identity = реальный user principal в БД
- `authUsers` → `instance_user_roles` (admin) → `company_memberships`
- User assignment paths валидируют активное членство

## Ссылки

- [Архитектура Paperclip](paperclip-architecture)
- [Source: CLI.md](/raw/Papperclip/doc/CLI.md)
- [Source: DEPLOYMENT-MODES.md](/raw/Papperclip/doc/DEPLOYMENT-MODES.md)
