# Log

## 2026-08-21 - Traffic limits, DB backup, expiry reminders, trial grant (admin)

- **Traffic limits**: Added `traffic_limit_bytes` column to `subscriptions` (0 = unlimited). `/auth` now checks: if `limit > 0` and `used >= limit` → deny. Default = 0 (unlimited) for all new keys.
- **Admin set-limit API**: `POST /api/admin/client/set-limit` `{id, limit_gb}` — admin sets per-user traffic cap in GB. `limit_gb=null/0` removes limit.
- **Admin grant-trial API**: `POST /api/admin/client/grant-trial` `{telegram_user_id, hours}` — resets `trial_used=0`, extends existing subscription by N hours, or informs that user can activate trial from bot.
- **DB backup**: Created `backend/backup_db.py` — gzips `app.db` and sends to all Telegram admins. `systemd/backup-db.service` + `backup-db.timer` run daily at 03:00.
- **Expiry reminders**: Improved `expire_subscriptions.py::send_reminders()` — uses new `last_expiry_notified_at` column instead of `audit_log` scan for dedup. Added webapp link to messages. Logs count of sent reminders.
- New DB columns: `subscriptions.traffic_limit_bytes INTEGER DEFAULT 0`, `subscriptions.last_expiry_notified_at INTEGER`.

## 2026-08-21 - Latvia Hysteria direct inbound for Telegram direct keys

- Added a separate Latvia Hysteria direct inbound on cascade server `193.164.155.153`: `hysteria-direct.service` listens on UDP `:55445`, with local `hysteria-direct-auth.service` on `127.0.0.1:8091`.
- Hysteria binary was copied from the verified main server binary (`v2.9.2`); no existing x-ui, wireproxy, crowdsec, or production x-ui inbounds were changed.
- Created `/etc/hysteria-direct/config.yaml`, `/etc/hysteria-direct/users.json`, self-signed TLS files, `/opt/hysteria-direct/auth.py`, and `/opt/hysteria-direct/update_user.py`; `users.json` is kept `root:hysteria-direct 0640`.
- Latvia pre-change backup: `/root/miniapp-backups/latvia-hysteria-direct-before-20260821-124701`.
- Mini App backend now stores `vpn_accounts.direct_hysteria_config_uri`; `/sub/<token>` returns the new `Латвия Hysteria` profile alongside `Каскад Москва Латвия`, `Латвия TCP`, and `Латвия XHTTP` when present.
- Direct key creation now attaches Latvia Hysteria for promocode-issued Mini App keys; admin direct creation accepts `transport=hysteria`; Telegram bot trial/Stars creation stores the Latvia Hysteria URI when the helper succeeds.
- Cleanup/delete paths now remove managed Latvia Hysteria users in addition to main Hysteria and x-ui TCP/xHTTP clients.
- Main server backup before deploying code and DB migration: `/root/miniapp-backups/latvia-hysteria-direct-code-20260821-124834`.
- Updated `/etc/telegram-miniapp.env` with non-secret Latvia Hysteria settings: host `193.164.155.153`, port `55445`, SSH key `/root/.ssh/id_cascade`, users file `/etc/hysteria-direct/users.json`.
- Validation: local `python3 -m unittest telegram_app.tests.test_all` -> `26 tests OK`; production `py_compile` OK; `telegram-miniapp`, `telegram-bot`, `hysteria-server`, and `nginx` active; `/app/` returned HTTP `200`.
- End-to-end smoke from main server through temporary Latvia Hysteria user returned external IP `193.164.155.153`; temporary smoke users were deleted and Latvia `users.json` had `smoke_left=False`.

## [2026-08-16] audit | Full server check from local machine

- Main server: all services active (hysteria-server, hysteria-manager, telegram-miniapp, telegram-bot, nginx, stats-collector timer, cleanup timer).
- `hysteria-cascade-client` inactive — cascade works via outbound in server config.
- Mini App deployed at `https://hist.yupiterpro.ru/app/` (95KB, production build).
- Bot running (polling mode, pid 505123, since Aug 12).
- DB: 15 tables, 60 vpn_accounts, 55 active subs (~25.5 days left), 3 telegram_users, 0 account_links, 11377 traffic_snapshots.
- Plans: 1 мес 300₽, 3 мес 800₽, 1 год 2500₽.
- Payment: manual enabled (card 4937...7804), Stars заявка (не автоинвойс).
- Cascade server: x-ui active, xray :18443 + :443, wireproxy :40000, crowdsec active.
- Disk: main 47% (4.1G/8.7G), cascade 43% (16G/38G).

## [2026-08-12] deploy | Separate Mini App x-ui TCP and xHTTP Inbounds

- User confirmed: one subscription link must show three VPN endpoints in the client: `Каскад Москва Латвия`, `Латвия TCP`, `Латвия XHTTP`.
- Created separate x-ui inbound for Mini App TCP direct keys via local x-ui API:
  - id `8`
  - remark `MiniApp Direct`
  - port `55443`
  - protocol `vless`
  - clients `0`
- Created separate x-ui inbound for Mini App xHTTP direct keys via local x-ui API:
  - id `9`
  - remark `MiniApp xHTTP`
  - port `55444`
  - protocol `vless`
  - clients `0`
- Existing production inbounds were not modified:
  - id `1`, port `443`, remark `Fine`, clients `27`
  - id `7`, port `55332`, remark `xHTTP`, clients `7`
- Backups before x-ui changes:
  - `/root/miniapp-backups/x-ui-db-before-miniapp-inbound-20260812-103252.db`
  - `/root/miniapp-backups/x-ui-db-before-miniapp-xhttp-inbound-20260812-103501.db`
