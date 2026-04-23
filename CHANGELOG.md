# Changelog

## [Unreleased] - 2026-04-23

### Added
- **AI Analysis Guide** (`docs/AI-ANALYSIS-GUIDE.md`)
  - Система классификации ошибок по критичности (CRITICAL, MEDIUM, LOW)
  - Подробное описание каждого типа ошибки
  - Рекомендации по исправлению с пометками критичности
  - Пример анализа для audiobookself контейнера

### Fixed
- **AI Agent Log Analysis** (`backend/app/ai_agent.py`)
  - Добавлена система классификации критичности ошибок
  - Исправлена логика анализа `systemd-networkd-wait-online` (теперь помечена как LOW)
  - Добавлены детальные комментарии для каждого типа ошибки
  - Добавлено поле `criticality` в результат анализа
  - Добавлено поле `criticality_details` с картой критичности для каждой ошибки

### Technical Details

#### Система критичности
- **🔴 CRITICAL**: Требует немедленного действия (OOM, Disk Full)
- **🟠 MEDIUM**: Требует внимания (Connection Refused, Service Failures)
- **🟢 LOW**: Информационно (systemd-networkd-wait-online timeout в LXC)

#### Исправленные проблемы анализа
1. **systemd-networkd-wait-online**: Теперь правильно классифицируется как LOW
   - Это известная проблема LXC контейнеров
   - Не влияет на функциональность приложения
   - Сеть работает нормально (eth0 имеет IP адрес)

2. **Regex pattern matching**: Исправлена проверка с "error code (1)" на "Timeout occurred"
   - Теперь корректно парсит логи systemd-networkd-wait-online

3. **Error analysis pattern**: Добавлена пометка критичности для каждой ошибки
   - Позволяет UI показывать визуальные индикаторы (цвета)

## [Unreleased] - 2026-04-21

### Added
- **Модуль логирования** (`backend/app/logger.py`)
  - Централизованная система логирования для всех компонентов
  - Логи в консоль и файлы (`logs/app.log`, `logs/proxmox.log`, `logs/ai.log`, `logs/db.log`)
  - Уровень логирования: DEBUG
  - Форматирование с временными метками и номерами строк

- **Роут для страницы логов** (`/logs`)
  - Добавлен HTML endpoint для просмотра логов контейнеров
  - Интеграция с существующим шаблоном `logs.html`

### Fixed
- **Конфигурация**
  - Исправлена загрузка `config.env.local` с приоритетом над `config.env`
  - Добавлены абсолютные пути для BASE_DIR
  - Логирование загрузки конфигурации

- **Main.py**
  - Исправлен синтаксис f-string (использование одинарных кавычек внутри двойных)
  - Исправлен доступ к словарю: `node['node']` вместо `node[node]`
  - Добавлено детальное логирование всех API endpoints
  - Добавлен traceback для ошибок
  - Исправлены пути к статическим файлам (абсолютные пути через BASE_DIR)

- **Startup процесс**
  - Добавлено логирование инициализации всех компонентов
  - Улучшена обработка ошибок при запуске
  - Визуальное разделение этапов запуска в логах

### Changed
- **Структура логов**
  - Создана директория `/opt/proxmox-omni-healer/logs/`
  - Логи разделены по компонентам для удобства отладки

- **База данных**
  - Создана директория `/opt/proxmox-omni-healer/backend/db/`
  - Исправлена ошибка "unable to open database file"

### Technical Details

#### Исправленные ошибки
1. **SyntaxError в f-string**: `{"*" * 8}` → `{'*' * 8}`
2. **TypeError в get_cluster_info**: `node[node]` → `node['node']`
3. **RuntimeError при запуске**: Отсутствующие директории `db/` и `logs/`
4. **404 на /logs**: Добавлен отсутствующий роут

#### Добавленное логирование
- Startup: Инициализация Database, Proxmox client, AI Agent
- API calls: Все endpoints логируют запросы и результаты
- Errors: Полный traceback для всех исключений
- Proxmox: Подключение, запросы к API, количество ресурсов

### Installation Notes
После обновления необходимо:
1. Создать директории: `mkdir -p backend/db logs`
2. Перезапустить сервер для применения изменений
3. Проверить логи в `logs/server.log`

### Compatibility
- Python 3.13+
- Proxmox VE 6.17+
- Все зависимости из `requirements.txt`
