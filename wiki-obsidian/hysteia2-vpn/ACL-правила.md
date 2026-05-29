# ACL-правила

**Файл:** `acl.txt`
**Путь на сервере:** `/etc/hysteria/acl.txt`
**Geo-обновление:** каждые 168ч

## Логика маршрутизации

1. **Приватные диапазоны** → `direct`
2. **geoip:ru** (Россия) → `direct`
3. **geosite:category-ru** (российские сайты по гео-BF) → `direct`
4. **Явный список российских доменов** → `direct`
5. **Всё остальное** → SOCKS5 каскад (Финляндия)

## Явно перечисленные домены

**Поисковики/порталы:** yandex.ru, ya.ru, yandex.net, yastatic.net, dzen.ru
**Видео:** kinopoisk.ru, rutube.ru
**Соцсети:** vk.com, vk.ru, vkvideo.ru, vk-cdn.net, vkuser.net, ok.ru
**Почта/CDN:** mail.ru, my.mail.ru, mycdn.me
**Госуслуги:** gosuslugi.ru, esia.gosuslugi.ru, nalog.gov.ru
**Банки:** sberbank.ru, sber.ru, tbank.ru, tinkoff.ru, alfabank.ru, vtb.ru
**Маркетплейсы:** ozon.ru, ozonusercontent.com, wildberries.ru, wb.ru, avito.ru
**Логистика:** cdek.ru, 2gis.ru
**Операторы:** mts.ru, megafon.ru, beeline.ru, tele2.ru
**Прочее:** mos.ru

## Зачем

Российские сайты идут напрямую с сервера (снижение задержки). Трафик на зарубежные ресурсы уходит через [[Каскад]] (Финляндия) для обхода блокировок.

## Источники
- `sources/Hysteria2/config/acl.txt`
