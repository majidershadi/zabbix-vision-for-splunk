# UserParameter execution through the Zabbix API — 1.1.0

Version 1.1.0 adds an opt-in `userparameters` stream, `zabbix:userparameter` sourcetype, a **UserParameter executions** dashboard, a `UserParameter` object in `Zabbix_Security`, and two disabled-by-default detection searches. A separate Splunk forwarder on the agent is not required for this route.

```text
Fixed UserParameter command → local wrapper start/end JSON log
  → Zabbix active log/logrt item → history.get → Splunk userparameters stream
  → invocation correlation, duration, failures and incomplete-evidence views
```

Zabbix must first collect execution evidence. Existing numeric check results alone cannot reconstruct all executions or the local command definition. The supplied wrapper reports the configured command's outcome; it is not independent OS process auditing and cannot establish every descendant process. See [OS process telemetry](USERPARAMETER_EXECUTION.md) for that additional coverage.

## 1. Deploy the optional Linux wrapper

Review `examples/userparameter-wrapper.py`, `userparameter-execution.json` and `userparameter-execution.conf` in the installed app. The examples are **not installed or executed automatically** on monitored hosts.

On the selected Linux agent, install the wrapper under `/etc/zabbix/scripts/userparameter-wrapper.py` and the JSON configuration under `/etc/zabbix/userparameter-execution.json`. Python 3.9+ is required on that agent. Use administrator-controlled parent directories; the configuration must be a regular file owned by root or the invoking service user and must not be group/world-writable. Keep executable/script/configuration files read-only to untrusted users. The wrapper rejects a symlink at the config or log file itself; it does not secure an administrator's whole filesystem hierarchy.

Provision `/var/log/zabbix` and a log readable by the Zabbix service. The log must be a regular file owned by the wrapper's effective UID, without group/world write permission. The wrapper creates a missing log with mode 0640 (subject to umask), but does not create the directory. Use log rotation that preserves the expected owner/mode and is compatible with `logrt`.

The example maps a simple key to a fixed argument array:

```json
{
  "log_file": "/var/log/zabbix/userparameter-execution.jsonl",
  "commands": {
    "vision.health": {
      "command_id": "vision-health-check",
      "argv": ["/usr/bin/printf", "1\n"],
      "timeout_seconds": 2
    }
  }
}
```

Add the example UserParameter definition to the agent's normal included configuration and reload/restart through your deployment process. The actual `printf` and Python paths must exist. Set the wrapper timeout shorter than the effective Zabbix item/agent timeout so it can record timeout cleanup before Zabbix kills it.

The wrapper supports **fixed commands and simple keys** (`A–Z`, `a–z`, digits, underscore, dot and hyphen; at most 128 characters). Flexible `key[*]` argument substitution is deliberately unsupported in this release. It uses a fixed `argv` with `shell=False`; invoking a shell is possible only if an administrator explicitly configures that executable and fixed arguments.

Stdout and stderr pass through unchanged to preserve the check's normal behavior; they are never copied into the wrapper audit log. Command text, arguments and environment are also omitted. The configured `command_id` is a nonsecret identifier, not the command itself.

Normal command exit codes are preserved; wrapper timeout returns 124, interruption 130, and spawn/config/logging failures 125. A start-log failure prevents execution. An end-log failure can happen after the command ran; the wrapper returns 125 and must not be blindly retried. SIGKILL, host failure or a killed agent can leave only a start record. Background descendants may outlive a normally exiting parent; OS telemetry is needed to observe them.

## 2. Create the Zabbix execution-log item

Configure an item on the matching Zabbix host:

| Field | Value |
| --- | --- |
| Name | UserParameter execution evidence |
| Type | Zabbix agent (active) |
| Information type | Log |
| Key | `logrt["/var/log/zabbix/^userparameter-execution\.jsonl(\.[0-9]+)?$"]` |
| Update interval | For example, 1 second; tune for volume |
| History retention | Longer than your maximum Splunk outage/backfill window |
| Preprocessing | Preserve every complete JSON line; do not discard unchanged records or remove start/end entries |

