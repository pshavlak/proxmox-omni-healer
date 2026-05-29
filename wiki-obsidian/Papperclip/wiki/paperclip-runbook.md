---
tags: [ops, deployment, startup]
created: 2026-05-29
updated: 2026-05-29
---

# Runbook Paperclip

> Правильный запуск и обслуживание Paperclip.

## Запуск (локальный проект)

```bash
cd /Users/phavlak/Documents/project/Papperclip

# Первый запуск или после обновления зависимостей
pnpm install

# Запуск сервера + UI
pnpm dev
```

После запуска:
- Сервер: `http://localhost:3100`
- UI: `http://localhost:3100` (встроен в сервер)

## ⚠️ Важно: не использовать глобальный `paperclipai`

**НЕЛЬЗЯ** запускать через глобальную установку:
```bash
# ❌ НЕПРАВИЛЬНО — использует глобальный npm пакет, не локальный код
npm exec paperclipai run

# ✅ ПРАВИЛЬНО — использует локальный код из server/src/
pnpm dev
```

Глобальный `paperclipai` (`/Users/phavlak/node_modules/paperclipai/`) НЕ синхронизирован с локальным кодом. Изменения в `server/src/` не применяются при запуске через `paperclipai run`.

## Конфигурация DeepSeek API

Настроено в `.env`:
```
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_API_KEY=<ключ>
```

Модель на всех агентах: **deepseek-v4-flash** (для codex_local), **openai/deepseek-v4-flash** (для opencode_local).

## Обслуживание

### Миграции БД
```bash
pnpm run db:migrate
```

### Сброс dev БД
```bash
rm -rf data/pglite
pnpm dev
```

### Остановка
```bash
pkill -f "tsx.*src/index.ts"
```

## Связанные страницы

- [Деплой и CLI Paperclip](paperclip-deployment-cli) — режимы деплоя
- [Архитектура Paperclip](paperclip-architecture) — архитектура сервера
- [Обзор Paperclip](paperclip-overview) — обзор проекта
