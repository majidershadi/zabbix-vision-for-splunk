"""Bounded collection, overlap deduplication, and atomic per-stream checkpoints."""
import hashlib
import json
import os
from pathlib import Path
import time
from .client import APIError
from .config import ids, validate_input
from .normalize import normalize


class Overflow(APIError):
    pass


class State:
    def __init__(self, directory, namespace):
        self.root = Path(directory)
        self.root.mkdir(parents=True, exist_ok=True)
        self.prefix = hashlib.sha256(namespace.encode()).hexdigest()

    def path(self, stream):
        return self.root / (self.prefix + "_" + stream + ".json")

    def load(self, stream):
        try:
            with self.path(stream).open(encoding="utf-8") as f:
                state = json.load(f)
            if not isinstance(state, dict) or "until" not in state or not isinstance(state.get("seen", {}), dict):
                raise ValueError("Invalid checkpoint")
            int(state["until"])
            return state
        except FileNotFoundError:
            return None
        except (ValueError, TypeError):
            raise APIError("Checkpoint is corrupt; restore it or explicitly reset the affected input")

    def save(self, stream, value):
        path = self.path(stream)
        temporary = path.with_suffix(".tmp.%s" % os.getpid())
        try:
            with temporary.open("w", encoding="utf-8") as f:
                json.dump(value, f, separators=(",", ":"))
                f.flush()
                os.fsync(f.fileno())
            os.replace(str(temporary), str(path))
        finally:
            if temporary.exists():
                temporary.unlink()


def bounded_window(client, method, params, start, end, limit):
    """Split inclusive time ranges; never advance past a potentially truncated second."""
    if start > end:
        return
    request = dict(params, time_from=start, time_till=end, limit=limit, sortfield="clock", sortorder="ASC")
    rows = client.call(method, request)
    if not isinstance(rows, list):
        raise APIError("Expected a list from " + method)
    if len(rows) >= limit:
        if start == end:
            # Item partitioning helps high-volume history without timestamp/ns loss.
            itemids = params.get("itemids", [])
            if len(itemids) > 1:
                mid = len(itemids) // 2
                for part in (itemids[:mid], itemids[mid:]):
                    yield from bounded_window(client, method, dict(params, itemids=part), start, end, limit)
                return
            raise Overflow("%s reached page_size in a single second (%s); increase page_size or narrow scope. Checkpoint retained." % (method, start))
        middle = (start + end) // 2
        yield from bounded_window(client, method, params, start, middle, limit)
        yield from bounded_window(client, method, params, middle + 1, end, limit)
    else:
        yield from rows


def snapshot_spec(stream, version):
    specs = {
        "hosts": ("host.get", {"output": ["hostid", "host", "name", "status", "maintenance_status"],
                               "selectInterfaces": ["interfaceid", "type", "ip", "dns", "available", "error"],
                               "selectInventory": "extend", "selectTags": "extend"}),
        "items": ("item.get", {"output": ["itemid", "hostid", "name", "key_", "value_type", "units", "status", "state", "error", "lastvalue", "lastclock"], "selectHosts": ["hostid", "host"], "templated": False}),
        "triggers": ("trigger.get", {"output": ["triggerid", "description", "priority", "value", "status", "lastchange", "error"], "selectHosts": ["hostid", "host"], "selectTags": "extend", "templated": False}),
        "problems": ("problem.get", {"output": "extend", "selectTags": "extend", "selectAcknowledges": "extend", "recent": False}),
        "hostgroups": ("hostgroup.get", {"output": ["groupid", "name"]}),
        "templates": ("template.get", {"output": ["templateid", "host", "name", "description"]}),
        "proxies": ("proxy.get", {"output": ["proxyid", "name", "operating_mode"] if version >= (7, 0, 0) else ["proxyid", "host", "status"]}),
        "services": ("service.get", {"output": "extend", "selectTags": "extend"}),
        "sla": ("sla.get", {"output": "extend"}),
        "maintenance": ("maintenance.get", {"output": "extend"}),
    }
    if stream == "sla" and version < (6, 0, 0):
        raise APIError("SLA collection requires Zabbix 6.0+")
    return specs[stream]


