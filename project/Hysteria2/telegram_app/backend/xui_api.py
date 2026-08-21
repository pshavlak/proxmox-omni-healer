import json
import os
import ssl
import time
import urllib.parse
import urllib.request
import uuid
import re
from http.cookiejar import CookieJar


class XUIConfigError(Exception):
    pass


class XUIAPIError(Exception):
    pass


def normalize_base_url(value):
    value = (value or "").strip().rstrip("/")
    if not value:
        raise XUIConfigError("xui_api_not_configured")
    return value


def xui_config_from_env():
    return {
        "base_url": normalize_base_url(os.environ.get("XUI_API_BASE_URL", "")),
        "username": os.environ.get("XUI_USERNAME", "").strip(),
        "password": os.environ.get("XUI_PASSWORD", "").strip(),
        "managed_inbound_id": int(os.environ.get("XUI_MANAGED_INBOUND_ID", "0") or 0),
        "managed_tcp_inbound_id": int(os.environ.get("XUI_MANAGED_TCP_INBOUND_ID", "0") or 0),
        "managed_xhttp_inbound_id": int(os.environ.get("XUI_MANAGED_XHTTP_INBOUND_ID", "0") or 0),
        "managed_hysteria_inbound_id": int(os.environ.get("XUI_MANAGED_HYSTERIA_INBOUND_ID", "0") or 0),
        "public_host": os.environ.get("XUI_PUBLIC_HOST", "193.164.155.153").strip(),
    }


def require_config(config):
    if not config.get("username") or not config.get("password"):
        raise XUIConfigError("xui_credentials_not_configured")
    if not (
        config.get("managed_inbound_id")
        or config.get("managed_tcp_inbound_id")
        or config.get("managed_xhttp_inbound_id")
        or config.get("managed_hysteria_inbound_id")
    ):
        raise XUIConfigError("xui_managed_inbound_not_configured")
    if not config.get("public_host"):
        raise XUIConfigError("xui_public_host_not_configured")


def build_client_payload(email, expiry_time_seconds=0, total_gb=0, client_uuid=None):
    email = (email or "").strip()
    if not email:
        raise ValueError("empty_xui_email")
    expiry_ms = int(expiry_time_seconds or 0)
    if expiry_ms and expiry_ms < 10_000_000_000:
        expiry_ms *= 1000
    return {
        "id": client_uuid or str(uuid.uuid4()),
        "email": email,
        "enable": True,
        "expiryTime": expiry_ms,
        "flow": "xtls-rprx-vision",
        "limitIp": 0,
        "subId": "",
        "tgId": "",
        "totalGB": int(total_gb or 0),
        "reset": 0,
    }


def transport_email(display_name, transport="tcp"):
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", (display_name or "").strip()).strip("._-")
    if not base:
        base = "miniapp"
    transport = (transport or "").lower()
    if transport == "xhttp":
        suffix = "__xhttp"
    elif transport == "hysteria":
        suffix = "__hysteria"
    else:
        suffix = "__tcp"
    max_base_len = 64 - len(suffix)
    return f"{base[:max_base_len]}{suffix}"


def add_client_request_body(inbound_id, client):
    return {
        "id": int(inbound_id),
        "settings": json.dumps({"clients": [client]}, separators=(",", ":")),
    }


def vless_client_uuid(uri):
    uri = (uri or "").strip()
    if not uri.startswith("vless://"):
        return ""
    return uri[len("vless://"):].split("@", 1)[0].strip()


def _as_dict(value):
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip():
        return json.loads(value)
    return {}


def build_vless_uri(inbound, client, public_host, label=None):
    stream = _as_dict(inbound.get("streamSettings") or inbound.get("stream_settings"))
    reality = stream.get("realitySettings") or {}
    reality_settings = reality.get("settings") or {}
    public_key = reality_settings.get("publicKey")
    if not public_key:
        raise XUIAPIError("xui_reality_public_key_missing")
    server_names = reality.get("serverNames") or []
    sni = reality_settings.get("serverName") or (server_names[0] if server_names else "")
    short_ids = reality.get("shortIds") or [""]
    query = {
        "type": stream.get("network") or "tcp",
        "security": stream.get("security") or "reality",
        "pbk": public_key,
        "fp": reality_settings.get("fingerprint") or "chrome",
        "sni": sni,
        "sid": short_ids[0] if short_ids else "",
        "spx": reality_settings.get("spiderX") or "/",
    }
    if client.get("flow"):
        query["flow"] = client["flow"]
    port = int(inbound.get("port") or 443)
    tag = urllib.parse.quote(label or client["email"])
    return (
        f"vless://{client['id']}@{public_host}:{port}?"
        f"{urllib.parse.urlencode(query, safe=':/')}"
        f"#{tag}"
    )


