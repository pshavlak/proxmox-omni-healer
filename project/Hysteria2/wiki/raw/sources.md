# Sources

## Local Sources

- `README.md` - инструкция восстановления и исторический контекст.
- `config/config.yaml` - фактический Hysteria config backup.
- `config/acl.txt` - direct/reject ACL rules.
- `config/users.json` - user auth database backup. Contains secrets.
- `manager/app.py` - Flask manager and Hysteria HTTP auth endpoint.
- `manager/hysteria-users.sh` - CLI user management script.
- `nginx/hist.yupiterpro.ru` - nginx public HTTPS and hidden manager route.
- `systemd/*.service` - service units.

## External Sources

- Karpathy LLM Wiki gist: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
  - Used for wiki structure: raw sources, maintained markdown wiki, schema, index, log, lint workflow.

## Live Checks

- 2026-08-11 SSH checks against `62.113.105.38` and `193.164.155.153`.
- 2026-08-11 local Hysteria client check through `hist.yupiterpro.ru:8443`.
