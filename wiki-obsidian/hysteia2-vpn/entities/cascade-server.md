---
title: Cascade SOCKS5 Server
created: 2026-06-08
updated: 2026-06-08
type: entity
tags: [сервер, socks5, каскад, vps, инфраструктура]
sources: [config/config.yaml, README.md]
confidence: high
---

# Cascade SOCKS5 Server

Каскадный SOCKS5 сервер, расположенный в Хельсинки (Финляндия). Через него проходит иностранный трафик от [[hysteria-2-server]]. Сервер также выступает самостоятельной точкой входа через Xray (VLESS+REALITY).

## Основные характеристики

| Параметр | Значение |
|----------|----------|
| **IP адрес** | `193.164.155.153` |
| **Локация** | Хельсинки, Финляндия |
| **Провайдер** | AS56971 Cloud |
| **SOCKS5 порт** | `:18443` |
| **Credentials SOCKS5** | `cascade` / `d17ed2425d8b1c37b5ee00ed4e28cd0b` |

## Компоненты на сервере

- **[[xray-server]]** — VLESS + REALITY (порт 443, 26 пользователей) и SOCKS5 (порт 18443)
- **[[wireproxy]]** — WireGuard-туннель к Cloudflare WARP (v1.0.9)
- **X-UI** — панель управления Xray
- **CrowdSec** — IDS/IPS система защиты
- **3dp-manager** — управление 3D-принтером (Docker)

## Схема прохождения трафика

```
Клиенты (Hysteria / VLESS)
  → Hysteria сервер (62.113.105.38:8443)
    → SOCKS5 каскад (193.164.155.153:18443) — Xray
      → WireProxy (127.0.0.1:40000) — WireGuard
        → Cloudflare WARP
          → Интернет
```

## Известные проблемы

[[wireproxy-memory-leak]] — утечка памяти WireProxy v1.0.9 (~20MB/час).

## SSH-доступ

```bash
ssh -i id_193_164_155_153 root@193.164.155.153
```

## Связанные страницы

- [[hysteria-2-server]] — основной Hysteria сервер
- [[xray-server]] — Xray на каскадном сервере
- [[wireproxy]] — WireGuard-туннель
- [[socks5-cascade]] — схема каскадирования
- [[infrastructure-architecture]] — общая архитектура
- [[wireproxy-memory-leak]] — проблема утечки памяти
