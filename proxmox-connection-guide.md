# Proxmox Connection Guide

## Основная информация

### Proxmox сервер
- **IP**: 192.168.1.110
- **Hostname**: p-home
- **SSH ключ**: `/Users/phavlak/.ssh/proxmox_key`
- **Пользователь**: root
- **Версия**: Proxmox 6.17.13-1-pve

### Команда подключения к серверу
```bash
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110
```

## Контейнеры

### Контейнер 107: Prox-IA-Agent
- **Имя**: Prox-IA-Agent
- **ID**: 107
- **IP**: 192.168.1.104 (обновлено 2026-04-24)
- **ОС**: Debian GNU/Linux 13 (trixie)
- **Сеть**: vmbr0 (bridge)

#### Команды для работы с контейнером 107
```bash
# Выполнить команду в контейнере
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- <команда>"

# Примеры:
# Проверить hostname
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- hostname"

# Проверить процессы
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- ps aux"

# Проверить логи
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- journalctl -n 50"
```

## Проект proxmox-omni-healer

### Установка в контейнере 107
- **Путь**: `/opt/proxmox-omni-healer`
- **GitHub**: https://github.com/pshavlak/proxmox-omni-healer
- **Веб-интерфейс**: http://192.168.1.104:8080 (обновлено 2026-04-24)
- **Статус**: Установлен и запущен

### Структура проекта
```
/opt/proxmox-omni-healer/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI приложение
│   │   ├── config.py         # Конфигурация
│   │   ├── logger.py         # Модуль логирования
│   │   ├── proxmox_client.py # Клиент Proxmox API
│   │   ├── ai_agent.py       # ИИ-агент
│   │   └── db_manager.py     # Работа с БД
│   └── db/                   # База данных SQLite
├── frontend/
│   ├── templates/            # HTML шаблоны
│   └── static/               # CSS/JS
├── logs/                     # Логи приложения
│   ├── server.log           # Основной лог сервера
│   ├── app.log              # Лог приложения
│   ├── proxmox.log          # Лог Proxmox клиента
│   ├── ai.log               # Лог AI агента
│   └── db.log               # Лог базы данных
├── venv/                     # Виртуальное окружение Python
├── config.env               # Базовая конфигурация
├── config.env.local         # Локальная конфигурация (токены)
└── requirements.txt         # Зависимости Python
```

### Конфигурация

#### Proxmox API
- **Host**: 192.168.1.110
- **Port**: 8006
- **User**: root@pam
- **Token Name**: omni-healer
- **Token Value**: e0098cf1-7593-4521-9b42-ce3808d8eacb
- **SSL Verify**: false

#### AI Agent
- **Claude Code Path**: /bin/claude
- **OmniRoute Path**: /bin/omniroute
- **Auto Confirm**: false

#### Server
- **Host**: 0.0.0.0
- **Port**: 8080

### Управление сервером

#### Запуск сервера
```bash
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- bash -c 'cd /opt/proxmox-omni-healer && source venv/bin/activate && cd backend && nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --log-level debug > /opt/proxmox-omni-healer/logs/server.log 2>&1 &'"
```

#### Остановка сервера
```bash
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- pkill -f uvicorn"
```

#### Проверка статуса
```bash
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- ps aux | grep uvicorn | grep -v grep"
```

#### Просмотр логов
```bash
# Основной лог сервера
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- tail -f /opt/proxmox-omni-healer/logs/server.log"

# Лог приложения
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- tail -f /opt/proxmox-omni-healer/logs/app.log"

# Все логи
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- ls -lh /opt/proxmox-omni-healer/logs/"
```

### API Endpoints

#### Cluster Info
```bash
curl http://192.168.1.104:8080/api/cluster
```

#### VM/CT Status
```bash
curl "http://192.168.1.104:8080/api/vm/{node_id}/{vm_id}/status?vm_type=lxc"
```

#### VM/CT Logs
```bash
curl "http://192.168.1.104:8080/api/vm/{node_id}/{vm_id}/logs?vm_type=lxc&limit=100"
```

#### Services Status (все контейнеры)
```bash
curl http://192.168.1.104:8080/api/services/status
```

#### Перезапуск неисправных служб в контейнере
```bash
curl -X POST http://192.168.1.104:8080/api/services/{ct_id}/restart-failed
```

#### Перезапуск конкретной службы
```bash
curl -X POST http://192.168.1.104:8080/api/services/{ct_id}/restart/{service_name}
```

### Веб-интерфейс страницы

#### Главная страница
```
http://192.168.1.104:8080/
```

#### Страница статуса служб
```
http://192.168.1.104:8080/services
```

#### Страница логов контейнера
```
http://192.168.1.104:8080/logs?node={node_id}&vmid={vm_id}&type=lxc
```

### Зависимости Python
- fastapi==0.109.0
- uvicorn[standard]==0.27.0
- proxmoxer==2.0.1
- requests==2.31.0
- python-dotenv==1.0.0
- aiosqlite==0.19.0
- websockets==12.0
- jinja2==3.1.3
- python-multipart==0.0.6

### Переустановка проекта

