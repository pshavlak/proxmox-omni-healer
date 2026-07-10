# Деплой сайта Золотаревка

## Быстрый старт (локально)

```bash
# Клонировать
git clone https://github.com/pshavlak/proxmox-omni-healer
cd proxmox-omni-healer/project/Selo_Zolotarevka

# Установить
make install

# Запустить (нужен ZOLO_SECRET)
export ZOLO_SECRET="my-secret-key"
make run

# Или вручную:
cd site && source .venv/bin/activate && uvicorn app:app --reload --port 8000
```

## Деплой на сервер

```bash
# Первый раз
make deploy SERVER=root@your-server.com
make restart SERVER=root@your-server.com

# Последующие разы
make deploy-full SERVER=root@your-server.com
```

## Systemd сервис

```bash
# Копировать юнит
sudo cp deploy/zolotarevka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now zolotarevka

# Переменные окружения
sudo mkdir -p /etc/zolotarevka
sudo tee /etc/zolotarevka/env <<EOF
ZOLO_SECRET=your-secret-here
DEBUG=false
HOST=0.0.0.0
PORT=8000
EOF
```

## Nginx

```bash
sudo cp deploy/nginx-zolotarevka.conf /etc/nginx/sites-available/zolotarevka
sudo ln -s /etc/nginx/sites-available/zolotarevka /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

## Резервное копирование

```bash
# Ежедневный бэкап (через cron)
0 3 * * * /opt/zolotarevka/deploy/backup.sh

# Мониторинг БД
0 6 * * * /opt/zolotarevka/deploy/check_db.sh
```

Настройка Telegram уведомлений:

```bash
sudo tee /etc/zolotarevka/telegram.env <<EOF
TG_BOT_TOKEN=your-bot-token
TG_CHAT_ID=your-chat-id
EOF
```

## Makefile команды

```bash
make help        # Справка
make install     # Установка зависимостей
make run         # Локальный запуск
make test        # Проверка API
make deploy      # Копирование на сервер
make restart     # Перезапуск сервиса
make deploy-full # Деплой + перезапуск
make logs        # Логи сервиса
make backup      # Локальный бэкап
make check-db    # Проверка БД
make clean       # Очистка
```
