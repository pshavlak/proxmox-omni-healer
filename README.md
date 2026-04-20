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

### Быстрая установка (рекомендуется)

```bash
cd /opt
git clone https://github.com/pshavlak/proxmox-omni-healer.git
cd proxmox-omni-healer
./scripts/install.sh
```

### Ручная установка

#### 1. Клонирование и установка

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

#### Разработка:
```bash
source venv/bin/activate
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Продакшен (используйте готовый скрипт):
```bash
./start.sh
```

Откройте браузер: http://localhost:8000

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

## 📦 Продакшен развертывание

### Системные требования
- Python 3.11+
- 2GB RAM минимум
- Proxmox VE 7.0+
- Доступ к Proxmox API

### Установленные компоненты
- FastAPI 0.136.0 (веб-фреймворк)
- Proxmoxer 2.3.0 (Proxmox API клиент)
- Paramiko 4.0.0 (SSH подключения)
- SQLAlchemy 2.0.49 (база данных)
- WebSockets 16.0 (реальное время)

### Структура продакшен установки
```
/opt/proxmox-omni-healer/
├── venv/                 # Виртуальное окружение Python
├── data/                 # Данные приложения
├── start.sh             # Скрипт запуска
├── backend/             # Backend код
├── frontend/            # Frontend файлы
└── config/              # Конфигурация
```

## 🔒 Безопасность

- Используйте токены API с минимальными правами
- Не храните токены в git
- Включайте режим подтверждения перед автоисполнением

## 📝 Лицензия

MIT
