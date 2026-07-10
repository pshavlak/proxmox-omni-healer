#!/bin/bash
# Health check скрипт для сайта Золотаревка
set -e

# --- Конфигурация ---
BASE_URL="${1:-http://127.0.0.1:8000}"
FAILED=0

echo "=== Health Check: Золотаревка ($(date)) ==="

# 1. /health
echo -n "1. /health ... "
HEALTH=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" 2>/dev/null)
if [ "$HEALTH" = "200" ]; then
    echo "✅ [$HEALTH]"
else
    echo "❌ [$HEALTH]"
    FAILED=1
fi

# 2. / (главная)
echo -n "2. Главная ... "
HOME=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/" 2>/dev/null)
if [ "$HOME" = "200" ]; then
    echo "✅ [$HOME]"
else
    echo "❌ [$HOME]"
    FAILED=1
fi

# 3. /admin/
echo -n "3. Админка ... "
ADMIN=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/admin/" 2>/dev/null)
if [ "$ADMIN" = "200" ]; then
    echo "✅ [$ADMIN]"
else
    echo "❌ [$ADMIN]"
    FAILED=1
fi

# 4. /api/pages
echo -n "4. API Pages ... "
API=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/pages" 2>/dev/null)
if [ "$API" = "200" ]; then
    echo "✅ [$API]"
else
    echo "❌ [$API]"
    FAILED=1
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo "✅ Все проверки пройдены"
    exit 0
else
    echo "❌ Некоторые проверки не пройдены"
    exit 1
fi
