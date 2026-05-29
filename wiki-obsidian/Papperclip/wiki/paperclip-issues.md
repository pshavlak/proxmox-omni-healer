---
tags: [core, tasks, architecture]
created: 2026-05-29
---

# Issue / Task система

## Модель данных

Каждый issue имеет:
- `companyId`, `projectId`, `goalId`, `parentId` — полная иерархия
- `assigneeAgentId` или `assigneeUserId` — один assignee, не оба
- `status` — backlog/todo/in_progress/blocked/in_review/done/cancelled
- `checkoutRunId` — кто владеет execution rights
- `executionRunId` — какой run сейчас live
- `blockedByIssueIds` — blocker dependencies
- Комментарии, документы, аттачи, work products, лейблы

## Parent/Sub-issue vs Blockers

| Отношение | Смысл |
|-----------|-------|
| `parentId` | Структурное (work breakdown, rollup контекста) |
| `blockedByIssueIds` | Execution dependency (задача ждёт другую) |

**Правило:** `parentId` сам по себе не является execution dependency. Если parent реально ждёт child — добавь blocker.

## Checkout (атомарный захват)

Issue checkout — атомарная операция:
1. Проверка: нет другого checkoutRunId
2. Блокировка: никто другой не может взять
3. Снятие: release или force-release (admin)

Это предотвращает double-work и race conditions.

## Liveness Contract (для агентских issues)

Paperclip не должен оставлять agent-owned не-терминальную работу в состоянии, где никто не ответственен и ничего не всплывёт.

### Допустимые action paths:
- Active runs (текущий heartbeat)
- Queued wakes (запланированное пробуждение)
- Typed execution-policy participants
- Pending interactions (ждёт ответа)
- One-shot monitors
- Human owners
- Blocker chains (здоровые цепочки)
- Explicit recovery actions

### Stalled detection:
- `in_progress` без run/continuation/monitor/recovery → stalled
- `todo` без wake и без recovery → stalled
- `blocked` где unresolved blocker leaf не имеет action path → stalled
- `in_review` без typed participant и других action paths → stalled

### Issue Monitors

One-shot deferred action path для `in_progress`/`in_review`:
- `nextCheckAt`, `notes`, `serviceName`, `externalRef`
- `maxAttempts`, `recoveryPolicy`
- Не recurring — assignee явно пере-армит
- Exhausted → recovery policy (wake_owner / create_recovery_issue / escalate_to_board)

## Execution Policy

- `executionPolicy.monitor` — настройки монитора
- Recovery model profile: cheap model для "status-only overhead", normal model для deliverable work
- `allowDeliverableWork: false` — флаг для статусных операций

## Goal Ancestry

Каждый issue несёт полную цепочку целей до миссии компании. Агенты всегда знают **почему** они делают эту работу. Work without justification shouldn't exist.

## Ссылки

- [Концепции Paperclip](paperclip-concepts)
- [Heartbeat и Исполнение](paperclip-heartbeat-execution)
- [Source: execution-semantics.md](/raw/Papperclip/doc/execution-semantics.md)
- [Source: SPEC-implementation.md](/raw/Papperclip/doc/SPEC-implementation.md)
