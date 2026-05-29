---
tags: [core, architecture]
created: 2026-05-28
---

# Архитектура Paperclip

## Структура репозитория

```
server/                 # Express REST API + оркестрация
ui/                     # React + Vite board UI
packages/
  db/                   # Drizzle схема, миграции, клиенты БД
  shared/               # Типы, константы, валидаторы, пути API
  adapters/             # Реализации адаптеров агентов
  adapter-utils/        # Общие утилиты адаптеров
  plugins/              # Пакеты системы плагинов
doc/                    # Документация
cli/                    # CLI (paperclipai)
```

## Системы (control plane)

```
┌─────────────────────────────────────────────────────────────┐
│                       PAPERCLIP SERVER                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │Identity  │  │Work &    │  │Heartbeat │  │Governance│    │
│  │& Access  │  │Tasks     │  │Execution │  │& Approvals│   │
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤    │
│  │Org Chart │  │Workspaces│  │Plugins   │  │Budget    │    │
│  │& Agents  │  │& Runtime │  │          │  │& Costs   │    │
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤    │
│  │Routines  │  │Secrets & │  │Activity  │  │Company   │    │
│  │& Schedule│  │Storage   │  │& Events  │  │Portability│   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└─────────────────────────────────────────────────────────────┘
```

1. **Identity & Access** — trusted local или authenticated mode, board users, agent API keys, JWT
2. **Org Chart & Agents** — роли, должности, иерархия, адаптеры
3. **Work & Task** — issues, checkout, blockers, комментарии, документы, вложения
4. **Heartbeat** — очередь пробуждения, проверка бюджета, workspace resolution, inject секретов
5. **Workspaces** — project workspaces, git worktrees, dev серверы, preview URLs
6. **Governance** — approval workflows, budget hard-stops, контроль агентов, audit log
7. **Budget** — учёт по всем разрезам, scoped policies, auto-pause
8. **Routines** — cron/webhook/API триггеры
9. **Plugin** — out-of-process, capability-gated, UI contributions
10. **Secrets** — шифрованное хранилище, провайдер-бэктированное, scoped injection
11. **Activity** — надёжный лог всех операций
12. **Company Portability** — экспорт/импорт организаций с очисткой секретов

## Адаптер-агностичность

Адаптеры подключаются через плагины. Из коробки: Claude Code, Codex, Cursor, OpenClaw, CLI (Bash), HTTP. Если может принимать heartbeat — нанят.

## База данных

Drizzle ORM, PostgreSQL. В dev — встроенный PGlite (без настройки). Миграции через `pnpm db:generate` + `pnpm db:migrate`.

## Ссылки

- [Обзор Paperclip](paperclip-overview)
- [Концепции Paperclip](paperclip-concepts)
- [Плагины Paperclip](paperclip-plugins)
- [Heartbeat и Исполнение](paperclip-heartbeat-execution)
- [Issue / Task система](paperclip-issues)
- [База данных](paperclip-database)
- [Деплой и CLI](paperclip-deployment-cli)
- [Roadmap](paperclip-roadmap)
- [Paperclip vs Альтернативы](paperclip-vs-alternatives)
- [Source: AGENTS.md](/raw/Papperclip/AGENTS.md)