def build_hysteria_client_payload(email, auth_secret, expiry_time_seconds=0, total_gb=0):
    email = (email or "").strip()
    auth_secret = (auth_secret or "").strip()
    if not email:
        raise ValueError("empty_xui_email")
    if not auth_secret:
        raise ValueError("empty_hysteria_auth")
    expiry_ms = int(expiry_time_seconds or 0)
    if expiry_ms and expiry_ms < 10_000_000_000:
        expiry_ms *= 1000
    return {
        "auth": auth_secret,
        "email": email,
        "enable": True,
        "expiryTime": expiry_ms,
        "limitIp": 0,
        "reset": 0,
        "subId": "",
        "tgId": "",
        "totalGB": int(total_gb or 0),
    }


def build_hysteria_uri(inbound, client, public_host, label=None):
    stream = _as_dict(inbound.get("streamSettings") or inbound.get("stream_settings"))
    tls = stream.get("tlsSettings") or {}
    tls_settings = tls.get("settings") or {}
    settings = _as_dict(inbound.get("settings"))
    protocol = "hysteria2" if int(settings.get("version") or 2) == 2 else "hysteria"
    query = {"security": "tls"}
    if tls.get("alpn"):
        query["alpn"] = ",".join(tls.get("alpn") or [])
    if tls_settings.get("allowInsecure"):
        query["insecure"] = "1"
    if tls_settings.get("fingerprint"):
        query["fp"] = tls_settings["fingerprint"]
    if tls.get("serverName"):
        query["sni"] = tls["serverName"]
    port = int(inbound.get("port") or 443)
    tag = urllib.parse.quote(label or client["email"])
    return (
        f"{protocol}://{client['auth']}@{public_host}:{port}?"
        f"{urllib.parse.urlencode(query, safe=',')}"
        f"#{tag}"
    )


