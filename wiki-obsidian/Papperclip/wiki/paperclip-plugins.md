---
tags: [core, plugins, architecture]
created: 2026-05-29
---

# Плагины Paperclip

Paperclip имеет два способа расширения: **platform modules** (доверенные, in-process) и **plugins** (out-of-process, capability-gated).

## Архитектура плагина

```
┌─────────────────────────────────┐
│          PAPERCLIP HOST          │
│  ┌───────────┐  ┌────────────┐  │
│  │ Manifest  │  │ Capability │  │
│  │ Validator │  │ Enforcer   │  │
│  ├───────────┤  ├────────────┤  │
│  │  Process  │  │   Event    │  │
│  │ Supervisor│  │    Bus     │  │
│  ├───────────┤  ├────────────┤  │
│  │   Job     │  │  Webhook   │  │
│  │ Scheduler │  │  Router    │  │
│  └───────────┘  └────────────┘  │
└─────────────────────────────────┘
         ▲ JSON-RPC over stdio
         │
┌────────┴────────┐
│ PLUGIN WORKER   │
│ (out-of-process)│
│ • Config        │
│ • Events        │
│ • Jobs          │
│ • Webhooks      │
│ • UI data/action│
└─────────────────┘
```

## Manifest (ключевые поля)

- `id`, `apiVersion`, `version`, `displayName`
- `categories`: connector, workspace, automation, ui
- `capabilities`: какие данные читает/пишет
- `entrypoints`: worker + опционально UI (pre-built React bundle)
- `configSchema`: JSON Schema для авто-генерации UI
- `jobs`, `webhooks`, `tools` (namespaced: `plugin:<id>:<tool>`)
- `ui`: pages, detail tabs, dashboard widgets, sidebar entries, toolbar buttons

## SDK

Плагины НЕ имеют прямого доступа к БД. SDK предоставляет typed host clients:
- `ctx.config`, `ctx.events`, `ctx.jobs`, `ctx.http`, `ctx.secrets`
- `ctx.assets`, `ctx.activity`, `ctx.state`, `ctx.entities`
- `ctx.projects`, `ctx.issues`, `ctx.agents`, `ctx.goals`
- Plugin-managed resources: agents, projects, routines, skills

## Возможности (capabilities)

Статичные, обязательные. Категории:
- **Data read:** companies, projects, issues, agents
- **Data write:** issues.create, issues.update
- **Plugin state**, runtime/integration, agent tools, UI

**Запрещено:** approval decisions, budget override, auth bypass, checkout lock override, direct DB.

## UI расширения

- React bundles, сервятся с `/_plugins/:pluginId/ui/*`
- Extension slots: страницы, вкладки, виджеты дашборда, сайдбар
- Hooks: `usePluginData`, `usePluginAction`, `useHostContext`, `useHostNavigation`
- Дизайн-токены через `@paperclipai/plugin-sdk/ui`

## Hot lifecycle

Install/uninstall/upgrade/config меняются без перезапуска сервера. При upgrade с новыми capabilities — `upgrade_pending`, оператор явно подтверждает.

## Встроенные плагины (папка packages/plugins/)

- `create-paperclip-plugin` — шаблон для создания
- `plugin-llm-wiki` — LLM Wiki
- `plugin-workspace-diff` — дифф воркспейсов
- `plugin-fake-sandbox` — фейковая песочница
- `sandbox-providers` — провайдеры песочниц
- `sdk` — SDK
- `examples` — примеры

## Ссылки

- [Архитектура Paperclip](paperclip-architecture)
- [Source: PLUGIN_SPEC.md](/raw/Papperclip/doc/plugins/PLUGIN_SPEC.md)
- [Source: PLUGIN_AUTHORING_GUIDE.md](/raw/Papperclip/doc/plugins/PLUGIN_AUTHORING_GUIDE.md)
