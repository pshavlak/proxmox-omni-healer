# Security

## Sensitive Material

The project contains sensitive material:

- `config/users.json` - active or historical user auth tokens.
- `config/config.yaml` - cascade SOCKS credentials.
- `ssh-keys/id_hysteria_rsa` - private SSH key for the main server.
- `ssh-keys/id_193_164_155_153` - private SSH key for the cascade server.
- README includes operational secrets from the original backup.

Do not paste secrets into chat or logs. Redact with `[redacted]`.

## Fixed on 2026-08-11

- Flask manager no longer logs raw `/auth` request bodies.
- Flask manager no longer logs received auth passwords.
- Admin panel auth now uses signed Flask `session` instead of trusting arbitrary `admin_session` cookie presence.
- Admin password comparison uses `secrets.compare_digest`.
- CLI user add now writes JSON through Python `json`, not `sed`.
- CLI validates usernames as `A-Za-z0-9_.-`.

## Remaining Risks

- Flask app still runs via built-in development server behind localhost. It is currently only bound to `127.0.0.1:8081`, but a production WSGI server would be cleaner.
- Secrets are still present in the local project files.
- Existing old logs on the server contain auth passwords from before the fix.
- `app.secret_key` is generated on every manager restart, so panel sessions are invalidated after restart. This is acceptable operationally but worth knowing.
