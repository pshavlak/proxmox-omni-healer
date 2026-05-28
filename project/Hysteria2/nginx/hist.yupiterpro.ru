server {
    listen 443 ssl;
    server_name hist.yupiterpro.ru;

    ssl_certificate /etc/letsencrypt/live/hist.yupiterpro.ru-0001/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hist.yupiterpro.ru-0001/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    root /var/www/html;
    index index.html;

    # Сайт-заглушка — корень
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Блокируем прямой доступ к Flask-маршрутам (чтобы случайно не попасть на заглушку)
    location = /login { return 404; }
    location = /logout { return 404; }
    location = /add { return 404; }
    location = /delete { return 404; }

    # Скрытая панель управления
    location /44169d2dba4d0fd5/ {
        proxy_pass http://127.0.0.1:8081/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Отключаем gzip чтобы sub_filter всегда работал
        proxy_set_header Accept-Encoding "";

        # Переписываем редиректы Flask
        proxy_redirect / /44169d2dba4d0fd5/;

        # Переписываем Set-Cookie Path
        proxy_cookie_path / /44169d2dba4d0fd5/;

        # Переписываем абсолютные пути в HTML
        sub_filter '="/login' '="/44169d2dba4d0fd5/login';
        sub_filter '="/logout' '="/44169d2dba4d0fd5/logout';
        sub_filter '="/add' '="/44169d2dba4d0fd5/add';
        sub_filter '="/delete' '="/44169d2dba4d0fd5/delete';
        sub_filter '="/static/' '="/44169d2dba4d0fd5/static/';
        sub_filter_once off;
    }
}

server {
    listen 80;
    server_name hist.yupiterpro.ru;
    return 301 https://$host$request_uri;
}
