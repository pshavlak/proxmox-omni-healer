# Telegram Mini App Plan

## Goal

Build a Telegram Mini App client cabinet for the existing Hysteria2 cascade VPN without breaking active clients on either server.

Current production client data must remain the source of truth until a migration is explicitly tested:

- Main server `62.113.105.38`: Hysteria users in `/etc/hysteria/users.json`.
- Cascade server `193.164.155.153`: x-ui/Xray data in `/etc/x-ui/x-ui.db`.

## Non-Breaking Rules

- Do not restart `hysteria-server` for Mini App work unless explicitly required and announced.
- Do not overwrite `/etc/hysteria/users.json` or `/etc/x-ui/x-ui.db` without timestamped backups.
- Start with read-only import and display; write operations are introduced only after validation on copies.
- Never expose full user auth tokens, Telegram bot token, payment secrets, private keys, or admin passwords in chat, logs, or UI.
- Keep existing Hysteria endpoint `hist.yupiterpro.ru:8443` unchanged for current clients.
- Keep cascade SOCKS `193.164.155.153:18443` unchanged.

## Target Architecture

```text
Telegram Bot
  -> opens Mini App
  -> sends reminders and admin notifications

Telegram Mini App
  -> client cabinet
  -> subscription status
  -> config/subscription links
  -> tariff and payment UI

Backend API
  -> Telegram auth validation
  -> subscription logic
  -> account linking
  -> config generation
  -> future payment webhooks

Bot database
  -> Telegram users
  -> VPN account links
  -> subscription tokens
  -> plans/payments
  -> audit log

Existing VPN data
  -> /etc/hysteria/users.json
  -> /etc/x-ui/x-ui.db
```

## Data Model

Minimum tables:

- `telegram_users`: `telegram_id`, `username`, `first_name`, `role`, `created_at`, `last_seen_at`, `trial_used`, `is_whitelisted`.
- `vpn_accounts`: `id`, `server_type`, `server_name`, `external_key`, `display_name`, `status`, `routing_mode`, `traffic_*`, `direct_*_config_uri`, `account_origin`, `created_by_promocode`, `auto_delete_at`.
- `account_links`: `telegram_user_id`, `vpn_account_id`, `linked_at`, `link_method`.
- `subscriptions`: `vpn_account_id`, `status`, `starts_at`, `expires_at`, `plan_id`, `traffic_limit_bytes` (0 = unlimited), `last_expiry_notified_at`.
- `subscription_tokens`: `vpn_account_id`, `token`, `created_at`, `revoked_at`.
- `plans`: `code`, `title`, `duration_days`, `price`, `currency`, `is_active`.
- `wallets`: `telegram_user_id`, `balance`, `currency`.
- `manual_receipts`: `telegram_user_id`, `amount`, `currency`, `receipt_note`, `status`, `created_at`, `processed_at`.
- `transactions`: `telegram_user_id`, `type`, `amount`, `description`, `created_at`.
- `audit_log`: `actor`, `action`, `target`, `result`, `timestamp`, `metadata`.
- `promocodes`: `code`, `bonus_days`, `discount_percent`, `max_activations`, `activations_count`, `expires_at`, `issue_key_on_activation`.
- `traffic_snapshots`, `connection_events`, `subscription_devices`, `invite_tokens`.

## Subscription Links

Each VPN account gets a separate subscription token. It must not be equal to the VPN password.

Example public shape:

```text
https://hist.yupiterpro.ru/sub/<token>
```

The endpoint checks:

- token exists and is not revoked;
- linked VPN account exists;
- subscription status is active;
- `expires_at` is in the future.

If active, it returns the config format requested by the client. If expired, it returns an expired-subscription response without exposing secrets.

Initial formats:

- Hysteria2 URI.
- Hysteria2 YAML.

Future formats:

- sing-box.
- Clash.
- x-ui/VLESS subscription format.

## User Flows

### Existing Client Linking

1. Admin opens a user in Mini App admin view.
2. Admin generates a one-time claim code.
3. Client sends `/start <code>` or enters code in Mini App.
4. Backend links Telegram account to existing VPN account.
5. Client sees status, expiry, and subscription link.

### Client Cabinet

- Show active/expired status.
- Show expiry date.
- Show subscription link with copy button.
- Show generated config.
- Show instructions by platform: iOS, Android, Windows, macOS.
- Show available tariffs.

### Admin Cabinet

- List clients from bot database and imported VPN sources.
- Search by VPN account name or Telegram username.
- Link/unlink Telegram account.
- Set or extend subscription expiry manually.
- Revoke and regenerate subscription link.
- Create Hysteria user after write support is enabled.
- Disable/delete users only with explicit confirmation.

## Implementation Phases

### Phase 1: Read-Only Foundation