class XUIClient:
    def __init__(self, config=None):
        self.config = config or xui_config_from_env()
        require_config(self.config)
        self.cookies = CookieJar()
        self.ssl_context = ssl._create_unverified_context()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookies),
            urllib.request.HTTPSHandler(context=self.ssl_context),
        )

    def _url(self, path):
        return self.config["base_url"] + "/" + path.lstrip("/")

    def request_json(self, method, path, body=None):
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self._url(path), data=data, headers=headers, method=method)
        try:
            with self.opener.open(req, timeout=12) as resp:
                raw = resp.read().decode("utf-8")
        except Exception as e:
            raise XUIAPIError("xui_api_request_failed") from e
        if not raw.strip():
            raise XUIAPIError("xui_api_empty_response")
        try:
            return json.loads(raw)
        except Exception as e:
            raise XUIAPIError("xui_api_invalid_json") from e

    def login(self):
        data = self.request_json("POST", "login", {
            "username": self.config["username"],
            "password": self.config["password"],
        })
        if not data.get("success"):
            raise XUIAPIError("xui_login_failed")

    def get_inbound(self, inbound_id):
        data = self.request_json("GET", f"xui/API/inbounds/get/{int(inbound_id)}")
        if not data.get("success"):
            raise XUIAPIError("xui_get_inbound_failed")
        return data.get("obj") or {}

    def add_client(self, inbound_id, client):
        data = self.request_json("POST", "xui/API/inbounds/addClient", add_client_request_body(inbound_id, client))
        if not data.get("success"):
            raise XUIAPIError("xui_add_client_failed")
        return data

    def delete_client_by_email(self, email):
        data = self.request_json("POST", f"panel/api/clients/del/{urllib.parse.quote(email, safe='')}")
        if not data.get("success"):
            raise XUIAPIError("xui_delete_client_failed")
        return data

    def delete_client_from_inbound(self, inbound_id, client_uuid):
        client_uuid = (client_uuid or "").strip()
        if not client_uuid:
            return {"success": True, "deleted": False}
        data = self.request_json("POST", f"xui/API/inbounds/{int(inbound_id)}/delClient/{client_uuid}")
        if not data.get("success"):
            raise XUIAPIError("xui_delete_client_failed")
        return data

    def managed_inbound_id(self, transport="tcp"):
        transport = (transport or "tcp").strip().lower()
        if transport == "xhttp":
            inbound_id = self.config.get("managed_xhttp_inbound_id") or self.config.get("managed_inbound_id")
        elif transport == "hysteria":
            inbound_id = self.config.get("managed_hysteria_inbound_id") or self.config.get("managed_inbound_id")
        else:
            inbound_id = self.config.get("managed_tcp_inbound_id") or self.config.get("managed_inbound_id")
        if not inbound_id:
            raise XUIConfigError("xui_managed_inbound_not_configured")
        return inbound_id

    def find_direct_client(self, display_name, transport="tcp"):
        inbound_id = self.managed_inbound_id(transport)
        transport = (transport or "tcp").strip().lower()
        display_name = (display_name or "").strip()
        wanted = {display_name.lower(), transport_email(display_name, transport).lower()}
        inbound = self.get_inbound(inbound_id)
        settings = _as_dict(inbound.get("settings"))
        for existing in settings.get("clients") or []:
            email = (existing.get("email") or "").lower()
            if email in wanted:
                return inbound_id, existing
        return inbound_id, None

    def delete_direct_client(self, display_name, transport="tcp"):
        self.login()
        inbound_id, existing = self.find_direct_client(display_name, transport)
        if not existing:
            return {"deleted": False, "inbound_id": inbound_id}

        transport = (transport or "tcp").strip().lower()
        email = existing.get("email") or transport_email(display_name, transport)
        client_uuid = existing.get("auth") if transport == "hysteria" else existing.get("id")
        try:
            self.delete_client_by_email(email)
        except XUIAPIError:
            self.delete_client_from_inbound(inbound_id, client_uuid)

        time.sleep(0.2)
        _, check = self.find_direct_client(display_name, transport)
        if check:
            raise XUIAPIError("xui_delete_client_verify_failed")
        return {"deleted": True, "inbound_id": inbound_id, "email": email}

    def create_direct_client(self, email, expiry_time_seconds=0, total_gb=0, transport="tcp", auth_secret=None):
        inbound_id = self.managed_inbound_id(transport)
        transport = (transport or "tcp").strip().lower()
        xui_email = transport_email(email, transport)
        if transport == "xhttp":
            label = "Латвия XHTTP"
        elif transport == "hysteria":
            label = "Латвия Hysteria"
        else:
            label = "Латвия TCP"
        self.login()
        inbound = self.get_inbound(inbound_id)
        settings = _as_dict(inbound.get("settings"))
        for existing in settings.get("clients") or []:
            if (existing.get("email") or "").lower() in {email.lower(), xui_email.lower()}:
                uri = build_hysteria_uri(inbound, existing, self.config["public_host"], label=label) if transport == "hysteria" else build_vless_uri(inbound, existing, self.config["public_host"], label=label)
                return {
                    "created": False,
                    "email": xui_email,
                    "client": existing,
                    "uri": uri,
                    "inbound_id": inbound_id,
                }
        client = (
            build_hysteria_client_payload(xui_email, auth_secret or email, expiry_time_seconds, total_gb)
            if transport == "hysteria"
            else build_client_payload(xui_email, expiry_time_seconds, total_gb)
        )
        self.add_client(inbound_id, client)
        time.sleep(0.2)
        inbound = self.get_inbound(inbound_id)
        uri = build_hysteria_uri(inbound, client, self.config["public_host"], label=label) if transport == "hysteria" else build_vless_uri(inbound, client, self.config["public_host"], label=label)
        return {
            "created": True,
            "email": xui_email,
            "client": client,
            "uri": uri,
            "inbound_id": inbound_id,
        }
