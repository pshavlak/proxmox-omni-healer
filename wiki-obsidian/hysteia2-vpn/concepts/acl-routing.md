---
title: ACL Routing
created: 2026-06-08
updated: 2026-06-08
type: concept
tags: [acl, geoip, geosite, маршрутизация, direct]
sources: [config/acl.txt, config/config.yaml, README.md]
confidence: high
---

# ACL Routing

Система правил ACL (Access Control List) на [[hysteria-2-server]], определяющая, через какой outbound направлять трафик. Российские сайты — напрямую, иностранные — через [[socks5-cascade|cSOCKS5 каскад]].

## Механизм работы

Hysteria 2 использует ACL-файл в формате правил с двумя действиями:

- **`direct(...)`** — отправить трафик напрямую (outbound `direct`)
- **`reject(...)`** — заблокировать трафик
- Отсутствие правила → fallback на outbound по умолчанию (`exit_socks` — SOCKS5 каскад)

Порядок правил имеет значение: **первое совпадение выигрывает**.

## Структура ACL

### 1. Приватные сети — напрямую

```acl
direct(geoip:private)
```
Локальные/частные адреса не должны уходить на внешние прокси.

### 2. Российские ресурсы — напрямую

```acl
direct(geoip:ru)
direct(geosite:category-ru)
```

Два слоя: по геолокации IP (GeoIP) и по списку доменов (GeoSite).

### 3. Конкретные российские сервисы

Поимённые записи для критически важных сервисов, где нужно гарантировать прямой выход:

**Поиск и медиа:** yandex.ru, ya.ru, yandex.net, yastatic.net, dzen.ru, kinopoisk.ru, rutube.ru

**Соцсети:** vk.com, vk.ru, vkvideo.ru, vk-cdn.net, vkuser.net, ok.ru

**Почта:** mail.ru, my.mail.ru, mycdn.me

**Госуслуги:** gosuslugi.ru, esia.gosuslugi.ru, nalog.gov.ru, mos.ru

**Банки:** sberbank.ru, sber.ru, tbank.ru, tinkoff.ru, alfabank.ru, vtb.ru

**Маркетплейсы:** ozon.ru, ozonusercontent.com, wildberries.ru, wb.ru, avito.ru

**Логистика:** cdek.ru

**Гео:** 2gis.ru

**Операторы:** mts.ru, megafon.ru, beeline.ru, tele2.ru

### 4. Блокировка мёртвых доменов

```acl
reject(suffix:meta.fmgid.com)
```

Добавлено 08.06.2026. Мёртвый домен `meta.fmgid.com` засорял логи таймаутами подключения.

## Обновление GeoIP/GeoSite

```yaml
geoUpdateInterval: 168h  # обновление раз в неделю
```

Hysteria 2 автоматически обновляет базы GeoIP и GeoSite каждые 168 часов (7 дней).

## Логика принятия решений

```
Входящий запрос
  → SNI определён (sniff.enable=true)
    → Проверка ACL
      → geoip:ru или geosite:category-ru или конкретный домен → DIRECT
      → reject(...) → БЛОК
      → Ничего не подошло → SOCKS5 каскад (default)
```

## Связанные страницы

- [[hysteria-2-server]] — сервер с ACL
- [[socks5-cascade]] — куда уходит не-российский трафик
- [[infrastructure-architecture]] — общая архитектура