- Create project structure for bot, backend API, Mini App frontend, and local SQLite database.
- Add Telegram Mini App auth validation.
- Import Hysteria users from a copied `users.json`.
- Import x-ui clients from a copied `x-ui.db`.
- Build Mini App cabinet with mock status/config display.
- Add admin-only read-only client list.
- No production writes.

Verification:

- Unit tests for importers.
- Redacted fixture tests.
- Mini App opens from Telegram bot button.
- Existing VPN clients unaffected.

### Phase 2: Subscription Layer

- Add `subscriptions` and `subscription_tokens`.
- Generate subscription links independent of VPN passwords.
- Add `/sub/<token>` endpoint.
- Return Hysteria configs for active subscriptions.
- Return expired response for inactive subscriptions.
- Add manual admin expiry editing.

Verification:

- Active token returns valid config.
- Expired token does not return auth secret.
- Revoked token stops working.
- Hysteria smoke test still exits as `193.164.155.153`.

### Phase 3: Safe Hysteria Writes

- Status 2026-08-11: implemented for creating new Hysteria keys from Mini App admin UI.
- Current scope: create only; test cleanup uses maintenance helper, not a public UI delete action.
- x-ui client creation is intentionally deferred and remains read-only until safe API-based integration.

- Extract current manager user logic into a shared service module.
- Add atomic write for `/etc/hysteria/users.json`.
- Add timestamped backup before each write.
- Add create/delete/disable user operations through backend.
- Restart only `hysteria-manager` if needed; do not restart `hysteria-server`.

Verification:

- Add test user.
- Auth endpoint accepts test user.
- Delete or disable test user.
- Existing users still authenticate.

### Phase 4: x-ui Integration

- Prefer x-ui API if stable and authenticated locally.
- If direct SQLite is needed, work on a copy first and document exact fields.
- Always back up `/etc/x-ui/x-ui.db` before writes.
- Start with read-only traffic/status display.
- Add write operations only after schema-specific tests.

Verification:

- x-ui remains active.
- `wireproxy` remains active.
- `18443`, `443`, `40000` ports remain listening.
- Cascade SOCKS check from main server still returns `193.164.155.153`.

### Phase 4.1: Safe x-ui Direct Key Creation

Approach for new Mini App keys:

- Do not add new clients into the existing production inbounds `443` or `55332` by default.
- Create one separate managed x-ui inbound for Mini App direct keys, with its own remark/tag, port, and Reality settings.
- Store that inbound id in `/etc/telegram-miniapp.env` as `XUI_MANAGED_INBOUND_ID`.
- Use x-ui API over local HTTPS instead of direct writes to `/etc/x-ui/x-ui.db`.
- Keep `/etc/x-ui/x-ui.db` backups before enabling write operations.
- The Mini App admin action creates a direct x-ui client only inside the configured managed inbound and then stores the generated VLESS URI in Mini App DB `vpn_accounts.direct_config_uri`.
- If the managed inbound/env is not configured, the Mini App must return a configuration error and must not change VPN state.
- Existing clients keep using their current inbounds and are not migrated automatically.

Activation checks:

- x-ui API login works locally on cascade.
- Managed inbound exists and is enabled.
- Adding a test client to the managed inbound does not change client counts in existing inbounds.
- x-ui remains active; `443`, `55332`, `18443`, `40000`, `21292`, `21293` remain listening.
- Test direct VLESS profile connects successfully.
- Full Hysteria cascade path still exits through `193.164.155.153`.

### Phase 5: Payments

- Keep payment module provider-neutral.
- Add manual payment status first.
- Add webhook-compatible payment abstraction.
- Later connect YooKassa, CloudPayments, Stripe, crypto, or another provider.

Payment flow:

1. Client selects plan.
2. Backend creates invoice.
3. Provider confirms payment by webhook.
4. Backend extends `expires_at`.
5. Subscription link starts or continues returning active config.

Verification:

- Paid webhook extends subscription once.
- Duplicate webhook is idempotent.
- Failed payment does not extend access.

### Phase 6: Production Deployment

- Deploy bot/backend as separate systemd service.
- Keep Mini App frontend behind nginx under a separate path, for example `/app/`.
- Keep subscription endpoint under `/sub/`.
- Keep hidden manager path unchanged.
- Add `.env` for secrets on the server only.
- Back up all touched deployed files before replacement.

Post-deploy checks:

- Bot responds to `/start`.
- Mini App opens.
- Existing Hysteria client works.
- Existing x-ui/cascade path works.
- Subscription link returns config for active test account.
- Expired test account does not receive config.

## Recommended MVP Scope

Build first:

- Telegram bot with Mini App button.
- Mini App client cabinet.
- Admin read-only list.
- Existing account linking by one-time code.
- Manual subscription expiry.
- Subscription link endpoint for Hysteria users.

Defer:

- Automatic payments.
- x-ui write operations.
- Automatic deletion of expired users.
- Full traffic accounting.
