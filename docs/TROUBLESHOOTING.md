# Troubleshooting

| Symptom | Check and response |
| --- | --- |
| Icon missing / old app name | A `/zabbix_connect/` bookmark opens the private prototype. Open `/zabbix_vision/`. Icons belong in the app's `static/` directory with case-sensitive names; check read permissions and refresh browser/Splunk Web asset caches after repairing files. |
| Connection initialization failed | Check that Zabbix frontend/server/database services are running, endpoint/port reachability, saved profile and credential access. The generic message can also mean an unavailable endpoint. |
| Old health error or duplicate rows | Check input name, last_seen and heartbeat age; retired inputs can leave historical status. Prototype/public collectors sharing a scope can duplicate records. Run one active collector per scope and retain indexed history. |
| Connection version fails | Confirm frontend/API URL and custom prefix, outbound DNS/network, proxy and CA trust. Redirects are intentionally refused. |
| 7.2+ authentication fails | Use automatic/Bearer mode; preserve Authorization through the reverse proxy. Check token expiry, user status and role method access. |
| Hosts work, audit denied | Audit requires Zabbix Super admin user type and `auditlog.get` permission. Use a dedicated audit profile if necessary. |
| Empty API data | Verify a known object with the same token and host-group scope; check time range and audit retention. Empty is not proof of universal access. |
| Collector shows error | Inspect the affected stream and sanitized error; other streams can continue. Resolve before relying on that stream's freshness. |
| Single-second overflow | Raise page_size or narrow item scope. The affected checkpoint is retained to prevent silent loss. |
| Inventory overflow | Increase snapshot_limit after assessing memory/response size; incomplete inventories are rejected. |
| Dashboard empty | Check `zabbix_index`, role index permissions, sourcetypes, time/instance filters, and model deployment. Use raw searches before investigating acceleration. |
| Collection lag grows | Check API latency, backlog window versus poll cadence, row volume and server load. Separate slow inventory and scoped metrics. |
| TLS key errors | Confirm paired certificate/key files, collector service-account access, encrypted key passphrase and PEM format. Avoid echoing key material in diagnostics. |
| Execution denied | Check both Splunk capabilities, profile switch, both allowlists, confirmation and independent Zabbix permissions. Execution defaults disabled. |
| Execution times out | Treat result as unknown. Correlate the request UUID, Zabbix audit and agent logs before deciding to rerun. |
| No agent commands | Enable the applicable remote-command logging and deploy an actual log collection path. API collection does not ingest host log files. |
| Health utility is stale | Check running inputs, permissions and retired health checkpoints. Set max-age above your longest intended poll plus processing delay. |

Useful Splunk checks:

```spl
`zabbix_events` sourcetype=zabbix:collector
| stats latest(status) AS status latest(error) AS error max(_time) AS last_seen
  BY instance input_name stream
```

```text
$SPLUNK_HOME/bin/splunk btool check
python3 $SPLUNK_HOME/etc/apps/zabbix_vision/bin/zabbix_health.py --checkpoint-dir $SPLUNK_HOME/var/lib/splunk/modinputs/zabbix_vision --max-age 900
```

Report issues with app/Splunk/Zabbix versions, stream, sanitized error, expected behavior and a minimal redacted record. Never attach tokens, passwords.conf, splunk.secret, client private keys, session keys or unredacted customer audit history.

## UserParameter execution evidence (1.1.0)

- **No execution records:** install the wrapper or compatible producer first. Numeric item results alone are insufficient. Confirm local JSON lines, active Zabbix log-item history, then the scoped Splunk input, in that order.
- **Wrapper fails before running:** verify Python/executable paths, root or service-user ownership of the regular configuration file, no group/world write permission, and a service-owned writable log. A copied file can retain the wrong numeric owner. Check the administrator-controlled parent directories too.
- **Collector rejects item IDs:** select the execution log item's ID, information type Log or Text, with token access to `item.get` and `history.get`. Do not select the numeric check-result ID.
- **Invalid records:** use the versioned JSON schema. Duplicated JSON fields, oversized records, invalid identifiers or contradictory status/exit code are rejected without retaining the payload.
- **Start-only rows:** check selected time range, collection lag, Zabbix retention, wrapper timeout and process interruption. Start-only does not prove that a command is still running.
- **New model fields missing:** rebuild/reconfigure an existing accelerated Security model summary, then rerun the search. Acceleration is off by default.

Full configuration and verification: [UserParameter API guide](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/docs/USERPARAMETER_API.md).