```bash
# 1. Подключиться к Proxmox
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110

# 2. Остановить сервер
pct exec 107 -- pkill -f uvicorn

# 3. Удалить старую установку
pct exec 107 -- rm -rf /opt/proxmox-omni-healer

# 4. Клонировать репозиторий
pct exec 107 -- bash -c 'cd /opt && git clone https://github.com/pshavlak/proxmox-omni-healer.git'

# 5. Запустить установку
pct exec 107 -- bash -c 'cd /opt/proxmox-omni-healer && chmod +x scripts/install.sh && ./scripts/install.sh'

# 6. Настроить конфигурацию (токены уже есть в этом документе)
# Создать config.env.local с параметрами из раздела "Конфигурация"

# 7. Создать директории
pct exec 107 -- mkdir -p /opt/proxmox-omni-healer/backend/db
pct exec 107 -- mkdir -p /opt/proxmox-omni-healer/logs

# 8. Запустить сервер (команда из раздела "Управление сервером")
```

### Локальная копия репозитория
- **Путь на Mac**: `/tmp/proxmox-omni-healer`
- Для обновления: `cd /tmp/proxmox-omni-healer && git pull`

### Важные исправления (применены)
1. ✅ Добавлен модуль логирования (logger.py)
2. ✅ Исправлены пути к статике (абсолютные пути)
3. ✅ Настроена загрузка config.env.local
4. ✅ Исправлен синтаксис f-string в main.py
5. ✅ Исправлен доступ к node['node'] в main.py
6. ✅ Созданы директории db/ и logs/
7. ✅ Установлены все зависимости

### Статус системы
- ✅ Database initialized
- ✅ Proxmox client connected (192.168.1.110:8006)
- ✅ AI Agent initialized
- ✅ API работает: 1 node, 10 resources
- ✅ Логирование настроено (уровень DEBUG)
- ✅ Роут /logs добавлен и работает
- ✅ CORS middleware добавлен
- ✅ Страница /services для статуса служб
- ✅ API /api/services/status работает

### Резервные копии

#### Последняя резервная копия
- **Файл**: `/Users/phavlak/Documents/proxmox-omni-healer-backup-20260421-200730.tar.gz`
- **Размер**: 100KB
- **Дата**: 2026-04-21 20:07
- **Содержимое**: Весь проект без venv и __pycache__

#### Создание новой резервной копии
```bash
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- bash -c 'cd /opt && tar --exclude=venv --exclude=__pycache__ --exclude=*.pyc -czf proxmox-omni-healer-backup-\$(date +%Y%m%d-%H%M%S).tar.gz proxmox-omni-healer'"

# Скопировать на Mac
ssh -i /Users/phavlak/.ssh/proxmox_key root@192.168.1.110 "pct exec 107 -- cat /opt/proxmox-omni-healer-backup-*.tar.gz" > ~/Documents/backup.tar.gz
```

### GitHub Repository

#### Последний коммит
- **Commit**: `1649dce`
- **Дата**: 2026-04-23 13:52
- **Сообщение**: "Add services status page and CORS support"
- **Ссылка**: https://github.com/pshavlak/proxmox-omni-healer/commit/1649dce

#### Изменения в коммите
- ✅ Добавлен CORS middleware для решения проблем с access control
- ✅ Добавлен маршрут `/logs` для страницы логов контейнеров
- ✅ Добавлена отдельная страница `/services` для статуса служб
- ✅ Добавлен файл `frontend/templates/services.html`
- ✅ Обновлен `backend/app/main.py` — новые маршруты и CORS
- ✅ Обновлен `backend/app/proxmox_client.py` — методы для управления сервисами
- ✅ Обновлен `frontend/templates/index.html` — кнопка "Статус служб"

#### Работа с репозиторием
```bash
# Обновить локальную копию
cd /tmp/proxmox-omni-healer && git pull

# Посмотреть последние коммиты
cd /tmp/proxmox-omni-healer && git log --oneline -5

# Посмотреть изменения в последнем коммите
cd /tmp/proxmox-omni-healer && git show HEAD
```

### Troubleshooting

#### Сервер не запускается
1. Проверить логи: `tail -50 /opt/proxmox-omni-healer/logs/server.log`
2. Проверить синтаксис Python: `python -m py_compile backend/app/main.py`
3. Проверить директории: `ls -la backend/db/ logs/`

#### 404 ошибки в веб-интерфейсе
1. Проверить роуты в main.py: `grep "@app.get" backend/app/main.py`
2. Проверить шаблоны: `ls frontend/templates/`
3. Перезапустить сервер

#### Ошибки подключения к Proxmox
1. Проверить токен: `grep TOKEN config.env.local`
2. Проверить доступность API: `curl -k https://192.168.1.110:8006/api2/json/version`
3. Проверить логи Proxmox клиента: `tail logs/proxmox.log`

---

*Создано: 2026-04-21*
*Последнее обновление: 2026-04-24 14:21*

### Последние изменения (2026-04-24)
- ✅ Контейнер 107 перезагружен
- ✅ IP обновлён: 192.168.1.104 (было 192.168.1.192)
- ✅ Сервер запущен и работает
- ✅ Все API endpoints доступны

### Последние изменения (2026-04-24 15:50)
- ✅ Блок "Предложения ИИ" перемещён под "Обзор кластера"
- ✅ Добавлена прокрутка для блока "Предложения ИИ"
- ✅ Исправлено открытие логов контейнеров в новой вкладке
- ✅ Изменён фон панели на пользовательское изображение
- ✅ Фоновое изображение: `/opt/proxmox-omni-healer/frontend/static/background.png` (1.9MB)

### Последние изменения (2026-04-26 03:30)
- ✅ Восстановлен CSS после повреждения
- ✅ Фоновое изображение работает корректно
- ✅ Шапка отображается правильно (не на половину страницы)
- ✅ Все функции панели работают
- ✅ Сервер стабильно работает (uptime 2 дня)
