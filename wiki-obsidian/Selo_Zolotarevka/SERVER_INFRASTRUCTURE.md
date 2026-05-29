# Серверная инфраструктура

## Развёрнутый стек

| Компонент | Версия | Статус |
|-----------|--------|--------|
| OS | Debian (Proxmox LXC контейнер) | ✅ |
| Веб-сервер | Apache 2.4.65 (mpm_prefork) | ✅ |
| PHP | 8.4 (FPM) | ✅ |
| База данных | MariaDB (через mysql) | ✅ |
| WordPress | 6.x | ✅ |

## Сервер

- **IP**: 192.168.1.64
- **Хостнейм**: `wordpress`
- **Хост-система**: Proxmox VE (ядро 6.17.13-1-pve)
- **Uptime**: ~5 часов (после перезапуска контейнера)
- **RAM**: 2.0GB
- **Диск**: 20GB (LVM, `/dev/mapper/pve-vm--105--disk--0`)
- **Swap**: 512MB

## Установка

- WordPress установлен в `/var/www/html/wordpress/`
- Apache VirtualHost: `DocumentRoot /var/www/html/wordpress`
- ServerName: `yourdomain.com` (не настроен)
- База: `wordpress_db`

## Плагины (активные)

- `akismet` — антиспам
- `essential-real-estate` — недвижимость
- `kk-star-ratings` — рейтинги
- `woocommerce` — интернет-магазин

## Тема

- `aster-real-estate` (кастомная тема недвижимости)
- Дефолтные темы: `twentytwentythree`, `twentytwentyfour`, `twentytwentyfive`

## Известные проблемы и решения

### URL сайта указывал на неверный IP
- **Проблема**: siteurl и home в wp_options были установлены на `http://192.168.1.65`, хотя контейнер на `192.168.1.64`. Из-за этого все CSS, JS, изображения и API-запросы пытались загружаться с несуществующего адреса, вызывая задержки при открытии страниц.
- **Решение**: обновлены поля в БД через `UPDATE wp_options SET option_value='http://192.168.1.64' WHERE option_name IN ('siteurl','home')`
- **Дата**: 29.05.2026

## Производительность

- Загрузка CPU: < 0.5 в простое
- PHP-FPM: `pm.max_children = 5` (настроено консервативно)
- PHP memory_limit: 512M
- Медленные запросы MySQL: 0
- TTFB локально: ~0.4 сек
- Проблема URL исправлена, что должно ускорить загрузку в браузере

## Рекомендации

- Сменить `yourdomain.com` на реальный домен
- Рассмотреть Nginx вместо Apache (легче, кэширование)
- Настроить внешний IP/домен для доступа из интернета
- Установить WP-CLI для удобного управления
- Рассмотреть увеличение `pm.max_children` при росте посещаемости
