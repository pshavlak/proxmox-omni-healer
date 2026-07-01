---
title: WireProxy
created: 2026-06-08
updated: 2026-06-08
type: entity
tags: [wireproxy, wireguard, компоненты, инфраструктура, прокси]
sources: [README.md]
confidence: high
---

# WireProxy

**WireProxy** — легковесный прокси-клиент, который создаёт WireGuard-туннель и предоставляет локальный HTTP/SOCKS5 прокси для выхода через этот туннель. Используется на [[cascade-server]] для маршрутизации трафика через Cloudflare WARP.

## Роль в инфраструктуре

WireProxy — **финальный выход** всей иностранного трафика:

```
SOCKS5 каскад (193.164.155.153:18443)
  → WireProxy (127.0.0.1:40000) — WireGuard
    → engage.cloudflareclient.com:2408 (Cloudflare WARP)
      → Интернет
```

## Технические детали

| Параметр | Значение |
|----------|----------|
| **Версия** | v1.0.9 |
| **Локальный адрес** | `127.0.0.1:40000` |
| **Endpoint** | `engage.cloudflareclient.com:2408` |
| **Тип туннеля** | WireGuard |
| **Цель** | Выход в интернет через Cloudflare WARP |

## Известные проблемы

**Утечка памяти** — [[wireproxy-memory-leak]]. Потребление растёт ~20MB/час, за 2-3 дня достигает 3GB.

### Текущие меры

- Ежедневный перезапуск через cron в 4:00 (`systemctl restart wireproxy`)
- Swap 2GB для смягчения пиков
- `vm.swappiness = 10`

## Управление

```bash
# Статус
systemctl status wireproxy

# Логи
journalctl -u wireproxy -n 20
```

## Связанные страницы

- [[cascade-server]] — сервер, на котором работает WireProxy
- [[wireproxy-memory-leak]] — проблема утечки памяти
- [[xray-server]] — Xray, передающий трафик в WireProxy
- [[infrastructure-architecture]] — общая архитектура
