# 🤖 Proxmox Omni-Healer

Автоматизированная система мониторинга и исправления ошибок в инфраструктуре Proxmox с использованием Claude Code CLI и OmniRoute.

## 📋 Возможности

- **Мониторинг VM/CT**: Отображение всех виртуальных машин и контейнеров в кластере Proxmox
- **Анализ логов**: Автоматическое обнаружение ошибок в логах
- **ИИ-предложения**: Генерация предложений по исправлению через Claude Code + OmniRoute
- **Режим подтверждения**: "Предложение → Подтверждение" или автоматическое выполнение
- **Веб-интерфейс**: Удобный дашборд для управления

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────┐
│              Web Interface (HTMX/JS)                │
├─────────────────────────────────────────────────────┤
│              FastAPI Backend (Python)               │
├──────────────┬────────────────────┬─────────────────┤
│  Proxmox     │   AI Agent         │   Database      │
│  Client      │   (Claude+Route)   │   (SQLite)      │
└──────────────┴────────────────────┴─────────────────┘
```

## 🚀 Установка

### 1. Клонирование и установка

```bash
cd /workspace/proxmox-omni-healer
./scripts/install.sh
```

### 2. Настройка конфигурации

Отредактируйте `config.env.local`:

```bash
# Proxmox API
PROXMOX_HOST="192.168.1.100"
PROXMOX_PORT="8006"
PROXMOX_USER="root@pam"
PROXMOX_TOKEN_NAME="omni_healer"
PROXMOX_TOKEN_VALUE="your-token-here"

# AI Agent
CLAUDE_CODE_PATH="/usr/local/bin/claude"
OMNIROUTE_PATH="/usr/local/bin/omniroute"
AUTO_CONFIRM="false"
```

### 3. Запуск

```bash
source venv/bin/activate
cd backend
python -m app.main
```

Откройте браузер: http://localhost:8080

## 🔑 Создание токена Proxmox

1. Зайдите в Proxmox VE Web UI
2. Permissions → API Tokens → Add
3. Создайте токен с правами PVEAuditor (минимальные права)

## 📁 Структура проекта

```
proxmox-omni-healer/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI приложение
│       ├── config.py         # Конфигурация
│       ├── proxmox_client.py # Клиент Proxmox API
│       ├── ai_agent.py       # ИИ-агент (Claude+OmniRoute)
│       └── db_manager.py     # Работа с БД
├── frontend/
│   ├── templates/
│   │   └── index.html        # Главная страница
│   └── static/
│       ├── style.css         # Стили
│       └── script.js         # JS логика
├── scripts/
│   ├── install.sh            # Скрипт установки
│   └── setup_ssh.sh          # Настройка SSH
├── requirements.txt
├── config.env
└── README.md
```

## 🔒 Безопасность

- Используйте токены API с минимальными правами
- Не храните токены в git
- Включайте режим подтверждения перед автоисполнением

## 📝 Лицензия

MIT