- Mini App `/sub/<token>` generation updated to return multiple newline-separated URI entries:
  - Hysteria cascade labelled `Каскад Москва Латвия`
  - VLESS TCP labelled `Латвия TCP`
  - VLESS xHTTP labelled `Латвия XHTTP`
- Mini App DB migrated with `direct_tcp_config_uri` and `direct_xhttp_config_uri`.
- Mini App env updated with non-secret x-ui API values and managed inbound ids:
  - `XUI_API_BASE_URL=https://127.0.0.1:21292/pshavlakurl`
  - `XUI_PUBLIC_HOST=193.164.155.153`
  - `XUI_MANAGED_TCP_INBOUND_ID=8`
  - `XUI_MANAGED_XHTTP_INBOUND_ID=9`
- x-ui credentials were not added to `/etc/telegram-miniapp.env` in this step; actual client creation from Mini App requires adding `XUI_USERNAME` and `XUI_PASSWORD` safely.
- Verification:
  - local tests: `17 tests OK`
  - `telegram-miniapp=active`
  - `hysteria-server=active`
  - `x-ui=active`
  - `/app/` -> HTTP 200
  - x-ui ports active: `443`, `55332`, `55443`, `55444`, `18443`, `21292`, `21293`

## [2026-08-12] plan+local | Safe x-ui Direct Key Creation Prep

- Разобрана безопасная схема создания x-ui direct ключей для Mini App.
- Решение: не добавлять новых клиентов в существующие production inbounds `443`/`55332` по умолчанию; использовать отдельный managed inbound для новых Mini App direct ключей.
- Добавлен локальный backend-модуль `telegram_app/backend/xui_api.py` для работы через x-ui API: login, get inbound, add client, сбор VLESS/Reality URI.
- Добавлен защищенный admin endpoint `/api/admin/xui/create-direct`; без env `XUI_API_BASE_URL`, `XUI_USERNAME`, `XUI_PASSWORD`, `XUI_MANAGED_INBOUND_ID` он возвращает ошибку конфигурации и не меняет VPN state.
- В Mini App admin client detail добавлен блок `Direct x-ui` и кнопка `Создать direct x-ui`.
- Production x-ui write operations не выполнялись; `/etc/x-ui/x-ui.db` и inbounds не изменялись.
- Локальная проверка: `PYTHONPYCACHEPREFIX=/tmp/hysteria-miniapp-pycache python3 -m unittest telegram_app.tests.test_all` -> 17 tests OK.
- UI detector: `impeccable detect` по `telegram_app/frontend/index.html` -> fallback parser, findings `[]`.

## [2026-08-12] deploy | Mini App Routing Modes

- Реализована страница `Тип роутинга` в Mini App в общем стиле, с более читаемыми и яркими надписями.
- Убрана пользовательская кнопка/страница `Прокси для Telegram`.
- Режимы сведены к двум вариантам: `Каскад` и `Прямой VPN`.
- Добавлено хранение выбора роутинга в Mini App DB: `vpn_accounts.routing_mode`.
- Добавлены поля для прямого профиля: `direct_config_uri`, `direct_config_updated_at`, `direct_config_note`.
- Добавлен защищенный Telegram Mini App API: `GET/POST /api/user/routing`.
- `/sub/<token>` теперь учитывает routing mode: по умолчанию отдаёт старый Hysteria cascade URI; при `direct` отдаёт VLESS/Reality URI, если он привязан; если direct-профиля нет, старый каскадный URI не ломается.
- Импорт x-ui расширен read-only сбором VLESS/Reality URI из `inbounds` и привязкой direct URI к Hysteria-аккаунтам с совпадающим именем.
- Оригинальная `/etc/x-ui/x-ui.db` не изменялась: импорт выполнялся с временного snapshot, временные файлы удалены.
- Локальная проверка: `PYTHONPYCACHEPREFIX=/tmp/hysteria-miniapp-pycache python3 -m unittest telegram_app.tests.test_all` -> 16 tests OK.
- UI detector: `impeccable detect` по `telegram_app/frontend/index.html` -> fallback parser, findings `[]`.
- Перед деплоем на основном сервере сделаны бэкапы `/opt/telegram-miniapp/backend/server.py`, `db.py`, `importers.py`, `/opt/telegram-miniapp/frontend/index.html`, `/var/lib/telegram-miniapp/app.db` в `/root/miniapp-backups/` с timestamp `20260812-101832`.
- Production import result: direct URI есть у 34 x-ui записей и у 5 Hysteria-аккаунтов по совпадению имени.
- Перезапущен только `telegram-miniapp`; `hysteria-server` не перезапускался.
- Production smoke после деплоя: `telegram-miniapp=active`, `hysteria-server=active`, `/app/` -> HTTP 200, unsigned `/api/user/routing` -> HTTP 403.

## [2026-08-12] deploy | Mini App Admin Payments and Promocodes

