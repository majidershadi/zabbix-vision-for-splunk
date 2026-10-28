"""Stable searchable fields, original payload, and deterministic replay IDs."""
import hashlib
import json
import re

ACTIONS = {0: "add", 1: "update", 2: "delete", 4: "logout", 7: "execute", 8: "login", 9: "failed_login",
           10: "history_clear", 11: "config_refresh", 12: "push"}
RESOURCES = {0: "user", 4: "host", 5: "action", 13: "trigger", 14: "hostgroup", 15: "item",
             18: "service", 25: "script", 26: "proxy", 27: "maintenance", 29: "macro", 30: "template",
             40: "settings", 42: "authentication", 44: "role", 45: "api_token", 48: "sla",
             49: "user_directory", 54: "mfa", 55: "proxy_group"}
SEVERITIES = {0: "not_classified", 1: "information", 2: "warning", 3: "average", 4: "high", 5: "disaster"}
SENSITIVE = re.compile(r"password|passwd|token|secret|authorization|private.?key|tls_psk|community|(?:^|\.)output$", re.I)


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SENSITIVE.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


def normalize(stream, row, instance, version, collected):
    raw = dict(row)
    if stream == "audit" and isinstance(raw.get("details"), str):
        try:
            raw["details"] = json.loads(raw["details"])
        except ValueError:
            # Unparseable audit detail text cannot be safely key-redacted.
            raw["details"] = {"parse_error": True, "raw_omitted": True}
    raw = redact(raw)
    object_id = next((str(row[k]) for k in ("auditid", "eventid", "alertid", "itemid", "hostid", "triggerid",
                      "groupid", "templateid", "proxyid", "serviceid", "slaid", "maintenanceid") if k in row), "")
    timestamp = int(row.get("clock", collected))
    identity = [instance, stream, object_id]
    if stream in ("history", "trends"):
        identity += [row.get("clock"), row.get("ns", 0), row.get("value_type")]
    elif stream not in ("audit", "events", "alerts", "discovery", "autoregistration", "internal"):
        identity += [collected, row]
    event = {"schema_version": 1, "instance": instance, "dataset": stream,
             "zabbix_version": version, "collected_at": collected, "event_time": timestamp,
             "object_id": object_id, "event_uid": hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
             "vendor_product": "Zabbix", "raw": raw, "status": "unknown", "action": "unknown",
             "user": "unknown", "src": "unknown", "dest": "unknown", "severity": "not_classified"}
    for field in ("hostid", "itemid", "triggerid", "eventid", "auditid", "alertid", "name", "value", "value_type",
                  "units", "key_", "acknowledged", "r_eventid", "recordsetid", "resourceid", "userid", "ns",
                  "num", "value_min", "value_avg", "value_max"):
        if field in row:
            event[field] = row[field]
    if stream == "audit":
        action = int(row.get("action", -1))
        event.update(action=ACTIONS.get(action, "unknown"), action_id=action,
                     user=row.get("username") or str(row.get("userid", "unknown")), src=row.get("ip") or "unknown",
                     resource=RESOURCES.get(int(row.get("resourcetype", -1)), str(row.get("resourcetype", "unknown"))),
                     resource_name=row.get("resourcename", ""), category="authentication" if action in (4, 8, 9) else "change",
                     status="failure" if action == 9 else "success")
    elif stream in ("events", "problems", "triggers", "internal", "discovery", "autoregistration"):
        event["severity_id"] = int(row.get("severity", row.get("priority", 0)))
        event["severity"] = SEVERITIES.get(event["severity_id"], "unknown")
        event["status"] = "resolved" if str(row.get("value", "1")) == "0" or str(row.get("r_eventid", "0")) != "0" else "problem"
    elif stream == "hosts":
        event["status"] = "monitored" if str(row.get("status")) == "0" else "disabled"
        event["dest"] = row.get("host", "unknown")
    elif stream == "alerts":
        event["status"] = {"0": "pending", "1": "sent", "2": "failed", "3": "new"}.get(str(row.get("status")), "unknown")
    hosts = row.get("hosts", [])
    if hosts:
        event["dest"] = hosts[0].get("host", hosts[0].get("name", "unknown"))
        event["host_names"] = [h.get("host", h.get("name", "")) for h in hosts]
    return event
