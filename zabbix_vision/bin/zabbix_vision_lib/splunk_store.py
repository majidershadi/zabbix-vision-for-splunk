"""Splunk owns secret encryption: $8$ on 10.6+, $7$ on earlier versions."""
import json
import re
from urllib.parse import quote
from .config import PROFILE_DEFAULTS, identifier, validate_profile

APP = "zabbix_vision"
ROOT = "/servicesNS/nobody/" + APP


class StoreError(RuntimeError):
    pass


class Store:
    def __init__(self, session_key, request=None):
        self.session_key = session_key
        if request is None:
            from splunk.rest import simpleRequest
            request = simpleRequest
        self.request = request

    def call(self, path, method="GET", data=None, missing_ok=False):
        try:
            response, body = self.request(path, sessionKey=self.session_key, method=method,
                                         getargs={"output_mode": "json", "count": "0"}, postargs=data,
                                         raiseAllErrors=False, rawResult=True)
        except Exception as exc:
            raise StoreError("Splunk management request failed (%s)" % type(exc).__name__)
        status = int(response.status) if hasattr(response, "status") else int(response["status"])
        if missing_ok and status == 404:
            return None
        if status >= 400:
            raise StoreError("Splunk management request rejected (HTTP %s); check capabilities" % status)
        try:
            return json.loads(body)
        except (ValueError, TypeError):
            raise StoreError("Invalid Splunk management response")

    def profile(self, name):
        result = self.call(ROOT + "/configs/conf-zabbix_vision_connections/" + quote(identifier(name), safe=""))
        content = result["entry"][0]["content"]
        return validate_profile({k: content[k] for k in PROFILE_DEFAULTS if k in content})

    def profiles(self):
        result = self.call(ROOT + "/configs/conf-zabbix_vision_connections", missing_ok=True)
        return [{"name": e["name"], "settings": validate_profile({k: e["content"].get(k, v) for k, v in PROFILE_DEFAULTS.items()})}
                for e in (result or {}).get("entry", []) if e["name"] != "default"]

    def save_profile(self, name, settings):
        identifier(name)
        settings = validate_profile(settings)
        path = ROOT + "/configs/conf-zabbix_vision_connections/" + quote(name, safe="")
        if self.call(path, missing_ok=True) is None:
            return self.call(ROOT + "/configs/conf-zabbix_vision_connections", "POST", dict(settings, name=name))
        return self.call(path, "POST", settings)

    def credential_path(self, name, kind="token"):
        identifier(name)
        if kind not in ("token", "key_password"):
            raise StoreError("Unknown credential kind")
        return ROOT + "/storage/passwords/" + quote("zabbix_vision_" + name + ":" + kind + ":", safe="")

    def secret(self, name, kind="token", optional=False):
        result = self.call(self.credential_path(name, kind), missing_ok=optional)
        return None if result is None else result["entry"][0]["content"]["clear_password"]

    def save_secret(self, name, secret, kind="token"):
        if not isinstance(secret, str) or not secret or len(secret) > 16384 or "\n" in secret or "\r" in secret:
            raise StoreError("Invalid secret")
        path = self.credential_path(name, kind)
        existing = self.call(path, missing_ok=True)
        if existing is None:
            self.call(ROOT + "/storage/passwords", "POST", {"name": kind, "realm": "zabbix_vision_" + name, "password": secret})
        else:
            self.call(path, "POST", {"password": secret})
        # Inspect only the prefix. Never expose encrypted or clear credential material.
        record = self.call(path)["entry"][0]["content"]
        encrypted = record.get("encr_password", "")
        observed = "$8$" if encrypted.startswith("$8$") else "$7$" if encrypted.startswith("$7$") else "unavailable"
        version = self.call("/services/server/info")["entry"][0]["content"].get("version", "")
        match = re.match(r"(\d+)\.(\d+)", version)
        expected = "$8$" if match and tuple(map(int, match.groups())) >= (10, 6) else "$7$"
        if observed != "unavailable" and observed != expected:
            raise StoreError("Secret was saved, but its cipher prefix differs from the installed Splunk version; investigate server configuration")
        return {"expected_cipher": expected, "observed_cipher": observed}

    def require_capability(self, capability):
        context = self.call("/services/authentication/current-context")["entry"][0]["content"]
        if capability not in context.get("capabilities", []):
            raise StoreError("Required capability: " + capability)
        return context.get("username", "unknown")