- Локально реализованы отдельные страницы админки Mini App: `Клиенты и ключи`, `Оплаты`, `Промокоды`.
- Список клиентов/ключей свернут с главной админки и вынесен в отдельную страницу.
- Добавлены admin API: `/api/admin/payments`, `/api/admin/payments/action`, `/api/admin/promocodes`, `/api/admin/promocodes/save`, `/api/admin/promocodes/delete`.
- Промокоды теперь управляются из админки с полями: код, бонусные дни, процент скидки, лимит активаций, срок действия.
- Активация промокода теперь проверяет `expires_at` и отклоняет истекшие промокоды.
- Локальная проверка: `PYTHONPYCACHEPREFIX=/tmp/hysteria-miniapp-pycache python3 -m unittest telegram_app.tests.test_all` -> 16 tests OK.
- UI detector: `impeccable detect` по `telegram_app/frontend/index.html` -> fallback parser, findings `[]`.
- Перед деплоем на основном сервере сделаны бэкапы `/opt/telegram-miniapp/backend/server.py`, `/opt/telegram-miniapp/frontend/index.html`, `/var/lib/telegram-miniapp/app.db` в `/root/miniapp-backups/` с timestamp `20260812-091418`.
- Развернуты только `/opt/telegram-miniapp/backend/server.py` и `/opt/telegram-miniapp/frontend/index.html`.
- Перезапущен только `telegram-miniapp`; `hysteria-server` не перезапускался.
- Production smoke после деплоя: `telegram-miniapp=active`, `hysteria-server=active`, `/app/` -> HTTP 200, unsigned `/api/admin/payments` -> HTTP 403, unsigned `/api/admin/promocodes` -> HTTP 403.

## [2026-08-12] deploy | Hide Device IPs from User Cabinet

- Removed IP address display from the user-facing Mini App Devices page for privacy posture.
- The user-facing page now shows device name and last subscription refresh time only.
- Admin diagnostic views were not changed.
- Changed only `telegram_app/frontend/index.html`; no backend, VPN config, key database, or device registry logic was changed.
- Backed up production frontend before deploy: `/root/miniapp-backups/index-before-hide-user-device-ip-20260812-085247.html`.
- Restarted only `telegram-miniapp`; `hysteria-server` remained active.
- Verification: local HTML parse passed; Impeccable detector returned no findings in regex fallback mode; production `/app/` contains the new privacy text and no old "Активные подключения и последние IP" subtitle.

## [2026-08-12] deploy | Inline Mini App Setup Instructions

- Implemented detailed in-app setup instructions inside the Mini App, based on the referenced Voron/Happ-style flow: install app, copy subscription link, import from clipboard/URL, choose location, connect and verify access.
- Added internal `instruction-detail-view` for iOS/iPad, Android, Windows, and macOS; platform cards now open instructions instead of only copying the subscription link.
- iOS instruction uses App Store link for `Happ - Proxy Utility`; other platforms point to the official Happ download page until platform-specific local download links are added.
- Added action buttons inside each instruction: install app, copy subscription link, and show QR.
- Changed only `telegram_app/frontend/index.html`; no backend, VPN config, key database, or subscription logic was changed.
- Backed up production frontend before deploy: `/root/miniapp-backups/index-before-inline-instructions-20260812-084643.html`.
- Restarted only `telegram-miniapp`; `hysteria-server` remained active.
- Verification: local HTML parse passed; backend tests passed `15/15`; Impeccable detector returned no findings in regex fallback mode; Playwright mobile smoke opened the iOS instruction with 5 steps and visible install/copy actions; production `/app/` contains `instruction-detail-view` and `Инструкция для iPhone/iPad`.

## [2026-08-12] deploy | Removed Duplicate Connect VPN Button

- Removed the green "Подключить VPN" button from the Mini App subscription card because it duplicated the "Скопировать ссылку" action.
- Changed only `telegram_app/frontend/index.html`; no backend, VPN config, key database, or subscription logic was changed.
- Backed up production frontend before deploy: `/root/miniapp-backups/index-before-remove-connect-vpn-button-20260812-083712.html`.
- Restarted only `telegram-miniapp`; `hysteria-server` remained active.
- Verification: local HTML parse passed; Impeccable detector returned no findings in regex fallback mode; production `/app/` contains "Скопировать ссылку" and no "Подключить VPN".

## [2026-08-12] deploy | Subscription Device Registry

- Implemented first-stage device tracking for one subscription link used across multiple VPN clients.
- Added Mini App DB table `subscription_devices` for per-account device registry keyed by HWID-like headers when available, with fallback fingerprinting from subscription request metadata.
- Extended `/sub/<token>` to record subscription fetch headers such as `X-Hwid`, `X-Device-Id`, `X-Device-Model`, `X-Platform`, `X-Client-Version`, and `User-Agent`; subscription tokens and VPN auth secrets remain redacted from logs.
- Added protected Mini App endpoints `GET /api/user/devices` and `POST /api/user/devices/reset`; both require signed Telegram Mini App auth and return `403` without it.
- Updated the Mini App Devices page to load the device registry and reset registered devices from inside Telegram.
- No device limit enforcement was enabled yet; this deploy only observes and registers devices so existing clients are not blocked.
- Backed up production Mini App DB and app files before deploy under `/root/miniapp-backups/`, timestamp `20260812-083348`.
- Restarted only `telegram-miniapp`; `hysteria-server` remained active and was not restarted.
- Verification: local tests passed `15/15`; production migration created `subscription_devices`; smoke subscription request with Happ-style headers registered `iPhone 11 Pro / iOS / Happ`; cleanup restored Mini App account count to `55`; unsigned devices API and reset returned HTTP `403`; `/app/` returned HTTP `200`.

## [2026-08-12] deploy | Mini App User Cabinet UX Refresh

