#!/bin/bash

# Proxmox Omni-Healer Installation Script

set -e

echo "🚀 Установка Proxmox Omni-Healer..."

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установите Python 3.8+"
    exit 1
fi

# Создание виртуального окружения
echo "📦 Создание виртуального окружения..."
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
echo "⬇️ Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Проверка Claude Code и OmniRoute
echo "🔍 Проверка Claude Code и OmniRoute..."
if ! command -v claude &> /dev/null; then
    echo "⚠️ Claude Code CLI не найден. Установите его вручную."
    echo "   https://docs.anthropic.com/claude-code"
fi

if ! command -v omniroute &> /dev/null; then
    echo "⚠️ OmniRoute не найден. Установите его вручную."
fi

# Создание директорий
echo "📁 Создание директорий..."
mkdir -p backend/app/db
mkdir -p backend/logs

# Копирование конфигурации
if [ ! -f config.env.local ]; then
    echo "📝 Копирование конфигурации..."
    cp config.env config.env.local
    echo "✅ Отредактируйте config.env.local с вашими настройками Proxmox"
fi

echo ""
echo "✅ Установка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте config.env.local:"
echo "   - PROXMOX_HOST, PROXMOX_TOKEN_NAME, PROXMOX_TOKEN_VALUE"
echo "   - CLAUDE_CODE_PATH, OMNIROUTE_PATH"
echo ""
echo "2. Запустите сервер:"
echo "   source venv/bin/activate"
echo "   cd backend && python -m app.main"
echo ""
echo "3. Откройте в браузере: http://localhost:8080"
