#!/bin/bash
# Fix reverse tunnel — install autossh and replace plain SSH
set -e

echo "=== Устанавливаю autossh ==="
apt-get update -qq && apt-get install -y -qq autossh

echo "=== Обновляю systemd сервис ==="
cat > /etc/systemd/system/reverse-tunnel.service << 'EOF'
[Unit]
Description=Reverse SSH tunnel for FastAPI (autossh)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
Environment="AUTOSSH_GATETIME=0"
ExecStart=/usr/bin/autossh -M 0 \
  -o StrictHostKeyChecking=no \
  -o UserKnownHostsFile=/dev/null \
  -o ServerAliveInterval=15 \
  -o ServerAliveCountMax=3 \
  -o ExitOnForwardFailure=yes \
  -i /root/.ssh/id_reverse_tunnel \
  -R 8000:localhost:8000 \
  -N root@31.56.208.248
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl restart reverse-tunnel
sleep 3

echo "=== Проверка ==="
systemctl is-active reverse-tunnel && echo "✅ Туннель работает"
systemctl status reverse-tunnel --no-pager | head -5