- Updated Mini App frontend `telegram_app/frontend/index.html` and deployed it to `/opt/telegram-miniapp/frontend/index.html` on the main server.
- Reworked the user cabinet in the existing Cascade VPN dark glass/neon style without copying external branding.
- Added larger primary actions: copy subscription link, QR code, connect VPN, instructions, devices, routing type, Telegram proxy, renew subscription, and help.
- Added internal Mini App views for devices, instructions, QR code, routing, Telegram proxy, renew, help, settings, and profile.
- Added bottom navigation for cabinet, tariffs, devices, settings, and profile; admin navigation remains hidden for non-admin users.
- QR code is generated client-side from the current subscription link; the feature does not write to VPN configs or key databases.
- Server backup before replacement: `/root/miniapp-backups/index-before-user-cabinet-refresh-20260812-075900.html`.
- Restarted only `telegram-miniapp`; `hysteria-server` remained active and was not restarted.
- Verification: backend unit tests passed `13/13`; local Mini App `/app/` returned HTTP `200`; `/api/user/me` returned demo data; Playwright mobile smoke verified visible dashboard actions, QR generation, and devices view; Impeccable detector returned no findings in regex fallback mode.
- Production checks after deploy: `telegram-miniapp=active`, `hysteria-server=active`, `/app/` returned HTTP `200`, unsigned admin API returned HTTP `403`, `/etc/hysteria/users.json` remained valid JSON, and the deployed HTML contains the new user cabinet views.

## [2026-08-11] deploy | Mini App Safe Hysteria Key Creation

- Implemented protected admin endpoint `POST /api/admin/hysteria/create` for creating new Hysteria users from the Telegram Mini App.
- Added `/opt/telegram-miniapp/backend/hysteria_users.py` logic locally and deployed it to the main server: username validation, timestamped backup of `/etc/hysteria/users.json`, atomic temp-file write, JSON validation, and manager `/auth` verification.
- Updated Mini App admin UI with a "New Hysteria key" form supporting 5, 15, 30, and infinite-day subscriptions.
- The feature writes only `/etc/hysteria/users.json` and `/var/lib/telegram-miniapp/app.db`; x-ui remains read-only and no cascade database writes were made.
- Before deploy, backed up Mini App production DB and current app files under `/root/miniapp-backups/`.
- Restarted only `telegram-miniapp`; `hysteria-server` was not restarted.
- Verification: local unit tests passed `13/13`; `telegram-miniapp`, `hysteria-server`, `hysteria-manager`, and `nginx` were active; `/app/` returned HTTP `200`; unsigned create request returned HTTP `403`.
- Smoke test created temporary user `codex-smoke-184355`, verified manager auth, connected through Hysteria, and returned exit IP `193.164.155.153`; the temporary key and Mini App DB row were removed afterward.
- Added rollback handling: if Mini App DB write fails after `users.json` write, the newly created Hysteria user is removed automatically.
- Re-ran create/delete smoke after final rollback patch: create `ok=true`, auth verified, temporary user appeared in `users.json`, cleanup restored Mini App account count to `55`, and no smoke user remained.
- Post-check counts: Hysteria users `21`, Mini App accounts `55`, smoke leftovers `0`.

## [2026-08-11] maintenance | Restarted Hysteria and Rebooted Cascade Server

- User requested restart of Hysteria and the second server.
- Pre-check main server: `hysteria-server`, `hysteria-manager`, `telegram-miniapp`, `telegram-bot`, and `nginx` were active; UDP `:8443` and local stats `127.0.0.1:9999` were listening.
- Pre-check cascade server `193.164.155.153`: `wireproxy`, `x-ui`, and `crowdsec` were active; ports `443`, `18443`, `40000`, `21292`, and `21293` were listening.
- Restarted `hysteria-server` on main server; after restart it returned active with UDP `:8443` and `127.0.0.1:9999` listening.
- Rebooted cascade server `193.164.155.153`; after reboot host `server-pflm6j` returned with uptime around 3 minutes.
- Post-reboot cascade services: `wireproxy=active`, `x-ui=active`, `crowdsec=active`; ports `443`, `18443`, `40000`, `21292`, and `21293` listening.
- Full local Hysteria client smoke after both restarts returned external IP `193.164.155.153`.
- Main services after checks: `hysteria-server=active`, `hysteria-manager=active`, `telegram-miniapp=active`, `telegram-bot=active`, `hysteria-stats-collector.timer=active`, `nginx=active`.

## [2026-08-11] deploy | Hysteria Traffic and Device Stats

- Implemented Hysteria stats collection for Mini App using Hysteria Traffic Stats API `/traffic` and `/online`.
- Added Mini App DB field `online_devices` and collector script `/opt/telegram-miniapp/backend/collect_hysteria_stats.py`.
- Added systemd units `hysteria-stats-collector.service` and `hysteria-stats-collector.timer`; timer runs every 5 minutes.
- Backed up Mini App DB before migration: `/var/lib/telegram-miniapp/app-before-hysteria-stats-*.db`.
- Enabled Hysteria `trafficStats` on `127.0.0.1:9999` only, with secret stored in `/etc/telegram-miniapp.env`.
- Backed up Hysteria config before change: `/root/miniapp-backups/hysteria-config-before-stats-20260811-181009.yaml`.
- Restarted `hysteria-server` once to enable local Traffic Stats API; service returned `active`, rollback was not needed.
- Fixed manager `/auth` response to return `id=username`, allowing Hysteria to attribute traffic and online device counts to real users.
- Backed up manager file before replacement as `/opt/hysteria-manager/app.py.bak-auth-id-*`; restarted only `hysteria-manager` for that change.
- Verification: `/auth` returned `ok=true` and matching `id`; Hysteria stats API listened on `127.0.0.1:9999`; collector saw online Hysteria user `myphone`; Mini App DB row for `myphone` recorded `online_devices=1` and `traffic_source=hysteria/trafficStats`.
- Full local Hysteria client smoke still returned external IP `193.164.155.153`.

## [2026-08-11] deploy | Mini App Client Detail Separate View

