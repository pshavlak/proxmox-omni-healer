---
tags: [core, governance]
created: 2026-05-29
---

# Governance и Управление

## Модель

Ты — **Board директоров**. В `local_trusted` режиме ты и есть board. В `authenticated` — board-пользователи с ролью `instance_admin`.

## Полномочия Board

- **Найм/увольнение** агентов — через approval gates
- **Стратегия** — CEO стратегия требует approval board
- **Override** — pause/resume/terminate любого агента
- **Бюджеты** — установка лимитов, hard stop при превышении
- **Откат** — все изменения revisioned, можно откатить

## Approval Workflow

1. Создаётся approval request (на战略ию, hire, изменение)
2. Board review с комментариями
3. Approve / Reject / Request Revision
4. Результат фиксируется в audit trail
5. При approve — изменения применяются

### Pre-approval restrictions
CEO не может pre-approve свою собственную стратегию — нужен явный аппрув board.

## Budget система

- **Окно:** ежемесячное (UTC)
- **Soft alert:** 80% — предупреждение
- **Hard limit:** 100% — auto-pause агента, отмена очереди
- **Трекинг:** по company / agent / project / goal / issue / provider / model
- **Read-time rollup:** затраты считаются на лету, не при каждом событии

## Audit Trail

- Все mutating actions записаны
- Activity log: actor, действие, timestamp, payload
- Actor типы: board user, agent, plugin
- Heartbeat run изменения, cost events, approvals, комментарии

## Permission Matrix

| Действие | Board | Agent |
|----------|-------|-------|
| CRUD компаний | ✅ | ❌ |
| Найм/увольнение агентов | ✅ | ❌ |
| Создание/назначение issues | ✅ | ✅ (scoped) |
| Approval | ✅ | ❌ |
| Бюджеты | ✅ | ❌ |
| Чтение activity | ✅ | ✅ (своя компания) |

## Governance над plugin-ами

- Установка плагина — операторская, глобальная
- Capabilities статичны и обязательны
- При upgrade с новыми cap — `upgrade_pending`, нужно явное approve
- Плагин НЕ может: принимать approval решения, менять бюджеты, обходить auth

## Ссылки

- [Концепции Paperclip](paperclip-concepts)
- [Heartbeat и Исполнение](paperclip-heartbeat-execution)
- [Source: SPEC.md](/raw/Papperclip/doc/SPEC.md)
- [Source: SPEC-implementation.md](/raw/Papperclip/doc/SPEC-implementation.md)
