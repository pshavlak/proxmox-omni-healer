import hmac
import hashlib
import urllib.parse
import json

def parse_and_verify_init_data(init_data: str, bot_token: str) -> dict:
    """
    Validates Telegram WebApp initData query string.
    Returns parsed user dict if valid, raises ValueError if invalid signature or missing hash.
    """
    if not init_data:
        raise ValueError("Empty initData")

    parsed = urllib.parse.parse_qs(init_data, keep_blank_values=True)
    params = {k: v[0] for k, v in parsed.items()}

    received_hash = params.pop("hash", None)
    if not received_hash:
        raise ValueError("Missing hash in initData")

    # Data check string is constructed by sorting keys alphabetically
    data_check_list = [f"{k}={params[k]}" for k in sorted(params.keys())]
    data_check_string = "\n".join(data_check_list)

    # Secret key calculation
    secret_key = hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid initData signature")

    user_data = params.get("user")
    if user_data:
        return json.loads(user_data)
    return params
