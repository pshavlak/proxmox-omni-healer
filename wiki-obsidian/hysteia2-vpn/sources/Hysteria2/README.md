# Hysteria 2 Server Configuration Backup

**Сервер:** `62.113.105.38` (hlamnndyjf)
**Домен:** `hist.yupiterpro.ru`
**Дата сохранения:** 28.05.2026
**Версия Hysteria:** v2.9.2

## 📁 Структура папки

```
Hysteria2/
├── README.md                    # Этот файл — инструкция по восстановлению
├── config/
│   ├── config.yaml              # Основная конфигурация Hysteria (с каскадом)
│   ├── config.yaml.backup       # Конфигурация без каскада (исходная)
│   ├── users.json               # Все пользователи и их пароли
│   ├── acl.txt                  # ACL правила (российские сайты — напрямую)
│   └── passwords.txt            # Пароли админа и auth
├── systemd/
│   ├── hysteria-server.service  # systemd unit для hysteria
│   └── hysteria-manager.service # systemd unit для веб-панели
├── nginx/
│   └── hist.yupiterpro.ru       # Конфиг nginx для домена
└── manager/
    ├── app.py                   # Flask веб-панель управления пользователями
    └── hysteria-users.sh        # Скрипт управления пользователями (CLI)
```

## 🚀 Инструкция по восстановлению на новом сервере

### 1. Установка Hysteria 2

```bash
# Скачать последнюю версию
bash <(curl -fsSL https://get.hy2.sh/)

# Или вручную:
wget https://github.com/apernet/hysteria/releases/latest/download/hysteria-linux-amd64
chmod +x hysteria-linux-amd64
mv hysteria-linux-amd64 /usr/local/bin/hysteria
```

### 2. Создание пользователя и директорий

```bash
useradd -r -s /bin/false hysteria
mkdir -p /etc/hysteria
mkdir -p /var/lib/hysteria
chown -R hysteria:hysteria /etc/hysteria /var/lib/hysteria
```

### 3. Копирование конфигурации

```bash
# Скопировать все файлы из config/
cp config/config.yaml /etc/hysteria/config.yaml
cp config/users.json /etc/hysteria/users.json
cp config/acl.txt /etc/hysteria/acl.txt
cp config/passwords.txt /etc/hysteria/passwords.txt  # или создать вручную

# Создать файлы паролей
echo "_wk28wOuAf8" > /etc/hysteria/admin_password.txt
echo "1RIMZITidxQTYYyn7ObXyAegHLUa04HcdkPNlMvaT4o=" > /etc/hysteria/auth_password

chown -R hysteria:hysteria /etc/hysteria
```

### 4. Получение SSL-сертификата (Let's Encrypt)

```bash
# Установка certbot
apt install -y certbot python3-certbot-nginx

# Получение сертификата
certbot certonly --nginx -d hist.yupiterpro.ru

# Или standalone (если nginx ещё не настроен):
certbot certonly --standalone -d hist.yupiterpro.ru
```

### 5. Настройка systemd

```bash
cp systemd/hysteria-server.service /etc/systemd/system/
cp systemd/hysteria-manager.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable hysteria-server hysteria-manager
systemctl start hysteria-server hysteria-manager
```

### 6. Настройка nginx

```bash
# Установка nginx
apt install -y nginx

# Копирование конфига
cp nginx/hist.yupiterpro.ru /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/hist.yupiterpro.ru /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default

# Проверка и перезапуск
nginx -t
systemctl restart nginx
```

### 7. Настройка веб-панели

```bash
# Установка Flask
apt install -y python3-flask
# или
pip3 install flask

# Копирование файлов
mkdir -p /opt/hysteria-manager
cp manager/app.py /opt/hysteria-manager/
cp manager/hysteria-users.sh /opt/hysteria-manager/
chmod +x /opt/hysteria-manager/hysteria-users.sh

# Запуск
systemctl restart hysteria-manager
```

### 8. Настройка fail2ban (рекомендуется)

```bash
apt install -y fail2ban

cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 30m
findtime = 10m
maxretry = 3

[sshd]
enabled = true
bantime = 30m
maxretry = 3

[recidive]
enabled = true
bantime = -1
findtime = 1d
maxretry = 3
EOF

systemctl restart fail2ban
```

## 🔧 Полезные команды

### Управление сервисами
```bash
systemctl status hysteria-server    # Статус Hysteria
systemctl status hysteria-manager   # Статус веб-панели
systemctl restart hysteria-server   # Перезапуск Hysteria
journalctl -u hysteria-server -n 50 # Последние 50 логов
```

### Управление пользователями
```bash
# Через веб-панель (скрытый путь):
# https://hist.yupiterpro.ru/44169d2dba4d0fd5/
# Пароль: _wk28wOuAf8

# Через CLI:
/opt/hysteria-manager/hysteria-users.sh list
/opt/hysteria-manager/hysteria-users.sh add username
/opt/hysteria-manager/hysteria-users.sh delete username
```

### Проверка работы
```bash
# Проверка через каскад (SOCKS5)
curl --socks5-hostname cascade:d17ed2425d8b1c37b5ee00ed4e28cd0b@193.164.155.153:18443 https://api.ipify.org

# Проверка напрямую
curl https://api.ipify.org
```

## 🌐 Схема работы

```
Клиент (hysteria2://...) 
    → Сервер 62.113.105.38:443 (Hysteria)
        → ACL проверка:
            ├── Российские сайты → напрямую (direct)
            └── Иностранные сайты → SOCKS5 каскад (193.164.155.153:18443)
                                    → Финляндия, Хельсинки
```

## ⚠️ Важно

1. **SSL-сертификаты** не включены в бэкап — их нужно перевыпустить через certbot
2. **Пароль auth** (`auth_password`) используется для HTTP-авторизации Hysteria
3. **Пароль админа** (`admin_password`) — для входа в веб-панель
4. **Каскадный SOCKS5** (`193.164.155.153:18443`) — credentials: `cascade` / `d17ed2425d8b1c37b5ee00ed4e28cd0b`
5. **DNS резолвер** — Яндекс DNS (`77.88.8.8`)
