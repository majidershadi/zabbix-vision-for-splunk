"""Shared validation for setup, input validation, and runtime."""
import re
from urllib.parse import urlsplit, urlunsplit


class ConfigError(ValueError):
    pass


def boolean(value):
    if str(value).lower() in ("true", "1", "yes"):
        return True
    if str(value).lower() in ("false", "0", "no", ""):
        return False
    raise ConfigError("Expected a boolean")


def identifier(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", str(value)):
        raise ConfigError("Names must contain 1–80 letters, digits, underscores or hyphens")
    return str(value)


def ids(value):
    values = [v.strip() for v in str(value or "").split(",") if v.strip()]
    if any(not v.isdigit() or int(v) <= 0 for v in values):
        raise ConfigError("IDs must be positive integers separated by commas")
    return values


def endpoint(value, allow_http=False):
    u = urlsplit(str(value).strip())
    if u.scheme not in ("https", "http") or not u.hostname:
        raise ConfigError("URL must be an absolute HTTP(S) frontend or API URL")
    if u.scheme == "http" and not allow_http:
        raise ConfigError("HTTP requires explicit allow_http for an isolated lab")
    if u.username or u.password or u.query or u.fragment:
        raise ConfigError("URL must not contain credentials, a query, or a fragment")
    if any(c.isspace() or ord(c) < 32 for c in value):
        raise ConfigError("URL contains whitespace or control characters")
    try:
        u.port
    except ValueError:
        raise ConfigError("Invalid URL port")
    path = u.path.rstrip("/")
    if not path.endswith("/api_jsonrpc.php"):
        path += "/api_jsonrpc.php"
    return urlunsplit((u.scheme, u.netloc, path, "", ""))


PROFILE_DEFAULTS = {
    "url": "", "verify_tls": "true", "allow_http": "false", "ca_bundle": "",
    "client_cert": "", "client_key": "", "tls_min": "1.2", "proxy_url": "",
    "timeout": "30", "retries": "3", "max_response_mb": "32",
    "auth_mode": "auto", "enable_execution": "false", "allowed_script_ids": "",
    "allowed_host_ids": "",
}


def validate_profile(raw):
    unknown = set(raw) - set(PROFILE_DEFAULTS)
    if unknown:
        raise ConfigError("Unknown connection option: " + ", ".join(sorted(unknown)))
    p = dict(PROFILE_DEFAULTS, **raw)
    for key in ("verify_tls", "allow_http", "enable_execution"):
        p[key] = "true" if boolean(p[key]) else "false"
    p["url"] = endpoint(p["url"], boolean(p["allow_http"]))
    for key, low, high in (("timeout", 1, 300), ("retries", 0, 5), ("max_response_mb", 1, 256)):
        try:
            number = int(p[key])
        except (ValueError, TypeError):
            raise ConfigError(key + " must be an integer")
        if not low <= number <= high:
            raise ConfigError("%s must be between %s and %s" % (key, low, high))
        p[key] = str(number)
    if p["tls_min"] not in ("1.2", "1.3"):
        raise ConfigError("tls_min must be 1.2 or 1.3")
    if p["auth_mode"] not in ("auto", "bearer", "body"):
        raise ConfigError("auth_mode must be auto, bearer or body")
    if bool(p["client_cert"]) != bool(p["client_key"]):
        raise ConfigError("Provide both client certificate and private key paths")
    if p["proxy_url"]:
        u = urlsplit(p["proxy_url"])
        if u.scheme != "http" or not u.hostname or u.username or u.password or u.query or u.fragment or u.path not in ("", "/"):
            raise ConfigError("Proxy must be an HTTP CONNECT proxy URL without embedded credentials")
        try:
            u.port
        except ValueError:
            raise ConfigError("Invalid proxy port")
    for k in ("allowed_script_ids", "allowed_host_ids"):
        ids(p[k])
    if boolean(p["enable_execution"]) and not all(ids(p[k]) for k in ("allowed_script_ids", "allowed_host_ids")):
        raise ConfigError("Execution requires explicit script and host allowlists")
    return p


STREAMS = ("audit", "events", "problems", "hosts", "items", "triggers", "hostgroups",
           "templates", "proxies", "services", "sla", "maintenance", "alerts",
           "history", "trends", "discovery", "autoregistration", "internal")
INPUT_DEFAULTS = {
    "profile": "", "streams": "audit,events,problems,hosts", "interval": "60",
    "index": "main", "page_size": "1000", "lookback": "3600", "overlap": "120",
    "settle_delay": "10", "window": "3600", "item_ids": "", "history_types": "0,1,2,3,4",
    "snapshot_limit": "100000", "disabled": "0",
}


def validate_input(raw):
    p = dict(INPUT_DEFAULTS, **{k: v for k, v in raw.items() if k in INPUT_DEFAULTS})
    identifier(p["profile"])
    identifier(p["index"])
    streams = [s.strip() for s in p["streams"].split(",") if s.strip()]
    if not streams or set(streams) - set(STREAMS) or len(streams) != len(set(streams)):
        raise ConfigError("Select unique supported streams")
    p["streams"] = ",".join(streams)
    for key, low, high in (("interval", 10, 86400), ("page_size", 2, 100000), ("lookback", 1, 31536000),
                          ("overlap", 0, 86400), ("settle_delay", 1, 3600), ("window", 1, 86400),
                          ("snapshot_limit", 2, 1000000)):
        try:
            number = int(p[key])
        except (ValueError, TypeError):
            raise ConfigError(key + " must be an integer")
        if not low <= number <= high:
            raise ConfigError("%s must be between %s and %s" % (key, low, high))
        p[key] = str(number)
    ids(p["item_ids"])
    if set(streams) & {"history", "trends"} and not ids(p["item_ids"]):
        raise ConfigError("History and trends require an explicit item_ids scope")
    types = p["history_types"].split(",")
    if not types or any(t not in ("0", "1", "2", "3", "4", "5") for t in types):
        raise ConfigError("history_types must be comma-separated types 0–5")
    p["disabled"] = "1" if boolean(p["disabled"]) else "0"
    return p
