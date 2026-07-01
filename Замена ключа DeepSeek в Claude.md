# Замена API-ключа DeepSeek в Claude

## Где нужно обновить ключ

При замене ключа DeepSeek (`ANTHROPIC_AUTH_TOKEN`) необходимо обновить **3 файла**:

---

### 1. `~/.zshrc`
Файл конфигурации терминала (zsh). Используется при запуске из Terminal/iTerm.

```bash
# Открыть файл:
code ~/.zshrc
```

**Строка для замены:**
```bash
export ANTHROPIC_AUTH_TOKEN=sk-f86bcf4496654f22be6caf4deb931922
```

---

### 2. `~/.zshenv`
Файл окружения macOS (читается всеми shell-сессиями, включая неинтерактивные).

```bash
# Открыть файл:
code ~/.zshenv
```

**Строка для замены:**
```bash
export ANTHROPIC_AUTH_TOKEN=sk-f86bcf4496654f22be6caf4deb931922
```

---

### 3. VS Code settings.json
Настройки расширения Claude Code for VS Code (чтобы работало в VS Code, запущенном из Finder).

```bash
# Открыть файл:
code ~/Library/Application\ Support/Code/User/settings.json
```

**Блок для замены:**
```json
{
    "name": "ANTHROPIC_AUTH_TOKEN",
    "value": "sk-f86bcf4496654f22be6caf4deb931922"
}
```

---

## Быстрая замена через терминал (одной командой)

```bash
НОВЫЙ_КЛЮЧ="sk-f86bcf4496654f22be6caf4deb931922"

# Замена в .zshrc
sed -i '' "s/export ANTHROPIC_AUTH_TOKEN=sk-[a-z0-9]*/export ANTHROPIC_AUTH_TOKEN=$НОВЫЙ_КЛЮЧ/" ~/.zshrc

# Замена в .zshenv
sed -i '' "s/export ANTHROPIC_AUTH_TOKEN=sk-[a-z0-9]*/export ANTHROPIC_AUTH_TOKEN=$НОВЫЙ_КЛЮЧ/" ~/.zshenv

# Замена в VS Code settings.json
sed -i '' "s/\"value\": \"sk-[a-z0-9]*\"/\"value\": \"$НОВЫЙ_КЛЮЧ\"/" ~/Library/Application\ Support/Code/User/settings.json
```

---

## После замены

1. **Закрыть и открыть VS Code заново**, чтобы изменения в settings.json вступили в силу.
2. **Проверить работу** в терминале:
   ```bash
   export ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
   export ANTHROPIC_AUTH_TOKEN=sk-НОВЫЙ_КЛЮЧ
   export ANTHROPIC_MODEL=deepseek-v4-flash
   claude -p "hi" --max-budget-usd 1 --print --no-session-persistence
   ```

---

## Текущие настройки (на момент создания файла)

| Параметр | Значение |
|----------|----------|
| `ANTHROPIC_BASE_URL` | `https://api.deepseek.com/anthropic` |
| `ANTHROPIC_AUTH_TOKEN` | `sk-f86bcf4496654f22be6caf4deb931922` |
| `ANTHROPIC_MODEL` | `deepseek-v4-flash` |