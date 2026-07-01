---
title: Hysteria 2 Server
created: 2026-06-08
updated: 2026-06-08
type: entity
tags: [сервер, hysteria-2, quic, инфраструктура]
sources: [config/config.yaml, systemd/hysteria-server.service, README.md]
confidence: high
---

# Hysteria 2 Server

Основной Hysteria 2 VPN сервер инфраструктуры. Принимает клиентские подключения по протоколу Hysteria 2 (поверх QUIC), выполняет ACL-маршрутизацию трафика: российские сайты отправляет напрямую, иностранные — через каскадный SOCKS5 прокси.

## Основные характеристики

| Параметр | Значение |
|----------|----------|
| **IP адрес** | `62.113.105.38` |
| **Хостнейм** | `hlamnndyjf` |
| **Домен** | `hist.yupiterpro.ru` |
| **Порт** | `8443` (ранее был `:443`) |
| **Версия Hysteria** | v2.9.2 |
| **Дата сохранения конфигурации** | 28.05.2026 |
| **Метод аутентификации** | HTTP (через Flask backend на `127.0.0.1:8081`) |
| **DNS резолвер** | Яндекс DNS (`77.88.8.8:53`) |
| **Логирование** | `info` (ранее было `debug`, понижено 08.06.2026) |

## Конфигурация

Конфигурация сервера (`config.yaml`):
- TLS через Let's Encrypt (сертификаты `/etc/letsencrypt/live/hist.yupiterpro.ru/`)
- Аутентификация: HTTP-коллбэк на веб-панель (`http://127.0.0.1:8081/auth`)
- DNS — Яндекс DNS по UDP/TCP
- **Sniffing** включён для определения типа трафика
- **Два outbound:** `exit_socks` (SOCKS5 каскад) и `direct` (прямой выход)
- ACL из файла `/etc/hysteria/acl.txt`, обновление GeoIP каждые 168 часов

См. [[socks5-cascade]] и [[acl-routing]] для деталей маршрутизации.

## Изменения в конфигурации (08.06.2026)

- Порт изменён `:443` → `:8443` (приведено к фактическому состоянию)
- Уровень логов `debug` → `info` (меньше спама)

## Systemd

Сервис запускается через `hysteria-server.service`:
- Исполняемый файл: `/usr/local/bin/hysteria server --config /etc/hysteria/config.yaml`
- Пользователь: `hysteria`
- Capabilities: `CAP_NET_ADMIN`, `CAP_NET_BIND_SERVICE`, `CAP_NET_RAW`
- `NoNewPrivileges=true`
- Переменная окружения `HYSTERIA_LOG_LEVEL=info`

## Пользователи

19 пользователей VPN (см. [[user-management]]). Аутентификация по паролю через HTTP-бекенд.

## SSH-доступ

```bash
ssh -i id_hysteria_rsa root@62.113.105.38
```

## Связанные страницы

- [[cascade-server]] — каскадный SOCKS5 сервер
- [[socks5-cascade]] — схема каскадирования
- [[acl-routing]] — правила ACL
- [[user-management]] — управление пользователями
- [[infrastructure-architecture]] — общая архитектура
