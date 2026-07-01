---
title: Hysteria 2 Protocol
created: 2026-06-08
updated: 2026-06-08
type: concept
tags: [hysteria-2, quic, протоколы, http3]
sources: [config/config.yaml, README.md, systemd/hysteria-server.service]
confidence: high
---

# Hysteria 2 Protocol

**Hysteria 2** — прокси-протокол следующего поколения, работающий поверх QUIC (HTTP/3). Отличается высокой производительностью в условиях плохого сетевого соединения благодаря маскировке под обычный HTTP/3 трафик.

Версия на сервере: **v2.9.2**.

## Особенности

- **QUIC transport** — мультиплексирование, встроенная защита от потери пакетов
- **Маскировка под HTTP/3** — трафик неотличим от обычного браузерного
- **TLS шифрование** — через Let's Encrypt сертификаты
- **Sniffing** — определение типа протокола на лету для принятия решений о маршрутизации
- **HTTP-аутентификация** — проверка паролей через внешний HTTP-бекенд ([[hist-yupiterpro-ru]])
- **ACL с GeoIP** — маршрутизация на основе геолокации и списков доменов

## Схема аутентификации

```
Клиент → Hysteria 2 сервер → HTTP POST /auth (127.0.0.1:8081)
  → Flask проверяет пароль по users.json
  → 200 OK или 401 Unauthorized
```

## Конфигурация ключевых параметров

| Параметр | Значение | Описание |
|----------|----------|----------|
| `listen` | `:8443` | Порт прослушивания |
| `tls.cert` | Let's Encrypt fullchain | Сертификат TLS |
| `auth.type` | `http` | Метод аутентификации |
| `auth.http.url` | `http://127.0.0.1:8081/auth` | Эндпоинт проверки |
| `resolver` | `77.88.8.8:53` | Яндекс DNS |
| `sniff.enable` | `true` | Определение протоколов |
| `acl.file` | `/etc/hysteria/acl.txt` | Правила ACL |
| `outbounds` | `exit_socks` + `direct` | Два канала выхода |

## Outbounds

Hysteria 2 поддерживает несколько outbound-каналов:

1. **`exit_socks`** (SOCKS5) — трафик на иностранные ресурсы через [[cascade-server]] в Хельсинки
2. **`direct`** — прямой выход для российских ресурсов (согласно ACL)

Выбор outbound управляется ACL правилами. См. [[acl-routing]].

## Связанные страницы

- [[hysteria-2-server]] — сервер с Hysteria 2
- [[acl-routing]] — правила ACL для выбора outbound
- [[socks5-cascade]] — каскадное проксирование
- [[infrastructure-architecture]] — общая архитектура
- [[user-management]] — аутентификация пользователей
