import json
import os
import re
import secrets
import stat
import time
import urllib.error
import urllib.request


USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,64}$")
DEFAULT_USERS_FILE = os.environ.get("HYSTERIA_USERS_FILE", "/etc/hysteria/users.json")
DEFAULT_BACKUP_DIR = os.environ.get("HYSTERIA_USERS_BACKUP_DIR", "/root/miniapp-backups")
DEFAULT_AUTH_URL = os.environ.get("HYSTERIA_AUTH_URL", "http://127.0.0.1:8081/auth")


class HysteriaUsersError(Exception):
    pass


def validate_username(username):
    username = (username or "").strip()
    if not USERNAME_RE.match(username):
        raise HysteriaUsersError("username_must_be_3_64_latin_digits_dot_dash_underscore")
    return username


def load_users(users_file=DEFAULT_USERS_FILE):
    with open(users_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise HysteriaUsersError("users_json_must_be_object")
    return data


def _safe_mode(path):
    try:
        return stat.S_IMODE(os.stat(path).st_mode)
    except FileNotFoundError:
        return 0o600


def atomic_save_users(users, users_file=DEFAULT_USERS_FILE, backup_dir=DEFAULT_BACKUP_DIR):
    if not isinstance(users, dict):
        raise HysteriaUsersError("users_must_be_object")

    os.makedirs(backup_dir, mode=0o700, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(backup_dir, f"users-json-before-miniapp-write-{ts}.json")
    mode = _safe_mode(users_file)

    original = load_users(users_file)
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(original, f, ensure_ascii=False, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.chmod(backup_path, 0o600)

    tmp_path = f"{users_file}.miniapp-{os.getpid()}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, mode)
        with open(tmp_path, "r", encoding="utf-8") as f:
            json.load(f)
        os.replace(tmp_path, users_file)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    load_users(users_file)
    return backup_path


def create_hysteria_user(username, users_file=DEFAULT_USERS_FILE, backup_dir=DEFAULT_BACKUP_DIR):
    username = validate_username(username)
    users = load_users(users_file)
    if username in users:
        raise HysteriaUsersError("username_already_exists")

    auth_secret = secrets.token_urlsafe(24)
    users[username] = auth_secret
    backup_path = atomic_save_users(users, users_file, backup_dir)
    return {
        "username": username,
        "auth_secret": auth_secret,
        "backup_path": backup_path,
    }


def delete_hysteria_user(username, users_file=DEFAULT_USERS_FILE, backup_dir=DEFAULT_BACKUP_DIR):
    username = validate_username(username)
    users = load_users(users_file)
    if username not in users:
        return False
    users.pop(username)
    atomic_save_users(users, users_file, backup_dir)
    return True


def verify_auth(auth_secret, expected_id=None, auth_url=DEFAULT_AUTH_URL, timeout=5):
    payload = json.dumps({"auth": auth_secret}).encode("utf-8")
    req = urllib.request.Request(
        auth_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            data = json.loads(e.read().decode("utf-8"))
        except Exception:
            data = {"ok": False}
    except Exception as e:
        raise HysteriaUsersError(f"auth_check_failed:{type(e).__name__}")

    ok = bool(data.get("ok"))
    if expected_id is not None and str(data.get("id", "")) != str(expected_id):
        ok = False
    return {
        "ok": ok,
        "id": data.get("id"),
    }
