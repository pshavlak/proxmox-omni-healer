---
tags: [core, database]
created: 2026-05-29
---

# База данных Paperclip

## Стек

- **ORM:** Drizzle
- **БД:** PostgreSQL
- **Dev:** встроенный PGlite (zero config, данные в `~/.paperclip/instances/default/db/`)
- **Docker:** PostgreSQL 17 на порту 5432
- **Production:** Supabase или любой PostgreSQL

## Миграции

```bash
pnpm db:generate    # Сгенерировать миграцию
pnpm db:migrate     # Применить миграции
pnpm issue-references:backfill  # Обратная заливка references
```

## Ключевые таблицы (из SPEC-implementation.md)

### Company-scoped (все привязаны к company)
- `companies`
- `agents` + `agent_api_keys`
- `goals` (иерархия целей от company до task)
- `projects`
- `issues` + `issue_comments` + `issue_documents` + `issue_attachments`
- `heartbeat_runs`
- `cost_events`
- `approvals`
- `activity_log`
- `memberships` (company_memberships, project_memberships, agent_memberships)
- `secrets`
- `assets`

### Instance-wide
- `plugins` + `plugin_config` + `plugin_state`
- `plugin_jobs` + `plugin_job_runs`
- `plugin_webhook_deliveries`
- `authUsers` (Better Auth)
- `instance_user_roles`

### Resource Membership
- `project_memberships` + `agent_memberships` — column `state` (joined/left)
- Missing row = user joined (эффективно)

## Плагины и БД

- `plugin_database_namespaces` — отслеживание namespace плагинов
- `plugin_migrations` — миграции плагинов
- Плагины НЕ имеют прямого доступа к БД — только через SDK

## Secrets

- Provider: `local_encrypted` (по умолчанию)
- Master key: `~/.paperclip/instances/default/secrets/master.key`
- Env override: `PAPERCLIP_SECRETS_MASTER_KEY`, `PAPERCLIP_SECRETS_MASTER_KEY_FILE`
- Миграция inline env vars: `pnpm paperclipai secrets migrate-inline-env`

## Бэкапы

```bash
pnpm db:backup    # Логический dump БД
# НЕ включает: локальные uploads, master key секретов
```

## Ссылки

- [Архитектура Paperclip](paperclip-architecture)
- [Source: DATABASE.md](/raw/Papperclip/doc/DATABASE.md)
- [Source: SPEC-implementation.md](/raw/Papperclip/doc/SPEC-implementation.md)
