#!/bin/bash
# Отправка алертов в Telegram
# Использование: TG_BOT_TOKEN="xxx" TG_CHAT_ID="xxx" ./telegram-alert.sh "Сообщение"

set -e

BOT_TOKEN="${TG_BOT_TOKEN:-}"
CHAT_ID="${TG_CHAT_ID:-}"
MESSAGE="${1:-}"

if [ -z "$BOT_TOKEN" ] || [ -z "$CHAT_ID" ]; then
    echo "❌ Укажите TG_BOT_TOKEN и TG_CHAT_ID"
    echo "   TG_BOT_TOKEN=\"xxx\" TG_CHAT_ID=\"xxx\" $0 \"Сообщение\""
    exit 1
fi

if [ -z "$MESSAGE" ]; then
    echo "❌ Укажите текст сообщения"
    echo "   $0 \"Сервер недоступен\""
    exit 1
fi

# Отправка через Telegram Bot API
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendMessage" \
    -d "chat_id=${CHAT_ID}" \
    -d "text=${MESSAGE}" \
    -d "parse_mode=HTML" > /dev/null

echo "✅ Уведомление отправлено: ${MESSAGE}"
