# Hysteria 2

**Версия:** v2.9.2
**Сервер:** `62.113.105.38` (hlamnndyjf)
**Домен:** `hist.yupiterpro.ru`

Hysteria 2 — VPN-протокол на базе QUIC (HTTP/3). Отличается высокой скоростью за счёт агрессивной мультиплексации и модифицированного алгоритма контроля перегрузки (Brutal).

## Состав проекта

Проект состоит из нескольких компонентов:
- [[Конфигурация]] — `config.yaml`, каскад SOCKS5 (с 16.04.2026)
- [[ACL-правила]] — гео-маршрутизация (российские сайты напрямую)
- [[Пользователи]] — `users.json`, HTTP-авторизация
- [[Веб-панель Manager]] — Flask UI для управления пользователями
- [[Systemd-сервисы]] — `hysteria-server`, `hysteria-manager`
- [[Nginx]] — фронтенд с сайтом-заглушкой и скрытой панелью
- [[CLI-скрипт]] — `hysteria-users.sh` для управления через консоль

## Схема работы

```
Клиент (hysteria2://...)
  → Сервер :443 (Hysteria)
    → ACL проверка:
      ├── Российские сайты → напрямую (direct)
      └── Иностранные сайты → SOCKS5 каскад → Финляндия
```

См. [[Архитектура]] для деталей.

## Установка

```bash
bash <(curl -fsSL https://get.hy2.sh/)
```

Или вручную:
```bash
wget https://github.com/apernet/hysteria/releases/latest/download/hysteria-linux-amd64
chmod +x hysteria-linux-amd64
mv hysteria-linux-amd64 /usr/local/bin/hysteria
```

## Источники
- `sources/Hysteria2/README.md`
