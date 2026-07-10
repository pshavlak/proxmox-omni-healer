#!/bin/bash
# Мониторинг SQLite базы данных сайта Золотаревка
# Запуск: ./deploy/check_db.sh
#
# Рекомендуемый cron (ежедневно):
# 0 6 * * * /opt/zolotarevka/deploy/check_db.sh

set -euo pipefail

# === Конфигурация ===
SITE_DIR="/opt/zolotarevka/site"
DB_PATH="${SITE_DIR}/zolotarevka.db"
MAX_SIZE_MB=500
WARN_SIZE_MB=300

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

if [ ! -f "$DB_PATH" ]; then
    echo "❌ База данных не найдена: $DB_PATH"
    exit 1
fi

echo "=== Мониторинг SQLite: $(date) ==="

# === Размер ===
SIZE_BYTES=$(stat -f%z "$DB_PATH" 2>/dev/null || stat -c%s "$DB_PATH" 2>/dev/null)
SIZE_MB=$((SIZE_BYTES / 1024 / 1024))
echo "Размер БД: ${SIZE_MB} MB"

if [ "$SIZE_MB" -gt "$MAX_SIZE_MB" ]; then
    echo "❌ БД превышает ${MAX_SIZE_MB} MB! Выполняю VACUUM..."
    sqlite3 "$DB_PATH" "VACUUM;"
    notify "⚠️ VACUUM выполнен: БД Золотаревка была ${SIZE_MB} MB"
elif [ "$SIZE_MB" -gt "$WARN_SIZE_MB" ]; then
    echo "⚠️ БД接近 лимита (${WARN_SIZE_MB} MB)"
fi

# === Целостность ===
echo -n "Проверка целостности ... "
INTEGRITY=$(sqlite3 "$DB_PATH" "PRAGMA integrity_check;" 2>/dev/null)
if [ "$INTEGRITY" = "ok" ]; then
    echo "✅"
else
    echo "❌ $INTEGRITY"
    notify "❌ Ошибка целостности БД Золотаревка: $INTEGRITY"
fi

# === Количество записей ===
echo "Статистика:"
for table in pages blocks media suggestions users; do
    COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM $table;" 2>/dev/null || echo "0")
    printf "  %-15s %s\n" "$table:" "$COUNT"
done

# === Размер WAL ===
WAL_PATH="${DB_PATH}-wal"
if [ -f "$WAL_PATH" ]; then
    WAL_SIZE=$(stat -f%z "$WAL_PATH" 2>/dev/null || stat -c%s "$WAL_PATH" 2>/dev/null)
    WAL_MB=$((WAL_SIZE / 1024 / 1024))
    if [ "$WAL_MB" -gt 50 ]; then
        echo "⚠️ WAL файл большой: ${WAL_MB} MB, выполняю checkpoint..."
        sqlite3 "$DB_PATH" "PRAGMA wal_checkpoint(TRUNCATE);"
    fi
fi

echo "✅ Мониторинг завершён"
