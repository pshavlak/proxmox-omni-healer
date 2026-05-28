#!/usr/bin/env python3
"""
Hysteria 2 Manager Panel - Flask приложение для управления пользователями
Сервер: 62.113.105.38
Домен: hist.yupiterpro.ru
"""

import json
import os
import secrets
import string
from functools import wraps
from flask import Flask, render_template_string, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'hysteria-manager-secret-key-change-me'

USERS_FILE = '/etc/hysteria/users.json'
ADMIN_PASSWORD_FILE = '/etc/hysteria/admin_password.txt'
AUTH_PASSWORD_FILE = '/etc/hysteria/auth_password'

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hysteria 2 Manager</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0f0f1a;
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: #1a1a2e;
            border-radius: 16px;
            padding: 40px;
            width: 100%;
            max-width: 800px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        h1 {
            text-align: center;
            margin-bottom: 30px;
            color: #00d4aa;
            font-size: 24px;
        }
        .flash { padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .flash.success { background: #00d4aa22; border: 1px solid #00d4aa; color: #00d4aa; }
        .flash.error { background: #ff444422; border: 1px solid #ff4444; color: #ff4444; }
        .login-form { display: flex; gap: 10px; justify-content: center; margin-bottom: 20px; }
        input[type="password"], input[type="text"] {
            padding: 12px 16px;
            border: 1px solid #333;
            border-radius: 8px;
            background: #16213e;
            color: #e0e0e0;
            font-size: 14px;
            width: 250px;
        }
        input:focus { outline: none; border-color: #00d4aa; }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-primary { background: #00d4aa; color: #0f0f1a; }
        .btn-primary:hover { background: #00e6b3; transform: translateY(-1px); }
        .btn-danger { background: #ff4444; color: white; }
        .btn-danger:hover { background: #ff5555; }
        .btn-logout { background: #333; color: #e0e0e0; }
        .btn-logout:hover { background: #444; }
        .user-list { margin-top: 20px; }
        .user-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: #16213e;
            border-radius: 8px;
            margin-bottom: 8px;
        }
        .user-info { display: flex; flex-direction: column; gap: 4px; }
        .user-name { font-weight: 600; color: #00d4aa; }
        .user-password { font-size: 12px; color: #888; font-family: monospace; }
        .user-actions { display: flex; gap: 8px; }
        .add-form { display: flex; gap: 10px; margin-bottom: 20px; }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .stats { text-align: center; color: #888; font-size: 13px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Hysteria 2 Manager</h1>

        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% if not logged_in %}
        <form method="POST" action="/login" class="login-form">
            <input type="password" name="password" placeholder="Пароль администратора" required>
            <button type="submit" class="btn btn-primary">Войти</button>
        </form>
        {% else %}
        <div class="header">
            <span>👤 Администратор</span>
            <form method="POST" action="/logout" style="display:inline;">
                <button type="submit" class="btn btn-logout">Выйти</button>
            </form>
        </div>

        <div class="stats">Всего пользователей: {{ users|length }}</div>

        <form method="POST" action="/add" class="add-form">
            <input type="text" name="username" placeholder="Имя нового пользователя" required>
            <button type="submit" class="btn btn-primary">➕ Добавить</button>
        </form>

        <div class="user-list">
            {% for username, password in users.items() %}
            <div class="user-item">
                <div class="user-info">
                    <span class="user-name">{{ username }}</span>
                    <span class="user-password">hysteria2://{{ password }}@hist.yupiterpro.ru:443?insecure=0&sni=hist.yupiterpro.ru</span>
                </div>
                <div class="user-actions">
                    <form method="POST" action="/delete/{{ username }}" style="display:inline;" onsubmit="return confirm('Удалить пользователя {{ username }}?')">
                        <button type="submit" class="btn btn-danger">🗑️</button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}
    </div>
</body>
</html>
'''


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)


def get_admin_password():
    if os.path.exists(ADMIN_PASSWORD_FILE):
        with open(ADMIN_PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    return 'admin'


def generate_password(length=20):
    alphabet = string.ascii_letters + string.digits + '-_'
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def requires_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.cookies.get('admin_session'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


@app.route('/')
def index():
    logged_in = request.cookies.get('admin_session') == 'valid'
    users = load_users() if logged_in else {}
    return render_template_string(HTML_TEMPLATE, logged_in=logged_in, users=users)


@app.route('/login', methods=['POST'])
def login():
    password = request.form.get('password', '')
    admin_pwd = get_admin_password()
    if password == admin_pwd:
        resp = redirect(url_for('index'))
        resp.set_cookie('admin_session', 'valid')
        return resp
    else:
        flash('Неверный пароль', 'error')
        return redirect(url_for('index'))


@app.route('/logout')
def logout():
    resp = redirect(url_for('index'))
    resp.set_cookie('admin_session', '', expires=0)
    return resp


@app.route('/add', methods=['POST'])
@requires_login
def add_user():
    username = request.form.get('username', '').strip()
    if not username:
        flash('Введите имя пользователя', 'error')
        return redirect(url_for('index'))
    users = load_users()
    if username in users:
        flash(f'Пользователь {username} уже существует', 'error')
        return redirect(url_for('index'))
    password = generate_password()
    users[username] = password
    save_users(users)
    flash(f'Пользователь {username} добавлен', 'success')
    return redirect(url_for('index'))


@app.route('/delete/<username>', methods=['POST'])
@requires_login
def delete_user(username):
    users = load_users()
    if username in users:
        del users[username]
        save_users(users)
        flash(f'Пользователь {username} удалён', 'success')
    else:
        flash(f'Пользователь {username} не найден', 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    print(f"\n{'='*50}")
    print(f"Панель управления Hysteria 2 запущена")
    print(f"{'='*50}\n")
    app.run(host='127.0.0.1', port=8081, debug=False)