- Changed Mini App admin client detail from an inline card below the client list to a separate internal view `client-detail-view`.
- Clicking a client now hides the admin list and opens the client detail page with a `Назад` button.
- The bottom navigation keeps Admin highlighted while viewing client detail.
- Deployed frontend-only update to `/opt/telegram-miniapp/frontend/index.html` and restarted only `telegram-miniapp`.
- Verification: public `/app/` contains `client-detail-view`; unsigned `/api/admin/client?id=1` still returns `403`; services remain active.
- Full local Hysteria client smoke still returned external IP `193.164.155.153`.

## [2026-08-11] deploy | Mini App Client Detail Cabinet

- Added clickable client rows in Mini App admin list.
- Added admin client detail endpoint `/api/admin/client?id=...&from=YYYY-MM-DD&to=YYYY-MM-DD`, protected by signed Telegram Mini App admin auth.
- Added client detail UI with date range controls, traffic summary, IP events, subscription expiry, and quick extension buttons `+5`, `+15`, `+30`, and infinite.
- Updated `/api/admin/extend` to accept only `5`, `15`, `30`, or `infinite`; changes affect only Mini App subscription DB.
- Added `traffic_snapshots` table; x-ui imports now store snapshots for future date-range deltas. Existing historical x-ui daily data is not available before snapshots start.
- Backed up Mini App DB before migration: `/var/lib/telegram-miniapp/app-before-client-detail-*.db`.
- Verification: local tests `11/11` passed; public unsigned `/api/admin/client?id=1` returned `403`; signed admin detail request returned `200`; snapshots count `34`; Mini App `/app/` returned `200`.
- Services after deploy: `hysteria-server=active`, `hysteria-manager=active`, `telegram-miniapp=active`, `telegram-bot=active`, `nginx=active`.
- Full local Hysteria client smoke still returned external IP `193.164.155.153`.

## [2026-08-11] security | Locked Mini App Admin Access

- User added `TELEGRAM_ADMIN_IDS` to `/etc/telegram-miniapp.env`; value was not printed.
- Added Telegram Mini App `initData` signature verification for admin access.
- Protected `/api/admin/clients`, `/api/admin/receipts`, `/api/admin/receipts/action`, and `/api/admin/extend` behind signed Telegram admin checks.
- Frontend now sends `X-Telegram-Init-Data` for API calls and hides the Admin tab unless `/api/user/me` returns `is_admin=true`.
- Verification: unauthenticated public `/api/admin/clients` returned `403`; signed admin request returned `200` with `55` clients.
- Services after deploy: `hysteria-server=active`, `hysteria-manager=active`, `telegram-miniapp=active`, `telegram-bot=active`, `nginx=active`.
- Full local Hysteria client smoke still returned external IP `193.164.155.153`.

## [2026-08-11] deploy | Mini App Real Traffic Metrics

- Replaced demo traffic/device values in Mini App API and UI.
- x-ui clients now use real aggregate traffic from copied `client_traffics.up`, `client_traffics.down`, and `client_traffics.total` fields.
- Hysteria clients no longer show fake traffic; API reports that Hysteria traffic accounting is not connected yet.
- Added Mini App DB columns for traffic counters and source metadata; added `connection_events` table for subscription fetch/auth event IP records.
- Added subscription-link event recording for active subscription fetches without printing subscription tokens.
- Refreshed x-ui data through a read-only copy of cascade `/etc/x-ui/x-ui.db`; production x-ui DB was not overwritten.
- Backed up Mini App DB before migration: `/var/lib/telegram-miniapp/app-before-traffic-*.db`.
- Verification: admin API reported `xui_count=34`, `hysteria_count=21`, Hysteria fake traffic removed, Mini App page returned `200`, all services active.
- Full local Hysteria client smoke still returned external IP `193.164.155.153`.

## [2026-08-11] deploy | Telegram Bot Polling Service

- Added Telegram polling runner to `telegram_app/bot/bot.py` for `/start` and `/start claim_<token>` handling.
- Added `telegram_app/systemd/telegram-bot.service` and deployed it to main server.
- Enabled and started `telegram-bot.service`; service returned `active`.
- Verified Telegram webhook is not set, so polling mode can receive updates.
- Verified services after bot deployment: `hysteria-server=active`, `hysteria-manager=active`, `telegram-miniapp=active`, `telegram-bot=active`, `nginx=active`.
- Local tests after bot runner changes: `9/9` passed.

## [2026-08-11] check | Telegram Bot Token Configured

- User entered Telegram bot token into `/etc/telegram-miniapp.env`; token value was not printed.
- Verified env file permissions: `600 root:root`.
- Restarted only `telegram-miniapp`; service returned `active`.
- Telegram API `getMe` returned ok for bot username `kaskad_yupiter_bot`, bot id `8810775803`.
- Mini App API after restart returned active user data with subscription link present.

## [2026-08-11] deploy | Telegram Mini App Safe Production Rollout

- Deployed local `telegram_app/` to main server as separate service `/opt/telegram-miniapp`, listening on `127.0.0.1:8085`.
- Created production Mini App database at `/var/lib/telegram-miniapp/app.db`; did not copy local demo `app.db`.
- Created separate env file `/etc/telegram-miniapp.env`; Telegram bot token remains placeholder until configured.
- Imported existing clients into Mini App DB read-only: `hysteria=21`, `xui=34`.
- Backups created before rollout: main server `/root/miniapp-backups/users-json-before-miniapp-*.json` and `/root/miniapp-backups/nginx-hist-before-miniapp-*.conf`; cascade `/root/miniapp-backups/x-ui-db-before-miniapp-*.db`.
- Added nginx routes `/app/`, `/api/`, and `/sub/` to proxy to `127.0.0.1:8085`; hidden manager route `/44169d2dba4d0fd5/` remains proxied to `127.0.0.1:8081`.
- Did not change Hysteria server config, Hysteria `/auth`, `/etc/hysteria/users.json`, or `/etc/x-ui/x-ui.db`.
- Verification: `https://hist.yupiterpro.ru/app/` returned `200`; `https://hist.yupiterpro.ru/api/user/me` returned active Mini App user data; hidden manager returned `200`; root decoy returned `200`.
- Service check after deployment: `hysteria-server=active`, `hysteria-manager=active`, `telegram-miniapp=active`, `nginx=active`.
- Subscription endpoint check returned HTTP `200` and a Hysteria2 URI without printing the URI body.
- Full local Hysteria client smoke through `hist.yupiterpro.ru:8443` still returned external IP `193.164.155.153`.

