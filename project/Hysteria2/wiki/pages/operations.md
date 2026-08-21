# Operations

## Read-Only Health Check

Local:

```bash
curl -Ik --connect-timeout 10 https://hist.yupiterpro.ru/
curl -Ik --connect-timeout 10 https://hist.yupiterpro.ru/44169d2dba4d0fd5/
nc -vz -w 10 62.113.105.38 443
nc -vz -w 10 62.113.105.38 8443
nc -vz -w 10 193.164.155.153 18443
```

Expected:

- `https://hist.yupiterpro.ru/` returns the public placeholder page.
- `https://hist.yupiterpro.ru/44169d2dba4d0fd5/` reaches the hidden admin panel login.

Main server:

```bash
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38
systemctl is-active hysteria-server hysteria-manager nginx
ss -lntup | grep -E ":(443|8081)"
ss -lunp | grep -E ":8443"
```

Cascade server:

```bash
ssh -i ssh-keys/id_193_164_155_153 root@193.164.155.153
systemctl is-active wireproxy x-ui crowdsec
ss -lntup | grep -E ":(443|18443|40000)"
```

## Mini App Deploy

Files live in `/opt/telegram-miniapp/`. Services: `telegram-miniapp` (port 8085) and `telegram-bot`.

Standard deploy (does **not** touch `hysteria-server`, `hysteria-manager`, `nginx`):

```bash
# From local project root:
scp -i ssh-keys/id_hysteria_rsa \
    telegram_app/backend/server.py \
    telegram_app/backend/db.py \
    root@62.113.105.38:/opt/telegram-miniapp/backend/

# Syntax check on server:
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38 \
  "python3 -m py_compile /opt/telegram-miniapp/backend/server.py && echo OK"

# DB migration (safe ALTER TABLE ADD COLUMN):
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38 \
  "cd /opt/telegram-miniapp && python3 -c 'from backend.db import init_db; init_db()'"

# Restart Mini App only:
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38 \
  "systemctl restart telegram-miniapp telegram-bot"
```

Post-deploy check:
```bash
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38 \
  "systemctl is-active telegram-miniapp telegram-bot && \
   curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8085/api/user/me"
# Expected: active active 200
```

### Admin API Reference (as of 2026-08-21)

| Method | Path | Описание |
|--------|------|----------|
| POST | `/api/admin/client/set-limit` | `{id, limit_gb}` — лимит трафика. `0`/`null` = безлимит |
| POST | `/api/admin/client/grant-trial` | `{telegram_user_id, hours}` — выдать/продлить триал |
| POST | `/api/admin/extend` | `{id, days}` — продление подписки |
| POST | `/api/admin/hysteria/create` | Создать Hysteria аккаунт |
| POST | `/api/admin/client/delete` | Удалить miniapp аккаунт |
| GET  | `/api/admin/clients` | Список всех клиентов |
| GET  | `/api/admin/client?id=N` | Детали клиента |

### Timers on Main Server (as of 2026-08-21)

| Timer | Schedule | Описание |
|-------|----------|----------|
| `backup-db.timer` | daily 03:00 UTC | Бэкап `app.db` → Telegram admins |
| `expire-subscriptions.timer` | daily 00:00 UTC | Истечение подписок + уведомления |
| `hysteria-stats-collector.timer` | every 5 min | Трафик/устройства из Hysteria API |
| `expired-promocode-key-cleanup.timer` | every 5 min | Удаление истёкших промокод-ключей |

## Manager Deploy

Do not restart `hysteria-server` for manager-only changes.

1. Copy changed files to `/tmp/`.
2. Validate syntax on the server.
3. Back up current deployed files with timestamp.
4. Install new files into `/opt/hysteria-manager/`.
5. Restart `hysteria-manager`.
6. Verify `/auth` and full Hysteria client path.

## 3x-ui / x-ui Update Notes

Installed cascade panel is `alireza0/x-ui`, not `MHSanaei/3x-ui` major version 3.x.

Safe update rule:

- Stay within the same `alireza0/x-ui` release line unless migration is explicitly planned.
- Back up `/etc/x-ui/x-ui.db`, `/etc/x-ui/`, `/usr/local/x-ui/`, `/etc/systemd/system/x-ui.service`, `/etc/xray-cascade/`, and `/etc/wireguard/proxy.conf` before update.
- Do not replace `/etc/x-ui/x-ui.db` during binary update.
- After update, verify database tables/counts, `x-ui`, `wireproxy`, panel ports, cascade SOCKS from main server, and full Hysteria client path.

Latest successful update:

- 2026-08-11: `x-ui 1.11.1` -> `x-ui 1.11.4`.
- Full backup archive: `/root/backup-3xui-20260811-125329.tar.gz`.
- Pre-update binary backup: `/root/x-ui-pre-v1.11.4-20260811-125852`.
- Pre-update DB backup: `/root/x-ui-db-pre-v1.11.4-20260811-125852.db`.

## Hysteria Client Smoke

Use a temporary local config with a valid user password:

```yaml
server: hist.yupiterpro.ru:8443
auth: [redacted]
tls:
  sni: hist.yupiterpro.ru
  insecure: false
socks5:
  listen: 127.0.0.1:19443
```

Then:

```bash
hysteria --disable-update-check -l info client -c /tmp/config.yaml
curl --socks5-hostname 127.0.0.1:19443 https://api.ipify.org
```

Expected IP: `193.164.155.153`.

## Hysteria Stats Collection

Mini App Hysteria traffic/device stats use Hysteria's local Traffic Stats API:

- Config: `/etc/hysteria/config.yaml`, `trafficStats.listen: 127.0.0.1:9999`.
- Secret: `/etc/telegram-miniapp.env`, `HYSTERIA_STATS_SECRET`.
- Collector: `hysteria-stats-collector.service`.
- Schedule: `hysteria-stats-collector.timer`, every 5 minutes.

Safe checks:

```bash
systemctl is-active hysteria-stats-collector.timer
systemctl list-timers --all hysteria-stats-collector.timer
systemctl start hysteria-stats-collector.service
journalctl -u hysteria-stats-collector.service -n 20 --no-pager
```

Do not expose `127.0.0.1:9999` publicly.
