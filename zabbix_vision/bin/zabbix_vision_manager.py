"""Admin-only Splunk REST management endpoint; caller's session is always used."""
import json
import logging
import os
import sys
from pathlib import Path
import time
sys.path.insert(0, str(Path(__file__).resolve().parent))
from splunk.persistconn.application import PersistentServerConnectionApplication
from zabbix_vision_lib.client import Client, APIError
from zabbix_vision_lib.config import boolean, identifier, ids, validate_profile, validate_input, STREAMS
from zabbix_vision_lib.splunk_store import Store, StoreError, ROOT


def audit(actor, profile, scriptid, hostid, status, request_id):
    path = Path(os.environ["SPLUNK_HOME"]) / "var" / "log" / "splunk" / "zabbix_vision_actions.log"
    # Fail before execution if the audit trail cannot be written.
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"event_time": time.time(), "dataset": "execution", "user": actor,
                            "instance": profile, "scriptid": scriptid, "hostid": hostid,
                            "status": status, "request_id": request_id}) + "\n")
        f.flush()
        os.fsync(f.fileno())


class Manager(PersistentServerConnectionApplication):
    def __init__(self, command_line=None, command_arg=None):
        super().__init__()

    def handle(self, raw):
        try:
            request = json.loads(raw)
            session_key = request.get("session", {}).get("authtoken")
            if not session_key:
                return self.reply(401, {"error": "Authenticated user session required"})
            store = Store(session_key)
            actor = store.require_capability("admin_all_objects")
            if request["method"] == "GET":
                return self.reply(200, {"profiles": store.profiles(), "streams": STREAMS})
            if request["method"] != "POST":
                return self.reply(405, {"error": "Use GET or POST"})
            body = json.loads(request.get("payload") or "{}")
            action = body.get("action")
            name = identifier(body.get("name", ""))
            if action == "save":
                settings = validate_profile(body.get("settings", {}))
                token = body.get("token")
                cipher = None
                # New profiles need a token; edits can retain the existing credential.
                if token:
                    cipher = store.save_secret(name, token)
                else:
                    store.secret(name)
                if body.get("key_password"):
                    store.save_secret(name, body["key_password"], "key_password")
                store.save_profile(name, settings)
                # Mark first-run setup complete only after a profile was saved.
                store.call(ROOT + "/configs/conf-app/install", "POST", {"is_configured": "1"})
                store.call("/services/apps/local/zabbix_vision", "POST", {"configured": "1"})
                return self.reply(200, {"saved": name, "cipher": cipher})
            if action == "input":
                options = validate_input(body.get("settings", {}))
                store.profile(options["profile"])
                disabled = options.pop("disabled")
                path = ROOT + "/data/inputs/zabbix_vision/" + name
                if store.call(path, missing_ok=True) is None:
                    store.call(ROOT + "/data/inputs/zabbix_vision", "POST", dict(options, name=name))
                else:
                    store.call(path, "POST", options)
                store.call(path + ("/disable" if disabled == "1" else "/enable"), "POST")
                return self.reply(200, {"saved_input": name})
            profile = store.profile(name)
            client = Client(profile, store.secret(name), store.secret(name, "key_password", optional=True))
            version = client.discover()
            if action == "test":
                result = {}
                for label, method, params in (("hosts", "host.get", {"output": ["hostid"], "limit": 1}),
                                               ("audit", "auditlog.get", {"output": ["auditid"], "limit": 1})):
                    try:
                        client.call(method, params)
                        result[label] = "accessible"
                    except APIError as exc:
                        result[label] = str(exc)
                return self.reply(200, {"version": version, "endpoint": profile["url"], "checks": result})
            if action == "execute":
                store.require_capability("zabbix_execute_scripts")
                scriptid, hostid = str(body.get("scriptid", "")), str(body.get("hostid", ""))
                if not boolean(profile["enable_execution"]) or scriptid not in ids(profile["allowed_script_ids"]) or hostid not in ids(profile["allowed_host_ids"]):
                    return self.reply(403, {"error": "Execution disabled or script/host outside configured allowlists"})
                if body.get("confirmation") != "EXECUTE":
                    return self.reply(400, {"error": "Explicit EXECUTE confirmation required"})
                import uuid
                request_id = str(uuid.uuid4())
                audit(actor, name, scriptid, hostid, "requested", request_id)
                try:
                    result = client.call("script.execute", {"scriptid": scriptid, "hostid": hostid}, retry=False)
                except APIError:
                    audit(actor, name, scriptid, hostid, "failed_or_unknown", request_id)
                    raise
                audit(actor, name, scriptid, hostid, "completed", request_id)
                # Output may contain secrets: never index or return it by default.
                return self.reply(200, {"request_id": request_id, "response": result.get("response", "unknown"), "output_omitted": True})
            return self.reply(400, {"error": "Unknown action"})
        except (ValueError, APIError, StoreError) as exc:
            return self.reply(400, {"error": str(exc)})
        except Exception:
            return self.reply(500, {"error": "Management operation failed; verify Splunk configuration and service permissions"})

    @staticmethod
    def reply(status, data):
        return {"status": status, "payload": json.dumps(data),
                "headers": {"Content-Type": "application/json", "Cache-Control": "no-store"}}
