#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
import json
import os
import secrets
from functools import wraps
import logging

# Включаем логирование
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

ADMIN_PASSWORD_FILE = '/etc/hysteria/admin_password.txt'
USERS_FILE = '/etc/hysteria/users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def generate_password():
    return secrets.token_urlsafe(16)

def get_admin_password():
    if os.path.exists(ADMIN_PASSWORD_FILE):
        with open(ADMIN_PASSWORD_FILE, 'r') as f:
            return f.read().strip()
    return ''

@app.route('/auth', methods=['POST'])
def auth():
    data = request.get_json()
    app.logger.debug(f"AUTH REQUEST: {data}")
    if not data:
        app.logger.warning("AUTH: No data received")
        return jsonify({'ok': False}), 401
    password = data.get('auth', '')
    app.logger.info(f"AUTH: Received password: {password}")
    users = load_users()
    app.logger.debug(f"AUTH: Users in DB: {list(users.keys())}")
    for user, pwd in users.items():
        if pwd == password:
            app.logger.info(f"AUTH: Success for user {user}")
            return jsonify({'ok': True}), 200
    app.logger.warning(f"AUTH: Failed - password not found in DB")
    return jsonify({'ok': False}), 401

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Hysteria 2 Manager</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
        h1 { color: #1a1a2e; margin-bottom: 10px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; }
        .header h1 { margin: 0; color: white; }
        .header p { margin: 5px 0 0; opacity: 0.9; }
        .card { background: white; border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .card h2 { margin: 0 0 15px; color: #333; font-size: 18px; }
        .form-row { display: flex; gap: 10px; margin-bottom: 15px; }
        input[type="text"], input[type="password"] { flex: 1; padding: 12px; border: 2px solid #e0e0e0; border-radius: 8px; font-size: 14px; }
        input:focus { outline: none; border-color: #667eea; }
        .btn { padding: 12px 24px; border: none; border-radius: 8px; cursor: pointer; font-weight: 600; transition: all 0.2s; }
        .btn-primary { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(102,126,234,0.4); }
        .btn-danger { background: #ff4757; color: white; }
        .btn-danger:hover { background: #ff3344; }
        .btn-copy { background: #2ed573; color: white; padding: 6px 12px; font-size: 12px; }
        .user-list { list-style: none; padding: 0; }
        .user-item { display: flex; justify-content: space-between; align-items: center; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; margin-bottom: 10px; }
        .user-info { flex: 1; }
        .user-name { font-weight: 600; color: #333; }
        .user-password { font-family: monospace; background: #f5f5f5; padding: 4px 8px; border-radius: 4px; font-size: 13px; color: #667eea; }
        .user-actions { display: flex; gap: 8px; }
        .flash { padding: 12px 16px; border-radius: 8px; margin-bottom: 15px; }
        .flash-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .flash-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .config-box { background: #1e1e1e; color: #00ff00; padding: 15px; border-radius: 8px; font-family: "Consolas", monospace; font-size: 12px; overflow-x: auto; }
        .login-form { max-width: 400px; margin: 100px auto; }
        .tag { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: 600; margin-left: 10px; }
        .tag-active { background: #2ed573; color: white; }
    </style>
</head>
<body>
    {% if not logged_in %}
    <div class="card login-form">
        <h2 style="text-align:center;">🔐 Вход в панель управления</h2>
        {% with messages = get_flashed_messages(with_categories=true) %}
          {% for category, message in messages %}
            <div class="flash flash-{{ category }}">{{ message }}</div>
          {% endfor %}
        {% endwith %}
        <form method="POST" action="/login">
            <input type="password" name="password" placeholder="Введите пароль администратора" required>
            <button type="submit" class="btn btn-primary" style="width:100%; margin-top:10px;">Войти</button>
        </form>
    </div>
    {% else %}
    <div class="header">
        <h1>🚀 Hysteria 2 Manager</h1>
        <p>Управление пользователями VPN</p>
    </div>
    
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% for category, message in messages %}
        <div class="flash flash-{{ category }}">{{ message }}</div>
      {% endfor %}
    {% endwith %}
    
    <div class="card">
        <h2>➕ Добавить пользователя</h2>
        <form method="POST" action="/add" class="form-row">
            <input type="text" name="username" placeholder="Имя пользователя (например, user1)" required>
            <button type="submit" class="btn btn-primary">Добавить</button>
        </form>
    </div>
    
    <div class="card">
        <h2>👥 Пользователи <span class="tag tag-active">{{ users|length }}</span></h2>
        {% if users %}
        <ul class="user-list">
        {% for username, password in users.items() %}
            <li class="user-item">
                <div class="user-info">
                    <div class="user-name">👤 {{ username }}</div>
                    <div style="margin-top:8px;">
                        <span style="font-size:12px; color:#666;">Пароль:</span>
                        <span class="user-password" id="pwd-{{ username }}">{{ password }}</span>
                    </div>
                </div>
                <div class="user-actions">
                    <button class="btn btn-copy" onclick="copyConfig('{{ username }}', '{{ password }}')">📋 Копировать конфиг</button>
                    <form method="POST" action="/delete/{{ username }}" style="display:inline;" onsubmit="return confirm('Удалить пользователя {{ username }}?')">
                        <button type="submit" class="btn btn-danger">🗑️</button>
                    </form>
                </div>
            </li>
        {% endfor %}
        </ul>
        {% else %}
        <p style="color:#666; text-align:center; padding:20px;">Нет пользователей. Добавьте первого!</p>
        {% endif %}
    </div>
    
    <div class="card">
        <h2>📋 Информация</h2>
        <p><strong>Сервер:</strong> hist.yupiterpro.ru:443</p>
        <p><strong>Протокол:</strong> Hysteria 2 (QUIC)</p>
        <p><strong>Панель:</strong> <a href="/logout" style="color:#667eea;">Выйти</a></p>
    </div>
    
    <div id="config-modal" style="display:none; position:fixed; top:0; left:0; right:0; bottom:0; background:rgba(0,0,0,0.5); z-index:1000;">
        <div style="max-width:600px; margin:50px auto; background:white; border-radius:12px; padding:20px;">
            <h3 style="margin-top:0;">📱 Конфигурация для клиента</h3>
            <div class="config-box" id="config-content"></div>
            <button class="btn btn-primary" onclick="document.getElementById('config-modal').style.display='none'" style="margin-top:15px;">Закрыть</button>
        </div>
    </div>
    
    <script>
    function copyConfig(username, password) {
        const config = `{
  "server": "hist.yupiterpro.ru:443",
  "auth": "${password}",
  "tls": {
    "sni": "hist.yupiterpro.ru"
  }
}`;
        const uri = `hysteria2://${password}@hist.yupiterpro.ru:443?insecure=0&sni=hist.yupiterpro.ru`;
        const full = config + '\\n\\nURI для импорта:\\n' + uri;
        document.getElementById('config-content').textContent = full;
        document.getElementById('config-modal').style.display = 'block';
        navigator.clipboard.writeText(full);
    }
    </script>
    {% endif %}
</body>
</html>
'''

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
