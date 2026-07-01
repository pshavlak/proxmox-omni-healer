# Index — Hysteia2 VPN Wiki

> Каталог всех страниц вики. Читай этот файл первым, чтобы найти нужную страницу.
> Обновлено: 2026-06-08 | Всего страниц: 27

## Навигация
- [[Добро пожаловать]] — стартовая страница
- [[CLAUDE]] — схема работы с вики для LLM-агента
- [[SCHEMA]] — теги, фронтматер, конвенции оформления
- [[log]] — хронология изменений

## Основное
- [[Hysteria2]] — обзор проекта, версия v2.9.2
- [[Архитектура]] — схема работы всех компонентов (старая)
- [[infrastructure-architecture]] — архитектура в структурированном формате
- [[Восстановление]] — инструкция по развёртыванию на новом сервере

## Сущности (entities/)

| Страница | Описание |
|----------|----------|
| [[entities/hysteria-2-server]] | Основной Hysteria 2 сервер: IP, порт, конфигурация, systemd |
| [[entities/cascade-server]] | Каскадный SOCKS5 сервер в Хельсинки (193.164.155.153) |
| [[entities/hist-yupiterpro-ru]] | Домен, nginx, Flask-панель управления |
| [[entities/wireproxy]] | WireGuard-туннель к Cloudflare WARP |
| [[entities/xray-server]] | Xray: VLESS+REALITY + SOCKS5 на каскаде |

## Концепции (concepts/)

| Страница | Описание |
|----------|----------|
| [[concepts/hysteria-2-protocol]] | Протокол Hysteria 2: QUIC, аутентификация, outbounds |
| [[concepts/infrastructure-architecture]] | Архитектура: полная схема трафика (структурированно) |
| [[concepts/acl-routing]] | ACL-маршрутизация: geoip/geosite, direct vs SOCKS5 |
| [[concepts/socks5-cascade]] | SOCKS5 каскад через Хельсинки |
| [[concepts/user-management]] | Управление пользователями: 19 пользователей, веб+CLI |
| [[concepts/wireproxy-memory-leak]] | Известная проблема: утечка памяти WireProxy v1.0.9 |

## Конфигурация
- [[Конфигурация]] — config.yaml (каскад, TLS, auth, resolver)
- [[ACL-правила]] — гео-маршрутизация, российские сайты напрямую
- [[Каскад]] — SOCKS5 cascade через Финляндию

## Управление
- [[Пользователи]] — список пользователей (19 шт)
- [[Веб-панель Manager]] — Flask UI на 8081
- [[CLI-скрипт]] — hysteria-users.sh

## Инфраструктура
- [[Systemd-сервисы]] — hysteria-server, hysteria-manager
- [[Nginx]] — сайт-заглушка, скрытая панель

## Все страницы
- [[Добро пожаловать]] — входная точка wiki
- [[CLAUDE]] — инструкция для LLM-агента
- [[SCHEMA]] — теги, фронтматер, конвенции
- [[Hysteria2]] — обзор проекта Hysteria 2 v2.9.2
- [[Архитектура]] — схема работы компонентов (оригинал)
- [[Конфигурация]] — параметры config.yaml
- [[ACL-правила]] — маршрутизация по гео и доменам
- [[Каскад]] — SOCKS5 exit node в Финляндии
- [[Пользователи]] — users.json, список 19 пользователей
- [[Веб-панель Manager]] — Flask-панель на 8081
- [[Systemd-сервисы]] — hysteria-server и hysteria-manager
- [[Nginx]] — фронтенд с сайтом-заглушкой
- [[CLI-скрипт]] — консольное управление hysteria-users.sh
- [[Восстановление]] — развёртывание на новом сервере
- [[entities/hysteria-2-server]] — Hysteria сервер (структурированно)
- [[entities/cascade-server]] — каскадный сервер (структурированно)
- [[entities/hist-yupiterpro-ru]] — домен + nginx + Flask (структурированно)
- [[entities/wireproxy]] — WireProxy на каскаде
- [[entities/xray-server]] — Xray на каскаде
- [[concepts/hysteria-2-protocol]] — Hysteria 2 протокол (структурированно)
- [[concepts/infrastructure-architecture]] — архитектура (структурированно)
- [[concepts/acl-routing]] — ACL правила (структурированно)
- [[concepts/socks5-cascade]] — SOCKS5 каскад (структурированно)
- [[concepts/user-management]] — управление пользователями (структурированно)
- [[concepts/wireproxy-memory-leak]] — проблема WireProxy
- [[log]] — лог изменений