## [2026-08-11] planning | Telegram Mini App Server Rollout Plan

- User confirmed local Mini App works and asked for a server transfer/implementation plan.
- Created `wiki/pages/telegram-miniapp-server-rollout.md`.
- Rollout plan keeps the current Hysteria `/auth`, `/etc/hysteria/users.json`, and cascade `/etc/x-ui/x-ui.db` untouched during first production deployment.
- Plan deploys Mini App as a separate localhost service behind nginx `/app/` and `/sub/`, with rollback that does not touch VPN services or active key databases.

## [2026-08-11] dev | Telegram Bot & WebApp Deep Linking Integration

- Implemented Telegram Bot handler (`bot.py`) with `/start` command and WebApp Inline button (`InlineKeyboardButton`).
- Implemented 1-click Deep Linking (`/start claim_<token>`) for instant account linking.
- Integrated admin notification trigger for new payment receipt moderation.
- Added unit tests in `test_all.py` (6/6 tests passed). Local server running on `http://127.0.0.1:8085`.

- Created `wiki/pages/telegram-miniapp-plan.md`.
- Plan prioritizes a non-breaking Telegram Mini App rollout: read-only imports first, subscription links independent of VPN passwords, manual subscription control before payments, and no production writes before backups and validation.
- Current clients on main Hysteria `/etc/hysteria/users.json` and cascade x-ui `/etc/x-ui/x-ui.db` are explicitly preserved as production sources during MVP.

## [2026-08-11] planning | Telegram Bot Plan Requested

- User asked for a plan to build a Telegram bot using the existing client bases on both servers.
- Reviewed local wiki and project files only; no server changes were made.
- Relevant current sources: main Hysteria users in `/etc/hysteria/users.json`; cascade x-ui data in `/etc/x-ui/x-ui.db`; manager on `127.0.0.1:8081`.

## [2026-08-11] maintenance | Updated Cascade x-ui Panel

- User asked to check/update 3x-ui on cascade server `193.164.155.153` without breaking the active VPN and without losing user key database.
- Verified installed panel is `alireza0/x-ui`, previously reporting `x-ui 1.11.1`, not the `MHSanaei/3x-ui` v3.x line.
- Created full backup before update: `/root/backup-3xui-20260811-125329.tar.gz`.
- Backup includes `/etc/x-ui`, `/usr/local/x-ui`, `/etc/systemd/system/x-ui.service`, `/etc/xray-cascade`, and `/etc/wireguard/proxy.conf`.
- An attempted `MHSanaei/3x-ui v3.6.0` installer run was interrupted after removing `/usr/local/x-ui`; `x-ui.service` became inactive, while cascade SOCKS on `18443` remained alive.
- Restored `/usr/local/x-ui` and service unit from backup without overwriting `/etc/x-ui/x-ui.db`; `x-ui.service` returned active.
- Safely updated within the same fork to `alireza0/x-ui v1.11.4` using manual release tarball replacement and `/usr/local/x-ui/x-ui migrate`.
- Extra backups made during successful update: `/root/x-ui-pre-v1.11.4-20260811-125852` and `/root/x-ui-db-pre-v1.11.4-20260811-125852.db`.
- Post-update database check: `/etc/x-ui/x-ui.db` exists, size `73728`, tables include `inbounds`, `client_traffics`, `settings`, `users`; counts: `inbounds=2`, `client_traffics=34`, `settings=38`, `users=1`.
- Post-update services: `x-ui=active`, `wireproxy=active`, `crowdsec=active`.
- Post-update ports: `21292`, `21293`, `443`, `18443`, `40000` listening.
- Main server to cascade SOCKS check returned external IP `193.164.155.153`.
- Full local Hysteria client smoke through `hist.yupiterpro.ru:8443` returned external IP `193.164.155.153`.

## [2026-08-11] maintenance | Collected SSH Keys

- Created `ssh-keys/`.
- Moved cascade key from project root to `ssh-keys/id_193_164_155_153`.
- Moved cascade public key to `ssh-keys/id_193_164_155_153.pub`.
- Copied main server key from `~/.ssh/id_hysteria_rsa` to `ssh-keys/id_hysteria_rsa`.
- Updated README and wiki references to the new key paths.

## [2026-08-11] docs | Added Admin Panel and Decoy URL

- Added hidden admin panel URL: `https://hist.yupiterpro.ru/44169d2dba4d0fd5/`.
- Documented that `https://hist.yupiterpro.ru` is a placeholder/decoy page for hiding the VPN.

## [2026-08-11] setup | Created Local Wiki

- Локальной wiki до этого не было: найдены только `README.md`, `config/`, `manager/`, `nginx/`, `systemd/`.
- Создана wiki по паттерну LLM-maintained markdown knowledge base: `index.md`, `log.md`, `schema.md`, `pages/`, `raw/`.
- Добавлен корневой `AGENTS.md` с правилами безопасной работы по этому проекту.

