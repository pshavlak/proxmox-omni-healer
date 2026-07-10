#!/bin/bash
# Настройка UFW на LXC контейнере wordpress
set -e

echo "=== Настройка UFW ==="

# Разрешаем SSH (важно — сначала, чтобы не потерять доступ)
ufw allow 22/tcp
echo "✅ SSH (22/tcp) разрешён"

# HTTP/HTTPS
ufw allow 80/tcp
echo "✅ HTTP (80/tcp) разрешён"
ufw allow 443/tcp
echo "✅ HTTPS (443/tcp) разрешён"

# Дефолтные политики
ufw default deny incoming
echo "✅ Входящие по умолчанию запрещены"
ufw default allow outgoing
echo "✅ Исходящие по умолчанию разрешены"

# Включение
ufw --force enable
echo "✅ UFW включён"

# Статус
echo ""
echo "=== Статус UFW ==="
ufw status verbose

echo ""
echo "=== Проверка SSH ==="
# Проверяем что SSH правило активно
ufw status | grep -q "22/tcp" && echo "✅ SSH доступен" || echo "❌ SSH НЕ настроен!"

echo ""
echo "✅ UFW настроен успешно"
