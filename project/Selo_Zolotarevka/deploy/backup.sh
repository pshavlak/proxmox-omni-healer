#!/bin/bash
# Резервное копирование сайта Золотаревка
# Запуск: ./deploy/backup.sh
#
# Рекомендуемый cron (ежедневно в 3:00):
# 0 3 * * * /opt/zolotarevka/deploy/backup.sh

set -euo pipefail

# === Конфигурация ===
SITE_DIR="/opt/zolotarevka/site"
BACKUP_DIR="/opt/zolotarevka/backups"
DB_PATH="${SITE_DIR}/zolotarevka.db"
UPLOAD_DIR="${SITE_DIR}/static/uploads"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="zolotarevka_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# === Telegram уведомления (опционально) ===
TG_ENV="/etc/zolotarevka/telegram.env"
if [ -f "$TG_ENV" ]; then
    source "$TG_ENV"
fi

notify() {
    local msg="$1"
    echo "$msg"
    if [ -n "${TG_BOT_TOKEN:-}" ] && [ -n "${TG_CHAT_ID:-}" ]; then
        curl -s -X POST "https://api.telegram.org/bot${TG_BOT_TOKEN}/sendMessage" \
            -d "chat_id=${TG_CHAT_ID}" \
            -d "text=${msg}" \
            -d "parse_mode=HTML" > /dev/null
    fi
}

# === Создаём директории ===
mkdir -p "$BACKUP_DIR"
mkdir -p "$BACKUP_PATH"

echo "=== Резервное копирование: ${TIMESTAMP} ==="

# === 1. Бэкап SQLite ===
echo -n "1. SQLite ... "
if [ -f "$DB_PATH" ]; then
    sqlite3 "$DB_PATH" "VACUUM;"
    cp "$DB_PATH" "${BACKUP_PATH}/zolotarevka.db"
    sqlite3 "${BACKUP_PATH}/zolotarevka.db" "VACUUM;"
    echo "✅ ($(du -h "${BACKUP_PATH}/zolotarevka.db" | cut -f1))"
else
    echo "⚠️ Файл БД не найден"
fi

# === 2. Бэкап uploads ===
echo -n "2. Uploads ... "
if [ -d "$UPLOAD_DIR" ]; then
    cp -r "$UPLOAD_DIR" "${BACKUP_PATH}/uploads"
    echo "✅ ($(du -sh "${BACKUP_PATH}/uploads" | cut -f1))"
else
    echo "⚠️ Директория uploads не найдена"
fi

# === 3. Бэкап конфигов ===
echo -n "3. Config ... "
if [ -f "/etc/zolotarevka/env" ]; then
    cp /etc/zolotarevka/env "${BACKUP_PATH}/env"
    echo "✅"
else
    echo "⚠️ Файл env не найден"
fi

# === 4. Архивация ===
echo -n "4. Архивация ... "
cd "$BACKUP_DIR"
tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
rm -rf "$BACKUP_NAME"
echo "✅ ${BACKUP_NAME}.tar.gz"

# === 5. Удаляем старые бэкапы ===
echo -n "5. Очистка (>${RETENTION_DAYS} дней) ... "
find "$BACKUP_DIR" -name "zolotarevka_*.tar.gz" -type f -mtime +${RETENTION_DAYS} -delete
echo "✅"

# === 6. Размер бэкапа ===
SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
echo ""
echo "✅ Бэкап завершён: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz (${SIZE})"
notify "✅ Бэкап Золотаревка: ${SIZE}"
