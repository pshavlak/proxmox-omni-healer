---
tags: [core, concepts]
created: 2026-05-28
---

# Концепции Paperclip

## Company (Компания)

Базовый организационный юнит. В одной инсталляции может быть много компаний с полной изоляцией данных. Компания имеет оргструктуру, агентов, проекты, цели, бюджеты.

## Agent (Агент)

Адаптер, который может получать heartbeat и выполнять работу. У агента есть:
- Роль, должность, иерархия подчинения
- Разрешения и бюджет
- Adapter (Claude Code, Codex, OpenClaw, CLI, HTTP и т.д.)
- API-ключ для доступа

## Goal / Mission (Цель / Миссия)

Каждая задача отслеживается до миссии компании. Агенты знают **что** делать и **почему**. Задачи несут полную цепочку целей (goal ancestry).

## Governance (Управление)

Ты совет директоров. Approval gates, execution policies, budget hard-stops, agent pause/resume/terminate. Все изменения версионированы — можно откатить.

## Budget (Бюджет)

Учёт токенов и затрат по компании, агенту, проекту, цели, задаче, провайдеру, модели. Scoped budget policies с порогами предупреждения и hard stops. Превышение → пауза агента + отмена очереди.

## Heartbeat (Пульс)

Очередь пробуждения на основе БД с объединением. Агенты просыпаются по расписанию, проверяют работу, действуют. Делегирование вверх/вниз по оргструктуре.

## Issue / Task (Задача)

Тикет с привязкой к company/project/goal/parent. Атомарный checkout (execution lock), blocker dependencies, комментарии, документы, вложения, work products, лейблы, inbox state.

## Workspace (Рабочее пространство)

Project workspaces и изолированные execution workspaces (git worktrees, operator branches). Агенты работают в правильной директории с правильным контекстом.

## Plugin (Плагин)

Система плагинов уровня инстанса с out-of-process workers, capability-gated host services, job scheduling, tool exposure, UI contributions.

## Routine (Рутина)

Повторяющиеся задачи с cron, webhook, API триггерами. Политики конкурентности и catch-up. Каждое выполнение создаёт tracked issue.

## Ссылки

- [Обзор Paperclip](paperclip-overview)
- [Архитектура Paperclip](paperclip-architecture)
- [Деплой и CLI](paperclip-deployment-cli)
- [Плагины Paperclip](paperclip-plugins)
- [Heartbeat и Исполнение](paperclip-heartbeat-execution)
- [Issue / Task система](paperclip-issues)
- [База данных](paperclip-database)
- [Governance](paperclip-governance)
- [Roadmap](paperclip-roadmap)
- [Paperclip vs Альтернативы](paperclip-vs-alternatives)
- [Source: README](/raw/Papperclip/README.md)