def timed_specs(stream, options, version):
    if stream == "audit":
        return [("auditlog.get", {"output": "extend"}, {})]
    if stream in ("events", "discovery", "autoregistration", "internal"):
        pairs = {"events": [(0, 0)], "discovery": [(1, 1), (1, 2)], "autoregistration": [(2, 3)], "internal": [(3, 0), (3, 4), (3, 5)]}[stream]
        return [("event.get", dict(output="extend", source=src, object=obj,
                 **({"selectHosts": ["hostid", "host"], "selectTags": "extend", "selectAcknowledges": "extend"} if src == 0 else {})), {}) for src, obj in pairs]
    if stream == "alerts":
        # Include notification and remote-command operation records; status can change.
        return [("alert.get", {"output": ["alertid", "actionid", "eventid", "clock", "status", "retries", "alerttype", "esc_step", "userid"]}, {})]
    if stream == "history":
        types = [int(t) for t in options["history_types"].split(",")]
        if 5 in types and version < (7, 0, 0):
            raise APIError("Binary history requires Zabbix 7.0+")
        return [("history.get", {"output": "extend", "history": t, "itemids": ids(options["item_ids"])}, {"value_type": t}) for t in types]
    if stream == "trends":
        return [("trend.get", {"output": "extend", "itemids": ids(options["item_ids"])}, {})]
    return None


class Collector:
    def __init__(self, client, options, state, emit, clock=time.time):
        self.client = client
        self.options = validate_input(options)
        self.state = state
        self.emit = emit
        self.clock = clock

    def collect_stream(self, stream, now):
        o = self.options
        specs = timed_specs(stream, o, self.client.version)
        count = 0
        if specs is None:
            method, params = snapshot_spec(stream, self.client.version)
            limit = int(o["snapshot_limit"])
            rows = self.client.call(method, dict(params, limit=limit))
            if not isinstance(rows, list):
                raise APIError("Expected snapshot list")
            if len(rows) >= limit:
                raise Overflow("Snapshot hit snapshot_limit; raise the limit before collecting an incomplete inventory")
            # Empty inventory snapshots must remain observable (e.g. all problems resolved).
            snapshot_id = "%s:%s:%s" % (o["profile"], stream, now)
            for row in rows:
                event = normalize(stream, row, o["profile"], self.client.version_text, now)
                event["snapshot_id"] = snapshot_id
                event["event_time"] = now
                self.emit(event)
                count += 1
            self.emit({"dataset": "snapshot", "snapshot_dataset": stream, "snapshot_id": snapshot_id,
                       "instance": o["profile"], "event_time": now, "count": count, "complete": True})
            return count, 0
        previous = self.state.load(stream)
        end = now - int(o["settle_delay"])
        # Trends for the current hour are mutable; only collect fully closed hours.
        if stream == "trends":
            end = end // 3600 * 3600 - 1
        start = max(0, int(previous["until"]) - int(o["overlap"]) + 1) if previous else max(0, end - int(o["lookback"]) + 1)
        if start > end:
            return 0, max(0, now - int(previous["until"])) if previous else 0
        until = min(end, start + int(o["window"]) - 1)
        # Ensure overlap cannot starve forward progress.
        if previous:
            until = min(end, max(until, int(previous["until"]) + int(o["window"])))
        seen = dict(previous.get("seen", {})) if previous else {}
        for method, params, extra in specs:
            for row in bounded_window(self.client, method, params, start, until, int(o["page_size"])):
                event = normalize(stream, dict(row, **extra), o["profile"], self.client.version_text, now)
                uid = event["event_uid"]
                # Re-index updates of mutable event/alert records within the overlap.
                fingerprint = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
                if seen.get(uid, {}).get("fingerprint") == fingerprint:
                    continue
                self.emit(event)
                count += 1
                seen[uid] = {"clock": int(row["clock"]), "fingerprint": fingerprint}
        keep_from = until - int(o["overlap"]) + 1
        seen = {uid: data for uid, data in seen.items() if data["clock"] >= keep_from}
        self.state.save(stream, {"until": until, "seen": seen})
        return count, now - until

    def run(self):
        if self.client.version is None:
            self.client.discover()
        results = []
        now = int(self.clock())
        for stream in self.options["streams"].split(","):
            started = self.clock()
            health = {"dataset": "collector", "instance": self.options["profile"], "stream": stream,
                      "event_time": now, "zabbix_version": self.client.version_text}
            try:
                count, lag = self.collect_stream(stream, now)
                health.update(status="success", count=count, lag_seconds=lag)
            except (APIError, ValueError, OSError) as exc:
                # Only APIError messages are authored by this package; OS errors can contain paths.
                health.update(status="error", error=str(exc) if isinstance(exc, APIError) else "Collection or checkpoint failure", count=0)
            health["duration_seconds"] = round(self.clock() - started, 3)
            self.emit(health)
            results.append(health)
        return results
