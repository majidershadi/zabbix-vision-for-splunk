# Screenshots and captions

Captured from **Zabbix Vision for Splunk 1.0.0** on Splunk Enterprise 10.4.1, 30 October 2026, after verifying the red app icon. The old `zabbix_connect` lab prototype had missing icon files; they were restored separately. Every listing image below shows the public `zabbix_vision` interface.

These are real disposable-lab screens, not generated UI mockups. The seven-day range includes earlier acceptance tests. No passwords, tokens or private keys are displayed. Browser captures were converted from JPEG to PNG without changing UI content. The 623 × 350 previews are proportional reductions with neutral letterboxing; use the full PNGs where the portal supports larger screenshots.

Open [GALLERY.html](GALLERY.html) after extracting the kit for a local visual index. Recommended upload order: Operations, Audit, Connections/TLS, Agent activity, Collector health, Inventory, Metrics. If the portal limits the image count, prioritize the first five.

| File | Suggested title / caption | Context to preserve |
| --- | --- | --- |
| [01-operations.png](../docs/screenshots/splunkbase/01-operations.png) | **Operations overview:** explore Zabbix events, severity and affected hosts alongside collection health. | Captured before restarting the stopped disposable Zabbix stack; two real collector errors are visible. Connection and all 16 selected nonmetric streams later reported success. This image demonstrates error visibility, not current lab status. |
| [02-audit-authentication.png](../docs/screenshots/splunkbase/02-audit-authentication.png) | **Audit & authentication:** investigate Zabbix-recorded logins, changes, actors and audit records. | Selected profile has successful login/change records; failed-login panel is legitimately empty in this scope. Audit is not a universal API access log. |
| [03-infrastructure.png](../docs/screenshots/splunkbase/03-infrastructure.png) | **Infrastructure inventory:** inspect collected host snapshots and unsupported items. | The acceptance lab contains prototype/public history, including duplicate host rows. Some resource panels are empty. Production guidance requires one active collector per scope. |
| [04-agent-execution.png](../docs/screenshots/splunkbase/04-agent-execution.png) | **Scripts & agent activity:** correlate Zabbix execution records, app requests and forwarded agent command evidence. | Historical harmless remote-command test; automated remote-command panel is empty. This is not evidence of UserParameter/auditd/Sysmon validation. Agent data is independent of the API instance filter. |
| [05-collector-health.png](../docs/screenshots/splunkbase/05-collector-health.png) | **Collector health:** inspect stream status and collection volume while tracking backfill delay. | Current public input is shown with successful stream/connection status after stack recovery. Large lag is real backlog after downtime; success does not mean caught up. Table sorted by input name to show the public input first. |
| [06-connections-tls.png](../docs/screenshots/splunkbase/06-connections-tls.png) | **Connections and TLS:** configure version-aware authentication, custom CA, mutual TLS and native secret storage. | Unsaved new-connection form with placeholders and empty secret fields, showing production-safe defaults. No production connection is implied. The lab acceptance endpoint uses loopback HTTP. |
| [07-metrics.png](../docs/screenshots/splunkbase/07-metrics.png) | **Metrics & trends:** explore explicitly scoped numeric item history and available hourly aggregates. | Historical small-lab item samples; does not establish broad trend correctness or performance. Text/log history is not populated in this example. |

## Image directories

- Full captures: `docs/screenshots/splunkbase/*.png`.
- Size-constrained preview counterparts: `docs/screenshots/splunkbase/previews/*.png`, each exactly **623 × 350**.
- App icons/logos: `zabbix_vision/static/` (36/72-pixel icons and 160 × 40 / 320 × 80 logos).
- High-resolution original mark: `docs/assets/zabbix-vision-icon.png` (512 × 512).

Do not use `docs/screenshots/security.png` for this listing: it shows the private prototype. Do not present any screenshot's historical status as a current production health claim. Full captures preserve long-table horizontal clipping as rendered by Splunk; open the actual dashboard to scroll its detail columns.

Splunk documents the legacy splash screenshot as 623 × 350 PNG and the standard app icon as 36 × 36 PNG in its [file standards](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/approvalcriteria/). Confirm the current submission form's gallery constraints when uploading.
