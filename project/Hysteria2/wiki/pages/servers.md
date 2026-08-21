# Servers

## Main Server

- IP: `62.113.105.38`
- Hostname: `hlamnndyjf`
- Domain: `hist.yupiterpro.ru`
- Project SSH key: `ssh-keys/id_hysteria_rsa`

Verified 2026-08-11:

- `hysteria-server=active`
- `hysteria-manager=active`
- `nginx=active`
- `listen: :8443` in `/etc/hysteria/config.yaml`
- Auth URL: `http://127.0.0.1:8081/auth`
- Hysteria Traffic Stats API listens on `127.0.0.1:9999` with secret from `/etc/telegram-miniapp.env`.
- User count on server: `21`

## Cascade Server

- IP: `193.164.155.153`
- Hostname: `server-pflm6j`
- Project SSH key: `ssh-keys/id_193_164_155_153`
- Main project SSH key also worked on 2026-08-11: `ssh-keys/id_hysteria_rsa`

Verified 2026-08-11:

- `wireproxy=active`
- `x-ui=active`
- `crowdsec=active`
- x-ui panel updated from `1.11.1` to `1.11.4` on 2026-08-11.
- `xray` unit reported inactive, but `xray-linux-amd6` processes listened on `:443` and `:18443`.
- `wireproxy` listened on `127.0.0.1:40000`.
- x-ui panel listens on `:21292`; subscription server listens on `:21293`.

## Verification Result

Full client path tested from local machine:

```text
hysteria client -> hist.yupiterpro.ru:8443 -> cascade -> api.ipify.org
```

Observed external IP: `193.164.155.153`.
