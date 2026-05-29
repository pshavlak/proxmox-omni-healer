---
tags: [core, agents, architecture]
created: 2026-05-29
---

# Heartbeat и Исполнение Агентов

## Архитектура

**Control plane не запускает агентов — он их оркестрирует. Агенты бегут где угодно и докладывают домой.**

## Типы адаптеров (10 шт)

### Local (CLI/session)
- `claude-local` — Claude Code
- `codex-local` — Codex CLI
- `opencode-local` — OpenCode / Pi
- `pi-local` — Pi
- `gemini-local` — Gemini
- `grok-local` — Grok
- `cursor-local` — Cursor
- `acpx-local` — ACPX

### Cloud
- `cursor-cloud` — Cursor cloud

### Gateway
- `openclaw-gateway` — OpenClaw (remote agents, SOUL.md/HEARTBEAT.md)

### External plugin adapters
Через `adapter-plugin.md` — любой адаптер подключается динамически через реестр:
- `registerServerAdapter(adapter)`, `registerUIAdapter(adapter)`
- Валидация на сервере, а не в shared schemas

## Heartbeat lifecycle

1. **Планирование** — DB-backed очередь с coalescing
2. **Пробуждение** — проверка бюджета, workspace resolution, inject секретов, загрузка скиллов
3. **Исполнение** — вызов адаптера (process/http/CLI)
4. **Логирование** — structured logs, cost events, session state, audit trail
5. **Recovery** — orphaned runs автоматически обрабатываются

## Три метода исполнения

| Метод | Описание |
|-------|----------|
| **Local CLI/session** | Launch Claude Code, Codex, Gemini и т.д. через локальный процесс |
| **Command** | Shell-скрипт, мониторится Paperclip |
| **HTTP/webhook** | Fire-and-forget вызов внешнего агента |
| **External plugin adapter** | Self-hosted runtime через плагин |

## Состояния issue (State Machine)

```
backlog → todo → in_progress → in_review → done
                  ↓
              blocked ──→ todo/in_progress
                 │
             done/cancelled
```

- **backlog** — не готово к работе
- **todo** — готово, но никто не взял
- **in_progress** — активная работа (агентская → heartbeat-backed)
- **blocked** — ждёт внешнего изменения
- **in_review** — ждёт ревью/аппрува
- **done/cancelled** — терминальные

## Checkout (Атомарный захват)

- `checkoutRunId` — кто владеет правами выполнения
- `executionRunId` — какой run сейчас live
- Система чистит stale execution locks
- Single-assignee — у issue не может быть два assignee одновременно

## Crash & Recovery

При краше:
1. **Stranded `todo`** — один automatic recovery wake; если неудача → blocked с recovery action
2. **Stranded `in_progress`** — один automatic continuation wake; то же fallback

**Recovery action** — typed liveness repair path:
- source issue, recovery kind, idempotency fingerprint
- owner, cause, evidence, next action
- wake/monitor/timeout/retry/escalation policy

**Три исхода:**
- **Auto-recover** — ownership ясен, только execution continuity потеряна
- **Explicit recovery** — проблема есть, но unsafe завершить автоматически
- **Human escalation** — нужно решение board

## Startup Reconciliation

При старте сервера (в порядке):
1. Reap orphaned running runs
2. Resume persisted queued runs
3. Reconcile stranded assigned work
4. Scan silent active runs (watchdog)
5. Reconcile productivity reviews

## Ссылки

- [Концепции Paperclip](paperclip-concepts)
- [Архитектура Paperclip](paperclip-architecture)
- [Issue & Task System](paperclip-issues)
- [Source: execution-semantics.md](/raw/Papperclip/doc/execution-semantics.md)
