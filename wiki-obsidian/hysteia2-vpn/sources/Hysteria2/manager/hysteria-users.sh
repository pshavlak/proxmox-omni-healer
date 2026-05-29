#!/bin/bash
# Скрипт управления пользователями Hysteria 2

USERS_FILE="/etc/hysteria/users.json"
CONFIG_FILE="/etc/hysteria/config.yaml"

init_users() {
    if [ ! -f "$USERS_FILE" ]; then
        echo "{}" > "$USERS_FILE"
    fi
}

add_user() {
    local username=$1
    local password=$(openssl rand -base64 24 | tr -d '/+=' | head -c 20)
    
    if [ -z "$username" ]; then
        echo "Ошибка: введите имя пользователя"
        exit 1
    fi
    
    init_users
    
    if grep -q "\"$username\"" "$USERS_FILE" 2>/dev/null; then
        echo "Ошибка: пользователь $username уже существует"
        exit 1
    fi
    
    # Добавляем пользователя в JSON
    local temp=$(mktemp)
    if [ "$(cat $USERS_FILE)" = "{}" ]; then
        echo "{\"$username\": \"$password\"}" > "$temp"
    else
        sed "s/}$/, \"$username\": \"$password\"}/" "$USERS_FILE" > "$temp"
    fi
    mv "$temp" "$USERS_FILE"
    
    echo "✓ Пользователь '$username' добавлен"
    echo "  Пароль: $password"
    echo "  URI: hysteria2://$password@hist.yupiterpro.ru:443?insecure=0&sni=hist.yupiterpro.ru"
}

delete_user() {
    local username=$1
    
    if [ -z "$username" ]; then
        echo "Ошибка: введите имя пользователя"
        exit 1
    fi
    
    init_users
    
    if ! grep -q "\"$username\"" "$USERS_FILE" 2>/dev/null; then
        echo "Ошибка: пользователь $username не найден"
        exit 1
    fi
    
    # Удаляем пользователя
    python3 -c "
import json
with open('$USERS_FILE', 'r') as f:
    users = json.load(f)
if '$username' in users:
    del users['$username']
with open('$USERS_FILE', 'w') as f:
    json.dump(users, f, indent=2)
"
    echo "✓ Пользователь '$username' удалён"
}

list_users() {
    init_users
    echo "=== Пользователи Hysteria 2 ==="
    python3 -c "
import json
with open('$USERS_FILE', 'r') as f:
    users = json.load(f)
for username, password in users.items():
    print(f'  {username}: {password}')
    print(f'    hysteria2://{password}@hist.yupiterpro.ru:443')
"
}

case "$1" in
    add)
        add_user "$2"
        ;;
    delete|del|rm)
        delete_user "$2"
        ;;
    list|ls)
        list_users
        ;;
    *)
        echo "Использование: $0 {add|delete|list} [username]"
        echo "  add <username>    - Добавить пользователя"
        echo "  delete <username> - Удалить пользователя"
        echo "  list              - Показать всех пользователей"
        exit 1
        ;;
esac
