# Codex Instructions

## Project: Hysteria2 Cascade VPN

Краткие ответы. Сначала проверяй факты в локальной wiki, затем в коде/конфигах, затем на серверах.

## Wiki Workflow

- Wiki lives in `wiki/`.
- Read `wiki/index.md` first.
- Append every meaningful maintenance/deploy/check event to `wiki/log.md`.
- Keep source material in `wiki/raw/` immutable where practical.
- Update relevant pages in `wiki/pages/` when facts change.
- Prefer factual notes with commands, dates, server names, ports, and observed outputs.

## Safety

- Do not restart `hysteria-server` unless explicitly needed and stated.
- For production checks, prefer read-only commands first.
- Preserve `/etc/hysteria/users.json`, certificates, and SSH keys.
- Before replacing deployed manager files, copy timestamped backups.
- Never print full passwords, user auth tokens, or private keys in chat.

## Verified State

- Main server: `62.113.105.38`, host `hlamnndyjf`.
- Domain: `hist.yupiterpro.ru`.
- Hysteria listens on UDP `:8443`.
- Nginx listens on TCP `:443`.
- Manager listens on `127.0.0.1:8081`.
- Cascade SOCKS: `193.164.155.153:18443`.
- Verified on 2026-08-11: Hysteria client via `hist.yupiterpro.ru:8443` exits as `193.164.155.153`.
