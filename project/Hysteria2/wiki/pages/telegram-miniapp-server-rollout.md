# Telegram Mini App Server Rollout

## Goal

Deploy the locally working Telegram Mini App to the main server without breaking existing VPN clients or overwriting active key databases on either server.

## Core Safety Decision

First production rollout must not replace the current Hysteria HTTP auth path.

Keep:

- `hysteria-server` unchanged.
- existing manager on `127.0.0.1:8081` unchanged.
- current `/etc/hysteria/users.json` unchanged.
- cascade `/etc/x-ui/x-ui.db` unchanged.

Deploy Mini App as a separate service on another localhost port, for example `127.0.0.1:8085`.

## Public Paths

Add nginx proxy routes:

- `/app/` -> Mini App frontend/backend on `127.0.0.1:8085`.
- `/sub/` -> subscription link endpoint on `127.0.0.1:8085`.

Do not change:

- `/44169d2dba4d0fd5/` -> current Flask manager.
- `/auth` used by Hysteria server internally.
- `hist.yupiterpro.ru:8443` Hysteria endpoint.

## Phase 0: Local Preflight

Run locally:

```bash
python3 -m unittest telegram_app.tests.test_all
PORT=8085 python3 telegram_app/backend/server.py
curl http://127.0.0.1:8085/api/user/me
```

Check:

- Mini App opens locally.
- `/api/user/me` responds.
- `/sub/<token>` returns Hysteria URI for active local test subscription.
- No code path writes to production `/etc/hysteria/users.json` or `/etc/x-ui/x-ui.db`.

## Phase 1: Read-Only Production Snapshot

Main server:

```bash
ssh -i ssh-keys/id_hysteria_rsa root@62.113.105.38
systemctl is-active hysteria-server hysteria-manager nginx
cp /etc/hysteria/users.json /root/users-json-before-miniapp-$(date +%Y%m%d-%H%M%S).json
```

Cascade server:

```bash
ssh -i ssh-keys/id_193_164_155_153 root@193.164.155.153
systemctl is-active wireproxy x-ui crowdsec
cp /etc/x-ui/x-ui.db /root/x-ui-db-before-miniapp-$(date +%Y%m%d-%H%M%S).db
```

Copy read-only snapshots to the main server Mini App import directory, never edit originals.

## Phase 2: Install Separate Mini App Service

On main server:

- Create `/opt/telegram-miniapp`.
- Copy `telegram_app/backend`, `telegram_app/frontend`, and `telegram_app/bot`.
- Create `/var/lib/telegram-miniapp`.
- Store Mini App SQLite DB at `/var/lib/telegram-miniapp/app.db`.
- Store secrets in `/etc/telegram-miniapp.env`.
- Run as separate systemd service, for example `telegram-miniapp.service`.

Environment:

```text
PORT=8085
PUBLIC_DOMAIN=hist.yupiterpro.ru
MINIAPP_DB_PATH=/var/lib/telegram-miniapp/app.db
TELEGRAM_BOT_TOKEN=[redacted]
WEBAPP_URL=https://hist.yupiterpro.ru/app/
```

Do not put secrets into git or wiki.

## Phase 3: nginx Proxy

Before changing nginx:

```bash
cp /etc/nginx/sites-available/hist.yupiterpro.ru /root/hist.yupiterpro.ru-before-miniapp-$(date +%Y%m%d-%H%M%S)
```

Add only these locations:

```nginx
location /app/ {
    proxy_pass http://127.0.0.1:8085/app/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

location /sub/ {
    proxy_pass http://127.0.0.1:8085/sub/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Then:

```bash
nginx -t
systemctl reload nginx
```

Reload nginx only after syntax passes.

## Phase 4: Production Smoke Checks

Check Mini App:

```bash
curl -Ik https://hist.yupiterpro.ru/app/
curl -s https://hist.yupiterpro.ru/api/user/me
```

If API is served only under `/app/`, use:

```bash
curl -s https://hist.yupiterpro.ru/app/api/user/me
```

Check existing surfaces:

```bash
curl -Ik https://hist.yupiterpro.ru/
curl -Ik https://hist.yupiterpro.ru/44169d2dba4d0fd5/
systemctl is-active hysteria-server hysteria-manager telegram-miniapp nginx
```

Run full Hysteria smoke with an existing valid user. Expected exit IP remains `193.164.155.153`.

## Phase 5: Telegram Configuration

In BotFather:

- Set Mini App URL to `https://hist.yupiterpro.ru/app/`.
- Keep bot token only in `/etc/telegram-miniapp.env`.

Bot checks:

- `/start` returns WebApp button.
- WebApp opens inside Telegram.
- Copy subscription link works.
- Claim link binds existing local imported account.

## Phase 6: Controlled Beta

Start with 1-2 test accounts:

- import current users into Mini App DB;
- generate subscription links;
- send links manually to testers;
- verify configs connect through `hist.yupiterpro.ru:8443`;
- verify existing clients who do not use the Mini App continue working.

## Deferred High-Risk Step

Do not switch Hysteria `auth.url` from current manager to Mini App backend in the first rollout.

Only consider this after:

- Mini App DB correctly mirrors all active Hysteria users;
- `/auth` compatibility is tested locally and on server localhost;
- rollback is documented;
- timestamped backups exist;
- full VPN smoke passes before and after.

## Rollback

Fast rollback should be:

```bash
systemctl stop telegram-miniapp
restore previous nginx config backup
nginx -t
systemctl reload nginx
```

No rollback should require touching:

- `hysteria-server`;
- `/etc/hysteria/users.json`;
- `/etc/x-ui/x-ui.db`.

