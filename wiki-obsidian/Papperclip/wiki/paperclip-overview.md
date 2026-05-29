---
tags: [core, product]
created: 2026-05-28
---

# Paperclip — Обзор

Paperclip — open-source платформа оркестрации для управления компаниями из AI-агентов. Сервер на Node.js + React UI.

**Слоган:** *Open-source orchestration for zero-human companies*

**Если OpenClaw — сотрудник, то Paperclip — компания.**

## Ключевая идея

Paperclip не создаёт агентов — он **координирует** их в организацию: с оргструктурой, бюджетами, целями, управлением и подотчётностью.

Bring Your Own Agent — любой агент, любой runtime, если может принимать heartbeat — нанят.

## Проблема, которую решает

Без Paperclip: 20 терминалов Claude Code, потеря контекста, нет контроля расходов, ручной запуск рутины, разрозненные конфиги агентов.

С Paperclip: тикет-система, оргструктура, делегирование, бюджеты, governance, heartbeats, аудит.

## Возможности

- **BYO Agent** — Claude Code, Codex, Cursor, OpenClaw, HTTP, Bash — любой
- **Goal Alignment** — каждая задача привязана к миссии компании
- **Heartbeats** — агенты просыпаются по расписанию
- **Cost Control** — бюджеты на агента, hard stop при лимите
- **Multi-Company** — одна инсталляция, много компаний, полная изоляция
- **Ticket System** — каждая операция записана, полный audit trail
- **Governance** — ты board: найм, стратегия, пауза/терминейшн
- **Мобильный доступ**

## Быстрый старт

```bash
npx paperclipai onboard --yes
```

Требования: Node.js 20+, pnpm 9.15+. API на `localhost:3100`, встроенный PGlite.

## Лицензия

MIT, самохостинг.

## Ссылки

- [Архитектура Paperclip](paperclip-architecture)
- [Концепции Paperclip](paperclip-concepts)
- [Деплой и CLI](paperclip-deployment-cli)
- [Плагины Paperclip](paperclip-plugins)
- [Heartbeat и Исполнение](paperclip-heartbeat-execution)
- [Issue / Task система](paperclip-issues)
- [База данных](paperclip-database)
- [Governance](paperclip-governance)
- [Roadmap](paperclip-roadmap)
- [Paperclip vs Альтернативы](paperclip-vs-alternatives)
- [Source: README](/raw/Papperclip/README.md)