## [2026-08-11] check | Production Cascade VPN Verification

- Основной сервер `62.113.105.38`, host `hlamnndyjf`, uptime около 10 недель.
- Сервисы на основном сервере: `hysteria-server=active`, `hysteria-manager=active`, `nginx=active`.
- Порты на основном сервере: nginx TCP `:443`, manager TCP `127.0.0.1:8081`, Hysteria UDP `:8443`.
- `/etc/hysteria/config.yaml` содержит `listen: :8443` и auth URL `http://127.0.0.1:8081/auth`.
- Локальный auth check на основном сервере вернул `200 {"ok":true}`.
- Hysteria client через `hist.yupiterpro.ru:8443` успешно подключился и вышел наружу с IP `193.164.155.153`.
- Hysteria client через `hist.yupiterpro.ru:443` не подключился: timeout.
- Каскадный сервер `193.164.155.153`, host `server-pflm6j`, uptime около 4 недель.
- На каскаде активны `wireproxy`, `x-ui`, `crowdsec`; `xray` unit inactive, но процессы `xray-linux-amd6` слушают TCP `:443` и `:18443`.
- `wireproxy` слушает `127.0.0.1:40000`.

## [2026-08-11] deploy | Manager Security Fixes

- На основной сервер развернуты обновленные `/opt/hysteria-manager/app.py` и `/opt/hysteria-manager/hysteria-users.sh`.
- Перед заменой сделаны бэкапы: `app.py.bak-20260811-123652`, `hysteria-users.sh.bak-20260811-123652`.
- Перезапущен только `hysteria-manager`; `hysteria-server` не перезапускался.
- Исправлено: manager больше не логирует auth password.
- Исправлено: доступ к add/delete больше не доверяет произвольной cookie `admin_session=valid`, используется подписанная Flask session.
- Исправлено: генератор клиентских URI выдаёт фактический порт `8443`.

## [2026-08-12] deploy | Telegram Mini App Admin Client Split

