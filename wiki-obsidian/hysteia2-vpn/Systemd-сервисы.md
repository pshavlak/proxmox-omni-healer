# Systemd-сервисы

Два сервиса на сервере. См. структурированную версию: [[entities/hysteria-2-server]].

## hysteria-server

```ini
[Unit]
Description=Hysteria Server Service (config.yaml)
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/hysteria server --config /etc/hysteria/config.yaml
User=hysteria
Group=hysteria
Environment=HYSTERIA_LOG_LEVEL=info
CapabilityBoundingSet=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
AmbientCapabilities=CAP_NET_ADMIN CAP_NET_BIND_SERVICE CAP_NET_RAW
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

## hysteria-manager

```ini
[Unit]
Description=Hysteria 2 Manager Panel
After=network.target hysteria-server.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/hysteria-manager/app.py
Restart=on-failure
RestartSec=5s
```

## Управление

```bash
systemctl status hysteria-server
systemctl status hysteria-manager
systemctl restart hysteria-server
journalctl -u hysteria-server -n 50
```

## Источники
- `sources/Hysteria2/systemd/hysteria-server.service`
- `sources/Hysteria2/systemd/hysteria-manager.service`
