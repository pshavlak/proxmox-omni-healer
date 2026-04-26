# Proxmox Omni-Healer - Быстрый старт

## Установка

### 1. Автоматическая установка (рекомендуется)

```bash
cd /workspace/proxmox-omni-healer
sudo ./scripts/install.sh
```

### 2. Ручная установка

```bash
# Создать виртуальное окружение
cd /workspace/proxmox-omni-healer/backend
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать конфиг
cp ../config/settings.example.py ../config/settings.py
```

## Настройка

### 1. Proxmox API Token (рекомендуется)

В Proxmox VE создайте API токен:
```
Datacenter → Permissions → API Tokens → Add
```

Запишите токен в `config/settings.py`:
```python
PROXMOX_TOKEN_NAME = "omni-healer"
PROXMOX_TOKEN_VALUE = "uuid-here"
```

### 2. SSH ключ для доступа к гостям

```bash
# Ключ будет создан автоматически при установке
# Или вручную:
ssh-keygen -t ed25519 -f /root/.ssh/id_ed25519

# Добавьте публичный ключ во все VM/CT:
cat /root/.ssh/id_ed25519.pub
```

### 3. Claude Code CLI + OmniRoute

Установите локально в контейнере:

```bash
# Claude Code CLI
npm install -g @anthropic-ai/claude-code

# OmniRoute (следуйте официальной документации)
# https://github.com/omniroute/omniroute
```

Проверьте установку:
```bash
claude --version
omniroute --version
```

## Запуск

### Через systemd (после установки)
```bash
systemctl start proxmox-omni-healer
systemctl enable proxmox-omni-healer
```

### Вручную для тестирования
```bash
cd /workspace/proxmox-omni-healer/backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Доступ к интерфейсу

Откройте в браузере: `http://localhost:8000`

## API Endpoints

### Мониторинг
- `GET /api/nodes/scan` - Сканировать все ресурсы
- `GET /api/nodes/summary` - Получить сводку
- `GET /api/nodes/{node}/vms` - VM на узле
- `GET /api/nodes/{node}/containers` - Контейнеры на узле

### Логи и ошибки
- `GET /api/logs/errors` - Список ошибок
- `POST /api/logs/errors/{id}/acknowledge` - Подтвердить ошибку

### AI Healer
- `GET /api/ai/status` - Статус AI
- `POST /api/ai/mode/auto?enable=true` - Включить авто-режим
- `GET /api/ai/commands` - Список команд
- `POST /api/ai/commands/{id}/approve` - Одобрить команду
- `POST /api/ai/commands/{id}/reject` - Отклонить команду
- `POST /api/ai/analyze/{error_id}` - Анализировать ошибку

## Режимы работы

### Ручной (по умолчанию)
1. AI анализирует ошибку
2. Предлагает команду для исправления
3. Пользователь подтверждает или отклоняет
4. Команда выполняется через Claude Code + OmniRoute

### Автоматический
1. Включается кнопкой в интерфейсе
2. AI автоматически выполняет команды
3. Ограничение: макс. 10 команд в час
4. Все действия логируются

## Структура проекта

```
proxmox-omni-healer/
├── backend/app/          # Python FastAPI бэкенд
│   ├── api/             # API роуты
│   ├── models/          # Модели данных
│   ├── services/        # Бизнес-логика
│   └── utils/           # Утилиты
├── frontend/src/pages/  # HTML шаблоны
├── scripts/             # Скрипты установки
└── config/              # Конфигурация
```

## Логи

- Приложение: `/var/log/omni-healer/app.log`
- OmniRoute: `/var/log/omni-healer/omniroute.log`

## Безопасность

⚠️ **Важно:**
- Используйте API токены вместо паролей
- Ограничьте доступ к веб-интерфейсу (firewall, reverse proxy)
- Регулярно обновляйте систему
- Проверяйте команды перед авто-выполнением

## Требования

- Proxmox VE 7.x+
- Debian 12 / Ubuntu 22.04+
- 6 GB RAM минимум
- Python 3.11+
- Claude Code CLI
- OmniRoute

## Поддержка

При возникновении проблем проверьте:
1. Логи приложения
2. Доступность Proxmox API
3. Наличие SSH ключей на гостях
4. Работоспособность Claude Code CLI
