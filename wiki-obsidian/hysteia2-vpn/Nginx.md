# Nginx

**Конфиг:** `/etc/nginx/sites-available/hist.yupiterpro.ru`

## Структура

### server {} на 443 (SSL)
- Сайт-заглушка (`root /var/www/html`)
- Скрытая панель управления по пути `/44169d2dba4d0fd5/`
- Блокировка прямого доступа к `/login`, `/logout`, `/add`, `/delete`

### server {} на 80
- Редирект на HTTPS

## Скрытая панель

```
location /44169d2dba4d0fd5/ {
    proxy_pass http://127.0.0.1:8081/;
    sub_filter '="/login' '="/44169d2dba4d0fd5/login';
    ...
}
```

Nginx переписывает:
- пути в HTML (`sub_filter`)
- Set-Cookie Path
- редиректы Flask

Прямые маршруты `/login`, `/logout` и т.д. возвращают 404, чтобы не светить панель.

## Сертификаты

Путь к сертификатам Let's Encrypt:
```
/etc/letsencrypt/live/hist.yupiterpro.ru-0001/fullchain.pem
/etc/letsencrypt/live/hist.yupiterpro.ru-0001/privkey.pem
```

См. [[Восстановление]] — certbot для выпуска, а также структурированную версию: [[entities/hist-yupiterpro-ru]].

## Источники
- `sources/Hysteria2/nginx/hist.yupiterpro.ru`
