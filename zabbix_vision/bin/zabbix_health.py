#!/usr/bin/env python3
"""Zabbix agent health check. Read only redacted collector checkpoints."""
import argparse
import json
from pathlib import Path
import time


def health(directory, max_age):
    paths = list(Path(directory).glob("*_health.json"))
    now = time.time()
    result = {"ok": 1, "inputs": len(paths), "stale": 0, "errors": 0, "max_age_seconds": 0}
    if not paths:
        result["ok"] = 0
    for path in paths:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            age = max(0, now - data["until"])
            result["max_age_seconds"] = max(result["max_age_seconds"], int(age))
            result["stale"] += int(age > max_age)
            result["errors"] += sum(r["status"] != "success" for r in data["results"])
        except (ValueError, KeyError, OSError):
            result["errors"] += 1
    if result["stale"] or result["errors"]:
        result["ok"] = 0
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument("--max-age", type=int, default=900)
    args = parser.parse_args()
    print(json.dumps(health(args.checkpoint_dir, args.max_age)))
