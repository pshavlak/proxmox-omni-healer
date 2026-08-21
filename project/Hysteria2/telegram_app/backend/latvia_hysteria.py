import os
import urllib.parse

from .hysteria_users import validate_username
from .xui_api import XUIAPIError, XUIClient, XUIConfigError


class LatviaHysteriaError(Exception):
    pass


def is_enabled():
    return os.environ.get("LATVIA_HYSTERIA_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")


def build_hysteria_uri(auth_secret, host=None, port=None, label="Латвия Hysteria"):
    endpoint_host = host or os.environ.get("XUI_PUBLIC_HOST", "193.164.155.153").strip()
    endpoint_port = int(port or os.environ.get("XUI_HYSTERIA_PUBLIC_PORT", "55446") or 55446)
    return (
        f"hysteria2://{auth_secret}@{endpoint_host}:{endpoint_port}?"
        f"security=tls&alpn=h3#{urllib.parse.quote(label)}"
    )


def attach_user(username, auth_secret):
    if not is_enabled():
        raise LatviaHysteriaError("latvia_hysteria_not_enabled")
    username = validate_username(username)
    if not auth_secret:
        raise LatviaHysteriaError("latvia_hysteria_empty_auth")
    try:
        result = XUIClient().create_direct_client(
            username,
            transport="hysteria",
            auth_secret=auth_secret,
        )
    except (XUIAPIError, XUIConfigError) as e:
        raise LatviaHysteriaError(str(e)) from e
    return {
        "changed": bool(result.get("created")),
        "created": bool(result.get("created")),
        "inbound_id": result.get("inbound_id"),
        "email": result.get("email"),
        "uri": result["uri"],
    }


def delete_user(username):
    if not is_enabled():
        return {"deleted": False, "skipped": "latvia_hysteria_not_enabled"}
    username = validate_username(username)
    try:
        result = XUIClient().delete_direct_client(username, transport="hysteria")
    except (XUIAPIError, XUIConfigError) as e:
        raise LatviaHysteriaError(str(e)) from e
    return {
        "changed": bool(result.get("deleted")),
        "deleted": bool(result.get("deleted")),
        "inbound_id": result.get("inbound_id"),
        "email": result.get("email"),
    }