Configure `ServerActive` and `Hostname` according to your normal Zabbix deployment. Ensure the agent can read the file. This is a separate item from the numeric `vision.health` result item. Record the **log item's numeric item ID**. Zabbix documents [active log monitoring](https://www.zabbix.com/documentation/current/en/manual/config/items/itemtypes/zabbix_agent/log_items) and [log/text history retrieval](https://www.zabbix.com/documentation/current/en/manual/api/reference/history/get).

## 3. Enable the Splunk stream

After upgrading to 1.1.0 and restarting Splunk, open **Administration → Connections & collection**. Reuse a tested profile with `item.get` and `history.get` access to the selected host/items. A Super admin token is not required solely for this stream.

Create a **separate input**, for example `production-userparameters`:

```ini
[zabbix_vision://production-userparameters]
profile = production
streams = userparameters
userparameter_item_ids = 12345
index = zabbix
interval = 60
lookback = 3600
disabled = 0
```

Replace 12345 with the actual execution-log item ID. Up to 1000 unique IDs are accepted. Log and Text history types (2 and 4) are supported; metadata validation rejects numeric-result items and inaccessible IDs before advancing a checkpoint. The normal metric `item_ids` setting is separate.

The input uses the existing bounded windows, overlap and checkpoint mechanism. Keep one active collector per scope. Changing the execution-item scope changes checkpoint identity and can trigger backfill. Existing inputs with an empty new option keep their previous checkpoint identities.

Avoid collecting these same items through the generic `history` stream if you want the strict execution-field allowlist: generic history retains values, while `userparameters` omits unrecognized fields and raw payloads. Broad `items` snapshots can also retain `lastvalue`; review that scope if using a custom producer with sensitive payloads. The supplied wrapper never writes command output or arguments to its evidence log.

## 4. Verify and investigate

Run a harmless known check through the normal Zabbix item mechanism. Verify its original item result, two local JSON records, Zabbix log history, successful `userparameters` collector health and corresponding Splunk records:

```spl
`zabbix_events` sourcetype=zabbix:userparameter
| table _time instance dest itemid userparameter_key invocation_id phase status exit_code duration_ms parse_status error
```

Open **UserParameter executions**. Correlation groups by instance, Zabbix host ID, log item ID and invocation UUID. It distinguishes start-and-end, start-only, end-only and conflicting records. Missing records can result from retention, selected time range, forwarding/backfill lag or producer interruption. **Start-only is not proof of a running process.** Failure counters and duration values are producer-reported.

```spl
`zabbix_events` sourcetype=zabbix:userparameter parse_status=valid
| `zabbix_userparameter_correlation`
```

The invalid-record panel exposes parser errors and item identity without echoing the rejected value. Invalid records advance past collection once indexed so one bad line does not indefinitely block valid evidence. They retain deterministic history-based event IDs for investigation and deduplication.

`_time` uses the Zabbix history clock. `execution_time` retains the producer's Unix timestamp; `history_clock`/`history_ns` retain transport timing. `dest` and `hostid` come from Zabbix item metadata rather than a self-reported hostname. These fields are not cryptographic attestation.

Review and deliberately enable the saved searches for failures/rejected records and missing completion evidence. Tune the 900-second missing-end threshold above execution timeout plus collection/backfill delay. Widen the search window when needed. Rebuild the Security data-model acceleration summary if already enabled so the new object is summarized.

## Compatible producers and Windows

The Linux wrapper is optional. A separately reviewed producer can emit one JSON object per line with `schema="zabbix_userparameter_execution/v1"`, a UUID `invocation_id`, simple `userparameter_key` and `command_id`, positive integer `pid`, integer Unix `timestamp`, and `phase/status`.

Start uses `phase=start,status=started`. End uses `phase=end` and `status=success|failure|timeout|interrupted|spawn_failed`, finite nonnegative `duration_ms` and `exit_code` (0–255 or null; success requires 0 and failure requires nonzero). Records are bounded to 16 KiB. Duplicate JSON fields are rejected. Unknown fields are dropped. This release does not include a Windows wrapper or automatic conversion from raw auditd/Sysmon events. Those need a reviewed producer or the independent OS-search workflow.
