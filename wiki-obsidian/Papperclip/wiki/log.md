# Лог Wiki Papperclip

> Хронологическая запись всей активности в wiki.

## [2026-05-28] init | Структура LLM Wiki

Инициализирован паттерн LLM Wiki для Papperclip:
- Создан `CLAUDE.md` (схема и соглашения)
- Создана `raw/` (директория исходных документов)
- Создан `wiki/index.md` (каталог содержимого)
- Создан `wiki/log.md` (лог активности)

## [2026-05-28] ingest | Исходный код Paperclip

Проинжектирован проект Paperclip (`raw/Papperclip/`):
- Прочитаны `README.md`, `package.json`, `AGENTS.md`, `ROADMAP.md`
- Обсуждено: Paperclip — open-source платформа оркестрации для AI-компаний
- Создано 5 страниц wiki:
  - [paperclip-overview](wiki/paperclip-overview.md) — что это, ключевая идея, возможности
  - [paperclip-concepts](wiki/paperclip-concepts.md) — Company, Agent, Goal, Governance, Budget и т.д.
  - [paperclip-architecture](wiki/paperclip-architecture.md) — структура репо, 12 систем, модель адаптеров
  - [paperclip-vs-alternatives](wiki/paperclip-vs-alternatives.md) — чем является/не является, таблица сравнения
  - [paperclip-roadmap](wiki/paperclip-roadmap.md) — ✅ выполнено / ⚪ в работе
- Обновлён `wiki/index.md` — все новые страницы добавлены
- Страницы связаны markdown-ссылками `[text](link)`

## [2026-05-28] lint | Проверка wiki

Проведён линтинг wiki:
- Проверены битые ссылки — не найдено
- Проверены орфанные страницы — исправлено (добавлены cross-reference ссылки)
- Исправлена вводящая в заблуждение запись в логе

## [2026-05-28] translate | Перевод на русский

Все страницы wiki переведены на русский язык:
- `overview.md`
- `paperclip-overview.md`
- `paperclip-concepts.md`
- `paperclip-architecture.md`
- `paperclip-roadmap.md`
- `paperclip-vs-alternatives.md`
- `index.md`
- `log.md`

## [2026-05-29] ingest | Глубокое исследование GitHub

Исследован GitHub-репозиторий paperclipai/paperclip:
- Прочитаны: `GOAL.md`, `PRODUCT.md`, `SPEC.md`, `SPEC-implementation.md`
- Прочитаны: `CLI.md`, `DATABASE.md`, `DEPLOYMENT-MODES.md`, `execution-semantics.md`
- Прочитаны: `PLUGIN_SPEC.md`, `adapter-plugin.md`
- Исследована структура: `server/src/services/` (103 файла), `server/src/routes/` (39 файлов), `packages/adapters/` (10 адаптеров), `packages/plugins/` (7 пакетов)
- Создано 6 новых страниц:
  - [paperclip-deployment-cli](wiki/paperclip-deployment-cli.md) — local_trusted/authenticated, onboard, configure, команды
  - [paperclip-plugins](wiki/paperclip-plugins.md) — архитектура плагинов, manifest, SDK, runtime
  - [paperclip-heartbeat-execution](wiki/paperclip-heartbeat-execution.md) — 10 адаптеров, state machine, recovery
  - [paperclip-issues](wiki/paperclip-issues.md) — issue state machine, checkout, liveness contract
  - [paperclip-database](wiki/paperclip-database.md) — Drizzle, PostgreSQL, ключевые таблицы
  - [paperclip-governance](wiki/paperclip-governance.md) — board, approvals, budget, permission matrix
- Обновлены все существующие страницы: добавлены cross-reference ссылки на новые
- Обновлены `index.md` и `overview.md`
- Wiki выросла с 5 до 11 контентных страниц

## [2026-05-29] fix | Runbook и исправление проблем Paperclip

Диагностика и исправление работающего экземпляра Paperclip:
- Сервер был запущен из глобального npm пакета (`@paperclipai/server@2026.525.0`), а не из локального проекта
- Из-за этого все эндпоинты данных возвращали 500 (несоответствие схемы БД)
- Глобальный процесс остановлен, сервер перезапущен локально через `pnpm dev`
- Отменены 4 зависших heartbeat run (CEO агент, режим running, не могли завершиться)
- Отключён heartbeat scheduler у CEO (создавал бесконечные новые ранны)
- Модель на всех 8 агентах настроена на **deepseek-chat** (DeepSeek Pro 4 через OpenAI-совместимый API)
- Возобновлён агент "Системный администратор" (был paused)
- Создана страница [runbook](wiki/paperclip-runbook.md) с инструкциями по запуску

## [2026-05-30] fix | Codex CLI + DeepSeek совместимость, перезапуск, новый CEO

Диагностика и исправление интеграции Codex CLI с DeepSeek API:
- **Проблема:** Codex CLI не принимал модель `deepseek-v4-flash` — пытался запустить её через локальный OSS-провайдер (ollama/lmstudio), падал с "No default OSS provider configured"
- **Решение:** Агенты codex_local переключены на `deepseek-chat` (Codex CLI знает эту модель через профиль `deepseek-v4-pro` в `~/.codex/config.toml`, который направляет запросы в DeepSeek API)
- **CEO** (opencode_local): модель `openrouter/deepseek/deepseek-v4-flash` — работает через OpenRouter
- Сервер перезапущен после остановки
- CEO терминален (terminated), создан новый CEO 2 с правильной конфигурацией
- Старый CEO удалён
- Создана задача YUP-19 для CEO 2: подключение к серверу WordPress

---
*Лог только для добавления. Каждая запись начинается с `## [YYYY-MM-DD]` для парсинга grep.*
