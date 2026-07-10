#!/bin/bash
# Настройка SSL через certbot для сайта Золотаревка
set -e

DOMAINS="-d xn--80aaflivdxbvu.xn--p1ai -d www.xn--80aaflivdxbvu.xn--p1ai"
EMAIL="admin@yupiterpro.ru"
NGINX_CONF="/etc/nginx/sites-available/zolotarevka"

echo "=== 1. Установка certbot ==="
apt-get update -qq
apt-get install -y -qq certbot python3-certbot-nginx

echo "=== 2. Выпуск сертификата ==="
certbot --nginx $DOMAINS \
  --non-interactive --agree-tos \
  -m $EMAIL \
  --redirect

echo "=== 3. HSTS в nginx ==="
if ! grep -q "Strict-Transport-Security" "$NGINX_CONF"; then
  # Добавляем HSTS в server block HTTPS
  sed -i '/ssl_certificate_key/a \\tadd_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;' "$NGINX_CONF"
fi

echo "=== 4. Проверка nginx ==="
nginx -t && systemctl reload nginx

echo "=== 5. Настройка автообновления ==="
# certbot уже создаёт systemd timer
systemctl enable certbot.timer
systemctl start certbot.timer
systemctl status certbot.timer --no-pager | head -5

echo "=== 6. Проверка HTTPS ==="
for domain in xn--80aaflivdxbvu.xn--p1ai www.xn--80aaflivdxbvu.xn--p1ai; do
  echo "Проверка https://$domain ..."
  curl -sI "https://$domain" | head -5
  echo "---"
done

echo ""
echo "✅ SSL настроен!"
echo "Автообновление через certbot.timer (запуск 2 раза в сутки)"
