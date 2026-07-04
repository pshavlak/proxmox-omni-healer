---
title: Инфраструктура и деплой
created: 2026-07-03
updated: 2026-07-03
type: entity
tags: [инфраструктура, server, ssh, deploy, ssl, nginx, proxmox, lxc, wireguard, project: new]
sources: [deploy/README_DEPLOY.md, deploy/fix-tunnel.sh, deploy/nginx-zolotarevka.conf, deploy/zolotarevka.service, ssh/]
---

# Инфраструктура и деплой

## Схема подключения

```
🌍 DNS: золотаревка.рф → 31.56.208.248
    ↓
🖥️ VPS server-rm7kbp (31.56.208.248) — nginx :80/:443
   │
   ├── WireGuard 10.0.0.1 ←→ 10.0.0.2
   │                       │
   │                 📦 LXC wordpress (192.168.1.64) — VMID 105
   │                    ├── FastAPI :8000    ← золотаревка.рф
   │                    └── Apache/WP :80    ← zolotarevka.yupiterpro.ru (legacy)
   │                    ↑
   │              🖥️ Proxmox p-home (192.168.1.110)
   │
   └── (альтернативно: reverse SSH tunnel через autossh)
```

## Серверы

### VPS `server-rm7kbp` (31.56.208.248) — основной

| Параметр | Значение |
|----------|----------|
| **IP** | `31.56.208.248` |
| **OS** | Ubuntu 24.04.4 LTS |
| **nginx** | 1.24.0 |
| **Python** | 3.12.3 |
| **SSH** | `ssh zolotarevka-vps` (ключ `~/.ssh/id_ed25519`) |
| **Роль** | Публичный вход (:80/:443), прокси на LXC через WireGuard |

Маршрутизация nginx:

| Домен | Upstream | Назначение |
|-------|----------|------------|
| `золотаревка.рф` / `xn--80aaflivdxbvu.xn--p1ai` | `10.0.0.2:8000` | FastAPI (новый проект) |
| `www.золотаревка.рф` / `www.xn--80aaflivdxbvu.xn--p1ai` | `10.0.0.2:8000` | FastAPI (новый проект) |
| `zolotarevka.yupiterpro.ru` | `10.0.0.2:80` | WordPress (legacy) |

### Proxmox `p-home` (192.168.1.110)

- Хост для LXC-контейнеров
- **SSH ключ**: `~/.ssh/proxmox_key`
- LXC контейнер `wordpress` (VMID 105)

### LXC `wordpress` (VMID 105)

| Параметр | Значение |
|----------|----------|
| **IP** | `192.168.1.64` |
| **WireGuard IP** | `10.0.0.2` |
| **SSH** | `ssh wordpress-lxc` (ключ `~/.ssh/id_ed25519`) |
| **FastAPI** | `/var/www/zolotarevka-fastapi`, uvicorn `:8000` |
| **Systemd** | `zolotarevka-fastapi.service` |
| **WordPress** | `/var/www/html/wordpress`, Apache `:80` |
| **Бэкап FastAPI** | `/var/www/zolotarevka-fastapi.backup-20260628_172214` |

Проверки в контейнере:

```bash
ssh wordpress-vm "systemctl status zolotarevka-fastapi.service"
ssh wordpress-vm "curl http://127.0.0.1:8000/"
ssh wordpress-vm "curl http://127.0.0.1:8000/admin/"
ssh wordpress-vm "curl http://127.0.0.1:8000/api/pages"
ssh wordpress-vm "curl http://127.0.0.1/"   # WordPress
```

### VPS `62.113.105.38` — старый (выведен из эксплуатации для сайта)

- **SSH**: `ssh -i /Users/phavlak/.ssh/id_hysteria_rsa root@62.113.105.38`
- **Hysteria**: UDP `8443`
- Ранее направлял `золотаревка.рф` через nginx. Не используется.

## SSH-ключи

| Файл | Назначение |
|------|-----------|
| `ssh/id_31_56_208_248` | Основной ключ для входа на `root@31.56.208.248` |
| `ssh/id_tunnel` | Ключ для reverse tunnel (указан в `fix-tunnel.sh`) |

## DNS

Актуальные записи (проверено 2026-06-30):

| Тип | Хост | Значение | Статус |
|-----|------|----------|--------|
| A | `золотаревка.рф` / `xn--80aaflivdxbvu.xn--p1ai` | `31.56.208.248` | ✅ |
| A | `www.золотаревка.рф` / `www.xn--80aaflivdxbvu.xn--p1ai` | `31.56.208.248` | ✅ |

Проверка:

```bash
dig +short @8.8.8.8 xn--80aaflivdxbvu.xn--p1ai
dig +short @8.8.8.8 www.xn--80aaflivdxbvu.xn--p1ai
```

## SSL

Сертификат выпускать через certbot:

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx \
  -d xn--80aaflivdxbvu.xn--p1ai \
  -d www.xn--80aaflivdxbvu.xn--p1ai \
  --non-interactive --agree-tos \
  -m admin@yupiterpro.ru \
  --redirect
```

Проверка после SSL:

```bash
nginx -t && systemctl reload nginx
curl -I https://xn--80aaflivdxbvu.xn--p1ai/
curl -I https://www.xn--80aaflivdxbvu.xn--p1ai/
curl -I https://zolotarevka.yupiterpro.ru/
```

## Деплой (новый проект FastAPI)

### Быстрый запуск на сервере

```bash
cd /opt/zolotarevka/site
chmod +x install.sh start.sh
./install.sh
HOST=0.0.0.0 PORT=8000 ./start.sh
```

Проверка:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/admin/
curl http://127.0.0.1:8000/api/pages
```

### Systemd-сервис

Файл: `deploy/zolotarevka.service`

```bash
sudo cp deploy/zolotarevka.service /etc/systemd/system/zolotarevka.service
sudo systemctl daemon-reload
sudo systemctl enable --now zolotarevka
sudo systemctl status zolotarevka
```

### Nginx config

Файл: `deploy/nginx-zolotarevka.conf` (на VPS или на LXC)

```bash
sudo cp deploy/nginx-zolotarevka.conf /etc/nginx/sites-available/zolotarevka
sudo ln -s /etc/nginx/sites-available/zolotarevka /etc/nginx/sites-enabled/zolotarevka
sudo nginx -t
sudo systemctl reload nginx
```

### Reverse SSH tunnel

При нестабильном WireGuard используется reverse tunnel через autossh.

Файл: `deploy/fix-tunnel.sh`

```bash
# Установка autossh на LXC
./deploy/fix-tunnel.sh
# Создаёт systemd-сервис reverse-tunnel.service
# Пробрасывает порт 8000 LXC → VPS 31.56.208.248
```

### Что переносить на сервер

**Обязательно:**
- `app.py`, `config.py`, `database.py`, `models.py`
- `requirements.txt`, `start.sh`
- `admin/` (SPA-админка)
- `templates/` (Jinja2-шаблоны)
- `static/` (css, js, uploads)
- `zolotarevka.db` (если нужен существующий контент)

**Не переносить:**
- `.venv/`, `.git/`, `__pycache__/`, `.DS_Store`
- `archive/` (WordPress legacy)

## Связанные страницы

- [[fastapi-architecture]] — архитектура нового проекта (FastAPI)
- [[admin-panel-redesign]] — старый проект WordPress (legacy)
- [[SCHEMA]] — схема вики
