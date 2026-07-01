---
tags: [ops, paperclip, api-keys]
---

# Замена API ключа DeepSeek в Paperclip

При смене API ключа DeepSeek нужно обновить его в **5 местах**. Без этого Codex CLI будет выдавать `401 Unauthorized`.

## 1. Paperclip `.env`

```bash
# /Users/phavlak/Documents/project/Papperclip/.env
OPENAI_API_KEY=sk-...
```

**Важно:** передавать при старте сервера как env var:

```bash
OPENAI_API_KEY=sk-... pnpm dev
```

## 2. `adapterConfig` агента (через API)

Codex CLI (≥ 0.122) **игнорирует** `config.toml` и `OPENAI_API_KEY` env var — читает ключ только из `$CODEX_HOME/auth.json`.

Paperclip пишет ключ в `auth.json` ТОЛЬКО если он есть в `adapterConfig.env.OPENAI_API_KEY` агента:

```bash
curl -s -X PATCH 'http://localhost:3100/api/agents/{agentId}' \
  -H 'Content-Type: application/json' \
  -d '{
    "adapterConfig": {
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }'
```

Paperclip автоматически зарезолвит его в `auth.json` перед запуском Codex.

## 3. `~/.codex/auth.json`

Прямой доступ (если Codex запускается вне Paperclip):

```json
{
  "OPENAI_API_KEY": "sk-..."
}
```

Этот файл — symlink из `codex-home/auth.json`, поэтому обновление здесь применяется сразу.

## 4. `~/.codex/config.toml`

```toml
[model_providers.deepseek]
name = "DeepSeek"
base_url = "https://api.deepseek.com/v1/"
api_key = "sk-..."
```

Нужен для Codex UI (список моделей), но **не влияет** на аутентификацию Codex CLI.

## 5. `codex-home/config.toml`

```toml
# ~/.paperclip/instances/default/companies/{companyId}/codex-home/config.toml
[model_providers.deepseek]
api_key = "sk-..."
```

Копия из `~/.codex/`, обновлять синхронно.

## Где что читается

| Компонент | Откуда берёт ключ |
|-----------|------------------|
| **Codex CLI** (аутентификация запросов) | только `$CODEX_HOME/auth.json` — `OPENAI_API_KEY` |
| **Codex UI** (список моделей) | `config.toml` → `[model_providers.deepseek] api_key` |
| **Paperclip (resolveAdapterConfig)** | `adapterConfig.env.OPENAI_API_KEY` → пишет в `auth.json` |

## Быстрая проверка

```bash
# Где реальный ключ, который использует Codex CLI?
cat ~/.paperclip/instances/default/companies/*/codex-home/auth.json \
  | grep OPENAI_API_KEY

# Маска в ошибке — проверь endswith
# ****H8QE → последние 4 символа ключа в auth.json
```