- В Mini App админке разделены списки клиентов: `Новые ключи` и `Старые ключи`.
- Добавлен поиск по имени, типу, ID, статусу и сроку на страницах новых/старых ключей.
- В SQLite добавлено поле `vpn_accounts.account_origin`; существующие записи мигрированы в `legacy`, созданные через Mini App/audit `hysteria_create` - в `miniapp`.
- Проверено на prod DB: `legacy=55`, `miniapp=1`; ключ `Test_app` найден как `miniapp`.
- Перед деплоем сделаны backup файлы и DB с timestamp `20260812-110442` в `/root/miniapp-backups/`.
- Перезапущен только `telegram-miniapp`; `hysteria-server` не перезапускался.
- Проверки после деплоя: main `hysteria-server=active`, UDP `:8443` слушает, `http://127.0.0.1:8085/app/` вернул `200`; Latvia `x-ui=active`, порты `443`, `55443`, `55444`, `21292` слушают.
- Исправление фильтра: `Новые ключи` теперь показывают только `account_origin=miniapp`; старые ключи с direct TCP/xHTTP остаются в разделе `Старые ключи`. Backup перед исправлением: `20260812-110937`; после рестарта `telegram-miniapp=active`, `/app/` вернул `200`.
- Исправлено создание второго x-ui endpoint для одного Mini App ключа: x-ui требует глобально уникальный `email`, поэтому xHTTP теперь создаётся с техническим suffix `__xhttp`, а отображаемое имя в подписке остаётся `Латвия XHTTP`. Backup перед исправлением: `20260812-111518`.
- Проверено на `Test_app`: inbound `8 MiniApp Direct` содержит TCP-клиента, inbound `9 MiniApp xHTTP` содержит xHTTP-клиента; `/sub/<token>` отдаёт 3 строки с именами `Каскад Москва Латвия`, `Латвия TCP`, `Латвия XHTTP`.
- Для новых Mini App Hysteria ключей добавлен pending-режим Hysteria trafficStats: при создании ключ получает `traffic_source=hysteria/trafficStats/pending` и нулевой snapshot; после первого реального Hysteria-трафика collector переключает запись на `hysteria/trafficStats`.
- Backup перед изменением pending stats: `20260812-112234`; перезапущен только `telegram-miniapp`, `hysteria-server` не перезапускался. Проверка: `telegram-miniapp=active`, `hysteria-server=active`, `hysteria-stats-collector.timer=active`, `/app/` вернул `200`, ручной запуск collector: `pending_users=1`.
- Проверено для `Test_app`: `traffic_source=hysteria/trafficStats/pending`, counters `0/0`, Hysteria `/traffic` пока не содержит `Test_app` до первого реального подключения по Hysteria endpoint.
- В админской карточке клиента добавлены видимые `Ссылка подписки`, кнопка копирования и QR-код на эту же ссылку. Backup frontend перед деплоем: `20260812-115540`; после рестарта `telegram-miniapp=active`, `/app/` вернул `200`.
- Исправлен Telegram bot polling для `/start`: добавлен timeout Telegram API-запросов и логи обработки updates. Backup `bot.py`: `20260812-120216`; перезапущен только `telegram-bot`.
- Проверка после рестарта: бот обработал pending updates `984152536` и `984152537`, `pending_update_count=0`, webhook не установлен, `telegram-bot=active`, `telegram-miniapp=active`, `hysteria-server=active`, `/app/` вернул `200`.
- Security fix: удалён fallback `LIMIT 1` в `get_user_account`, из-за которого непривязанный Telegram пользователь мог видеть первый VPN-аккаунт. Теперь без `account_links` API отдаёт пустой кабинет `has_subscription=false`, `sub_link=null`.
- Frontend Mini App показывает непривязанному пользователю пустой кабинет с запросом на покупку/бонус-код; копирование ссылки и QR заблокированы до появления подписки.
- Исправлены демо-заглушки промокодов/ручных платежей: промокод больше не продлевает `vpn_account_id=1`, ручная заявка пишется на реальный Telegram ID, одобрение без привязанного VPN аккаунта возвращает ошибку.
- Backup перед security fix: `20260812-121346`; после деплоя `telegram-miniapp=active`, `hysteria-server=active`, `/app/` вернул `200`. Проверка signed API для нового Telegram ID: `has_subscription=false`, `sub_link=null`; `/api/promocode/apply` вернул `409` без изменения чужой подписки.
- Реализованы промокоды, которые при активации выдают новый VPN-ключ: Hysteria cascade + x-ui TCP + x-ui XHTTP. В админке промокодов добавлен флажок `Выдать новый VPN ключ при активации`; срок ключа берется из поля `+ дней`.
- Для таких ключей добавлены SQLite поля `vpn_accounts.created_by_promocode`, `auto_delete_at`, `deleted_at`; cleanup выбирает только `account_origin=miniapp` и `created_by_promocode IS NOT NULL`, чтобы не затрагивать legacy/manual ключи.
- Добавлен `/opt/telegram-miniapp/backend/cleanup_expired_promocode_keys.py` и systemd timer `expired-promocode-key-cleanup.timer` каждые 5 минут. Удаление идет по управляемым x-ui inbounds, затем из `/etc/hysteria/users.json`; после успешного удаления локальная подписка истекает, token revoke, account_link удаляется.
- Backup перед деплоем: `/root/miniapp-backups/20260812-122941/`. Перезапущен только `telegram-miniapp`; `hysteria-server` и `x-ui` не перезапускались.
- Проверки после деплоя: локальные тесты `19 OK`; server py_compile OK; DB columns true; `telegram-miniapp=active`; `expired-promocode-key-cleanup.timer=active`; ручной cleanup вернул `{"ok": true, "deleted": 0}`; `/app/` вернул `200`; `hysteria-server=active`, UDP `:8443` слушает; Latvia `x-ui=active`, порты `443`, `55443`, `55444`, `21292` слушают.
- Исправлена логика активации промокода: если у Telegram пользователя уже есть привязанный ключ, промокод добавляет дни к текущей подписке; если ключа нет, промокод создаёт новый Mini App ключ на 3 endpoint. Backup `server.py`: `20260812-131022`. Локально `20 OK`; после деплоя `telegram-miniapp=active`, `/app/` вернул `200`, `hysteria-server=active`, UDP `:8443` слушает.
- В админской карточке клиента добавлена кнопка `Удалить ключ` для `account_origin=miniapp`. Backend endpoint `/api/admin/client/delete` удаляет только Mini App ключи: x-ui TCP/xHTTP managed clients, Hysteria user, отзывает subscription token и снимает account_link; legacy keys защищены ошибкой `legacy_delete_blocked`. Backup `20260812-132115`; локально `21 OK`; после деплоя `telegram-miniapp=active`, `/app/` вернул `200`, no-auth delete вернул `403 admin_forbidden`, `hysteria-server=active`, UDP `:8443` слушает.
- Исправлено отображение после удаления: админские списки и карточка клиента больше не возвращают `vpn_accounts.status='deleted'`. Backup `20260812-132820`; локально `22 OK`; после деплоя `telegram-miniapp=active`, `/app/` вернул `200`, `hysteria-server=active`, UDP `:8443` слушает. На prod DB: `deleted_total=1`, `visible_total=57`.
- Добавлены настройки ручной оплаты в Mini App: SQLite таблица `payment_settings`, пользовательский endpoint `/api/payment/settings`, админские endpoint `/api/admin/payment-settings` и `/api/admin/payment-settings/save`. В админке появилась страница `Настройки оплат` с картой, банком, получателем, телефоном СБП, комментарием и инструкцией; в тарифах пользователь видит реквизиты только если ручная оплата включена. Backup `20260812-134027`; локально `23 OK`; после деплоя `payment_settings_table=1`, `manual_enabled=0`, `telegram-miniapp=active`, `/app/` вернул `200`, unsigned admin settings `403`, unsigned manual payment `403`, `hysteria-server=active`, UDP `:8443` слушает.
- Исправлены заявки на оплату из клиентского Mini App: кнопка `Telegram Stars` теперь отправляет POST `/api/payment/stars` и создаёт pending-заявку в админке оплат с `currency='STARS'`; кнопка `Карта / СБП` создаёт pending-заявку с `currency='RUB'` при включённой ручной оплате. В `manual_receipts` добавлена колонка `currency`; админский список показывает `Заявка #...` с `₽` или `⭐`, а рублёвая сводка считает только RUB. Backup `20260814-205146`; локально `24 OK`; после деплоя `currency_column=True`, `telegram-miniapp=active`, `/app/` вернул `200`, unsigned payment endpoints вернули `403`, `hysteria-server=active`, UDP `:8443` слушает.
- Исправлено отображение имени купленного/промо Mini App ключа: технический `vpn_accounts.display_name` вида `tg957009905_STARRT_...` остаётся только как server key, а в клиентском кабинете, списке и карточке админки основным именем показывается Telegram `first_name` и `@username` из `account_links -> telegram_users`. Backup `20260814-210244`; локально `24 OK`; после деплоя `telegram-miniapp=active`, `/app/` вернул `200`, `hysteria-server=active`. Проверка проблемного ключа: `tg957009905_STARRT_2c9871` связан с `Геннадий (@gn_pavlov)`.
