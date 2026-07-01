---
title: SOCKS5 Cascade
created: 2026-06-08
updated: 2026-06-08
type: concept
tags: [socks5, каскад, прокси, маршрутизация]
sources: [config/config.yaml, README.md]
confidence: high
---

# SOCKS5 Cascade

Механизм перенаправления трафика с [[hysteria-2-server]] на [[cascade-server]] в Хельсинки через SOCKS5 прокси для выхода в иностранный интернет.

## Конфигурация

На Hysteria сервере настроен outbound `exit_socks`:

```yaml
outbounds:
  - name: exit_socks
    type: socks5
    socks5:
      addr: 193.164.155.153:18443
      username: cascade
      password: d17ed2425d8b1c37b5ee00ed4e28cd0b
  - name: direct
    type: direct
```

Credentials: `cascade` / `d17ed2425d8b1c37b5ee00ed4e28cd0b`.

## Роль в архитектуре

Каскад решает две задачи:

1. **Обход блокировок** — трафик выходит из РФ через финский сервер
2. **Анонимизация** — реальный IP клиента скрыт дважды (Hysteria + SOCKS5)

Трафик, прошедший через SOCKS5, далее идёт через [[xray-server]] → [[wireproxy]] → Cloudflare WARP → интернет.

## Проверка

```bash
curl --socks5-hostname cascade:d17ed2425d8b1c37b5ee00ed4e28cd0b@193.164.155.153:18443 https://api.ipify.org
```

## Связанные страницы

- [[cascade-server]] — сервер, принимающий SOCKS5 трафик
- [[hysteria-2-server]] — сервер, отправляющий трафик в каскад
- [[acl-routing]] — правила, определяющие, какой трафик идёт в каскад
- [[infrastructure-architecture]] — общая архитектура
