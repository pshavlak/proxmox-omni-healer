#!/usr/bin/env python3
import bcrypt, sqlite3, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))
conn = sqlite3.connect('zolotarevka.db')
pw_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode()
conn.execute('INSERT OR IGNORE INTO users (username, password_hash, role) VALUES (?, ?, ?)',
             ('admin', pw_hash, 'admin'))
conn.commit()
user = conn.execute('SELECT id, username, role FROM users').fetchone()
conn.close()
if user:
    print(f'OK: id={user[0]}, username={user[1]}, role={user[2]}')
else:
    print('User already exists')
