#!/usr/bin/env python3
"""Splunk scheduled modular input protocol, using the bundled Python runtime."""
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from zabbix_vision_lib.client import Client
from zabbix_vision_lib.collector import Collector, State
from zabbix_vision_lib.config import INPUT_DEFAULTS, validate_input
from zabbix_vision_lib.splunk_store import Store


def scheme():
    root = ET.Element("scheme")
    for key, value in (("title", "Zabbix Vision for Splunk"), ("description", "Collect Zabbix API telemetry using a secure connection profile"),
                       ("use_external_validation", "true"), ("streaming_mode", "xml"), ("use_single_instance", "false")):
        ET.SubElement(root, key).text = value
    args = ET.SubElement(ET.SubElement(root, "endpoint"), "args")
    for key, default in INPUT_DEFAULTS.items():
        if key in ("interval", "index", "disabled"):
            continue
        arg = ET.SubElement(args, "arg", name=key)
        ET.SubElement(arg, "title").text = key.replace("_", " ").title()
        ET.SubElement(arg, "description").text = "Default: " + (default or "required / configured scope")
        ET.SubElement(arg, "data_type").text = "string"
        ET.SubElement(arg, "required_on_create").text = "true" if key == "profile" else "false"
        ET.SubElement(arg, "required_on_edit").text = "false"
    return ET.tostring(root, encoding="unicode")


def parameters(node):
    return {p.attrib["name"]: p.text or "" for p in node.findall("param")}


def emit(event, stanza, index):
    e = ET.Element("event", stanza=stanza, unbroken="1")
    for key, value in (("time", event.get("event_time", time.time())), ("index", index),
                       ("source", "zabbix:" + event.get("instance", "unknown")),
                       ("sourcetype", "zabbix:" + event["dataset"]),
                       ("data", json.dumps(event, ensure_ascii=True, separators=(",", ":")))):
        ET.SubElement(e, key).text = str(value)
    ET.SubElement(e, "done")
    sys.stdout.write(ET.tostring(e, encoding="unicode"))
    sys.stdout.flush()


def main():
    if "--scheme" in sys.argv:
        print(scheme())
        return 0
    root = ET.fromstring(sys.stdin.read())
    if "--validate-arguments" in sys.argv:
        try:
            validate_input(parameters(root.find("item")))
            return 0
        except ValueError as exc:
            error = ET.Element("error")
            ET.SubElement(error, "message").text = str(exc)
            print(ET.tostring(error, encoding="unicode"))
            return 1
    store = Store(root.findtext("session_key"))
    directory = root.findtext("checkpoint_dir")
    sys.stdout.write("<stream>")
    sys.stdout.flush()
    for stanza in root.findall("./configuration/stanza"):
        name = stanza.attrib["name"]
        options = validate_input(parameters(stanza))
        try:
            profile = store.profile(options["profile"])
            client = Client(profile, store.secret(options["profile"]), store.secret(options["profile"], "key_password", optional=True))
            # Endpoint and collection scope form part of checkpoint identity; edits safely backfill.
            scope = json.dumps({k: options[k] for k in ("item_ids", "history_types")}, sort_keys=True)
            state = State(directory, name + "|" + profile["url"] + "|" + scope)
            collector = Collector(client, options, state, lambda e: emit(dict(e, input_name=name), name, options["index"]))
            results = collector.run()
            emit({"dataset": "collector", "instance": options["profile"], "input_name": name,
                  "stream": "connection", "status": "success", "event_time": int(time.time()),
                  "zabbix_version": client.version_text, "error": "none"}, name, options["index"])
            state.save("health", {"until": int(time.time()), "seen": {}, "results": results})
        except Exception:
            # Never include session keys, token values, server bodies, or tracebacks in logs.
            emit({"dataset": "collector", "instance": options["profile"], "input_name": name,
                  "stream": "connection", "status": "error", "event_time": int(time.time()),
                  "error": "Connection initialization failed; use Setup connection test and verify credential permissions"}, name, options["index"])
            sys.stderr.write("ERROR Zabbix Vision for Splunk initialization failed; inspect collector events\n")
    sys.stdout.write("</stream>")
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
