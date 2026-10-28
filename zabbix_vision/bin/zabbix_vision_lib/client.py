"""Version-aware JSON-RPC transport. Never log request bodies or server error text."""
import json
import random
import re
import ssl
import time
import urllib.error
import urllib.request
from .config import boolean, validate_profile, ConfigError


class APIError(RuntimeError):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise APIError("Redirect refused: configure the final API URL explicitly")


def tls_context(p, key_password=None):
    ctx = ssl.create_default_context(cafile=p["ca_bundle"] or None)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3 if p["tls_min"] == "1.3" else ssl.TLSVersion.TLSv1_2
    if not boolean(p["verify_tls"]):
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    if p["client_cert"]:
        ctx.load_cert_chain(p["client_cert"], p["client_key"], password=key_password)
    return ctx


class Client:
    def __init__(self, profile, token, key_password=None, opener=None, sleep=time.sleep):
        self.profile = validate_profile(profile)
        if not token or any(c in token for c in "\r\n"):
            raise ConfigError("A nonempty API token without newlines is required")
        self._token = token
        self.version = None
        self.version_text = "unknown"
        self._serial = 0
        self.sleep = sleep
        if opener is None:
            proxy = self.profile["proxy_url"]
            # Disable inherited OS/environment proxies unless explicitly configured.
            self.opener = urllib.request.build_opener(
                urllib.request.ProxyHandler({"http": proxy, "https": proxy} if proxy else {}),
                urllib.request.HTTPSHandler(context=tls_context(self.profile, key_password)), NoRedirect())
        else:
            self.opener = opener

    def discover(self):
        version = self.call("apiinfo.version", {}, authenticated=False)
        m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:[a-zA-Z0-9.+_-]*)", str(version))
        if not m:
            raise APIError("Invalid API version response; verify the frontend path")
        self.version = tuple(int(v) for v in m.groups())
        self.version_text = str(version)
        if self.version < (6, 0, 0):
            raise APIError("This app requires Zabbix 6.0 or later")
        if self.profile["auth_mode"] == "body" and self.version >= (7, 2, 0):
            raise ConfigError("JSON-body authentication is unavailable on Zabbix 7.2+")
        return self.version_text

    def call(self, method, params, authenticated=True, retry=True):
        if authenticated and self.version is None:
            self.discover()
        self._serial += 1
        payload = {"jsonrpc": "2.0", "id": self._serial, "method": method, "params": params}
        headers = {"Content-Type": "application/json-rpc", "Accept": "application/json"}
        if authenticated:
            mode = self.profile["auth_mode"]
            if mode == "body" or (mode == "auto" and self.version < (6, 4, 0)):
                payload["auth"] = self._token
            else:
                headers["Authorization"] = "Bearer " + self._token
        request = urllib.request.Request(self.profile["url"], json.dumps(payload).encode(), headers, method="POST")
        attempts = int(self.profile["retries"]) + 1 if retry else 1
        cap = int(self.profile["max_response_mb"]) * 1024 * 1024
        for attempt in range(attempts):
            try:
                with self.opener.open(request, timeout=int(self.profile["timeout"])) as response:
                    raw = response.read(cap + 1)
                if len(raw) > cap:
                    raise APIError("Response exceeds max_response_mb; reduce collection scope")
                try:
                    result = json.loads(raw)
                except (ValueError, UnicodeError):
                    raise APIError("Endpoint returned non-JSON data; check API URL and reverse proxy")
                if not isinstance(result, dict) or result.get("id") != self._serial or result.get("jsonrpc") != "2.0":
                    raise APIError("Invalid JSON-RPC response envelope")
                if "error" in result:
                    code = result["error"].get("code") if isinstance(result["error"], dict) else None
                    raise APIError("Zabbix rejected %s (code %s); check API role, token, method support and parameters" % (method, code), code)
                if "result" not in result:
                    raise APIError("JSON-RPC response has no result")
                return result["result"]
            except urllib.error.HTTPError as exc:
                status = exc.code
                retry_after = exc.headers.get("Retry-After", "") if exc.headers else ""
                exc.close()
                if status not in (429, 502, 503, 504) or attempt + 1 == attempts:
                    raise APIError("API HTTP status %s; check endpoint, proxy and authentication forwarding" % status)
                wait = min(30, int(retry_after)) if retry_after.isdigit() else min(30, 2 ** attempt + random.random())
                self.sleep(wait)
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt + 1 == attempts:
                    raise APIError("API connection failed; check network, timeout, CA trust, hostname and client certificate")
                self.sleep(min(30, 2 ** attempt + random.random()))
        raise APIError("API request failed")
