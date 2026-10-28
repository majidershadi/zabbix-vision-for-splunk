# Connection and collection guide

## Zabbix access

Create a dedicated Zabbix API token. Grant only the API methods and host-group access required by the selected streams. `auditlog.get` requires a Zabbix Super admin user type and API method permission. A separate audit profile can isolate that privilege from routine operational collection. Enable audit logging and retain records longer than the maximum expected outage/backfill.

The connection test checks `host.get` and `auditlog.get`. It reports method access, not completeness of every host's data. Empty results can mean no matching records or limited permissions.

## Endpoint and authentication

Accepted profile URLs include:

```text
https://monitoring.example.com
https://monitoring.example.com/zabbix
https://monitoring.example.com/platform/monitoring
https://monitoring.example.com/platform/monitoring/api_jsonrpc.php
```

The client appends `api_jsonrpc.php` to the supplied frontend path. It does not guess prefixes or send a token through redirects. Configure the actual frontend address. Embedded credentials, URL queries and fragments are rejected.

Automatic authentication discovers `apiinfo.version` without authentication, uses JSON-body tokens for 6.0/6.2 and Bearer headers from 6.4 onward. JSON-body authentication is rejected for 7.2+. A reverse proxy must preserve the Authorization header for Bearer requests.

## TLS and transport

| Setting | Behavior |
| --- | --- |
| Certificate verification | CA and hostname verification enabled by default |
| Custom CA bundle | Absolute PEM file on the collector; blank uses Python system trust |
| Client certificate/key | Both absolute PEM paths required for mutual TLS |
| Key passphrase | Separate native Splunk credential; blank preserves an existing secret |
| Minimum TLS | 1.2 default; optional 1.3 |
| Proxy | Explicit HTTP CONNECT proxy; embedded proxy credentials unsupported |
| Timeout | 1–300 seconds, default 30 |
| Read retries | 0–5, default 3; script execution never retries automatically |
| Response limit | 1–256 MiB, default 32 |
| Insecure HTTP/TLS | Explicit isolated-lab choices; use verified HTTPS in production |

Give the Splunk service account read access to CA/certificate files and private access to key files. Restrict directory traversal and ownership too. A saved profile does not upload those files. When changing to an unencrypted key, remove an obsolete passphrase credential through Splunk's supported credential endpoint; an empty UI field retains it.

## Polling and checkpoints

| Option | Default | Operational meaning |
| --- | --- | --- |
| interval | 60 seconds | Schedule per input; separate inventory to reduce volume |
| lookback | 3600 seconds | First poll only; existing checkpoints take precedence |
| overlap | 120 seconds | Revisit recent time for late arrivals and mutable records |
| settle_delay | 10 seconds | Avoid the freshest mutable edge |
| window | 3600 seconds | Maximum backfill range advanced per poll |
| page_size | 1000 | Time-window split threshold; a saturated single second fails explicitly |
| snapshot_limit | 100000 | Fail before emitting an incomplete snapshot |
| item_ids | empty | Required explicit scope for history and trends |
| history_types | 0,1,2,3,4 | Float, character, log, unsigned and text; binary 5 is opt-in on 7.0+ |

The collector recursively splits time windows and, for history, item scopes. If one second for one scope reaches the row limit, increase `page_size` or narrow scope. It does not silently skip that second. Checkpoints advance only after output completes; a crash can replay records. Deduplicate with `instance,event_uid`. Splunk indexing is not transactionally acknowledged by this mechanism.

Checkpoints live under `$SPLUNK_HOME/var/lib/splunk/modinputs/zabbix_vision`. Corrupt checkpoints fail explicitly. Restore from backup or deliberately create a new input for replay; avoid casually deleting state. Changing an endpoint/scope creates a separate checkpoint namespace. Retire old health checkpoints when retiring inputs so external monitoring does not keep reporting them stale.

Updates outside the overlap require explicit reconciliation/backfill. Problems are also current-state snapshots. Trends exclude the current incomplete hour and may therefore show expected delay.
