# Troubleshooting and support diagnostics

Start with the correct app (`zabbix_vision`), selected profile and time range. Test the saved connection, check Collector health, and then verify raw indexed data before investigating data-model acceleration.

| Symptom | Diagnosis and corrective action |
| --- | --- |
| Missing app icon or old name | Check the URL: `zabbix_connect` is the old prototype. The public package contains six case-sensitive PNG assets under `zabbix_vision/static/`, not `appserver/static/`. Verify files/read permissions, reload the browser, and refresh Splunk Web's asset cache if required. Do not put secrets in image URLs. |
| Connection initialization failed | Test the saved connection. Check whether the Zabbix web/server/database services are running, the configured port is reachable from the collector, the profile exists and Splunk can read the native credential. This can be an unavailable endpoint, not just a bad token. |
| 404, HTML response or redirect | Use the actual frontend/API prefix and final HTTPS address. The client does not guess paths or follow redirects. Check reverse-proxy routing. |
| Authentication error on modern Zabbix | Use automatic/Bearer authentication, verify token expiry and user status, and preserve Authorization through the reverse proxy. Body authentication is not supported on 7.2+. |
| Hosts accessible, audit denied | Verify Zabbix Super admin user type, `auditlog.get` role permission and enabled audit logging. Consider a dedicated audit profile with the necessary privilege. |
| TLS certificate failure | Validate the hostname, certificate chain, system/custom CA and clock. Correct the trust chain rather than disabling verification in production. |
| Mutual-TLS/key error | Verify PEM format, matching certificate/key, collector-local absolute paths, service-account read access and passphrase. Blank passphrase fields retain a stored value; remove an obsolete value through Splunk's supported credential administration when changing to an unencrypted key. |
| No events despite successful test | Check streams, enabled input state, destination index, API object permissions, retention and the selected time range. Method accessibility is not proof of resource completeness. |
| Dashboards empty but raw events exist | Check `zabbix_index`, role index access, sourcetypes, instance/time filters and data-model deployment. Expand the time range to include a complete snapshot. Check raw SPL before rebuilding acceleration. |
| Old collector error remains | The dashboard groups by instance, input name and stream. A stopped/retired input's last error may remain in the chosen time window. Inspect `last_seen` and heartbeat age; check the currently active input separately. Do not treat old history as a new failure or simply erase it. |
| Duplicate data or two input names | Check for simultaneous prototype/public collectors or duplicate collectors. Disable the duplicate scope deliberately. Existing data remains; deduplicate by `instance,event_uid` and select the intended profile. |
| Single-second overflow / growing backlog | Narrow history item scope, increase the bounded page limit after capacity review, separate slow streams and check API latency. Checkpoints intentionally remain behind on failure. |
| Snapshot limit exceeded | Increase `snapshot_limit` only after checking response/memory size or reduce permitted scope. Incomplete inventories are intentionally rejected. |
| Metric panels empty | Configure explicit item IDs and correct value types; check collection permissions and retention. Trends exclude the current incomplete hour. |
| Agent commands missing | Confirm applicable command logging, log location, actual forwarding and sourcetype. API inputs do not read remote agent files. Agent evidence uses host identity independently of the API instance selector. |
| Execution denied | Check Splunk administrator and `zabbix_execute_scripts` capabilities, enabled profile, both ID allowlists, explicit confirmation and independent Zabbix permissions. Keep disabled unless needed. |
| Execution timed out | Treat the outcome as unknown. Correlate request UUID, Zabbix audit/alerts and agent evidence before deciding whether another invocation is safe. |

## Useful searches

Inspect current status and age per input/stream:

```spl
`zabbix_events` sourcetype=zabbix:collector
| stats latest(status) AS status latest(error) AS error
    latest(lag_seconds) AS lag_seconds max(_time) AS last_seen
    BY instance input_name stream
| eval heartbeat_age_seconds=now()-last_seen
| convert ctime(last_seen)
```

Inspect replay-aware audit records:

```spl
`zabbix_events` sourcetype=zabbix:audit
| dedup instance event_uid
| spath input=_raw path=raw.details output=details
| table _time instance user src action resource resource_name details
```

Check configuration syntax and external collector health on the collector:

```text
$SPLUNK_HOME/bin/splunk btool check
python3 $SPLUNK_HOME/etc/apps/zabbix_vision/bin/zabbix_health.py --checkpoint-dir $SPLUNK_HOME/var/lib/splunk/modinputs/zabbix_vision --max-age 900
```

Use a maximum age greater than the longest intended input interval plus processing delay. Retired health checkpoints require deliberate cleanup after preserving needed evidence. Do not delete active checkpoints to clear an error: that can cause a backfill and replay.

## Opening a support issue

Include app/Splunk/Zabbix versions, deployment topology, affected stream, selected time range, sanitized error, last successful collection time, expected behavior and a small redacted example. State whether raw searches work and whether an old prototype is still installed. Report through [GitHub Issues](https://github.com/majidershadi/zabbix-vision-for-splunk/issues).

Never attach API tokens, passwords, `passwords.conf`, `splunk.secret`, private keys, session keys, Authorization headers or unredacted customer audit logs. For suspected vulnerabilities, follow the repository's [security policy](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/SECURITY.md).
