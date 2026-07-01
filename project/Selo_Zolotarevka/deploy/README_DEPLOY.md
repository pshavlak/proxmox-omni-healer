# Деплой сайта Золотаревка

## Что переносить

Переносить папку `site/`.

Обязательно:
- `app.py`, `config.py`, `database.py`, `models.py`
- `requirements.txt`, `start.sh`
- `admin/`
- `templates/`
- `static/`
- `zolotarevka.db`, если нужно перенести текущий контент

Не переносить:
- `.venv/`
- `.git/`
- `__pycache__/`
- `.DS_Store`
- старые прототипы и WordPress legacy из `archive/`

## Быстрый запуск на сервере

```bash
cd /opt/zolotarevka/site
chmod +x install.sh start.sh
./install.sh
HOST=0.0.0.0 PORT=8000 ./start.sh
```

Проверка:

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/admin/
curl http://127.0.0.1:8000/api/pages
```

## Systemd

```bash
sudo cp deploy/zolotarevka.service /etc/systemd/system/zolotarevka.service
sudo systemctl daemon-reload
sudo systemctl enable --now zolotarevka
sudo systemctl status zolotarevka
```

## Nginx

```bash
sudo cp deploy/nginx-zolotarevka.conf /etc/nginx/sites-available/zolotarevka
sudo ln -s /etc/nginx/sites-available/zolotarevka /etc/nginx/sites-enabled/zolotarevka
sudo nginx -t
sudo systemctl reload nginx
```
