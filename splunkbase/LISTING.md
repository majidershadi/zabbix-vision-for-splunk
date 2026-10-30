# Listing copy

## App name

Zabbix Vision for Splunk

## Short description

Investigate Zabbix operations, audit, authentication and agent activity in Splunk with secure API collection, flexible TLS controls and data-model dashboards.

## Details

Zabbix Vision for Splunk connects Zabbix monitoring with operational and security investigation. Collect API records from multiple Zabbix instances, keep API tokens in Splunk's native credential store, and explore events, configuration changes, authentication activity, infrastructure and collector health from one application.

### Flexible connections and certificate controls

Use the actual Zabbix frontend address: the site root, `/zabbix`, a custom nested prefix, or the full `api_jsonrpc.php` URL. Automatic authentication discovers the server version and selects the supported token mechanism. Connections support CA and hostname verification, custom CA bundles, mutual TLS, encrypted private-key passphrases, TLS 1.2/1.3 minimums, timeouts, bounded read retries and an explicit HTTP CONNECT proxy. Redirects are refused.

Secrets are saved through Splunk's native credential service. Splunk manages encryption with `$7$` on older releases and `$8$` on 10.6+. The app does not implement its own cipher or display saved secrets. `$7$` was verified live on 10.4.1; live 10.6+ validation remains pending.

### Eighteen collection streams

Collect audit, trigger events, current problems, hosts, items, triggers, host groups, templates, proxies, services, SLA definitions, maintenance, alerts, explicitly scoped history, closed-hour trends, discovery, autoregistration and internal events. Choose streams and cadence per input, with independent profiles for different environments or privilege levels.

### Six investigation dashboards

- **Operations overview:** event counts, severity, affected hosts and recent problems/recoveries.
- **Audit & authentication:** logins, failed logins, configuration changes, source addresses and the audit trail.
- **Infrastructure inventory:** complete current snapshots of monitored resources and active problems.
- **Metrics & trends:** explicitly selected item history and trend data.
- **Scripts & agent activity:** Zabbix execution audit, automated remote-command operations, app-requested execution and forwarded agent command evidence.
- **Collector health:** latest stream status, ingestion volume, delay and heartbeat age.

Two custom data models provide `tstats` searches. Acceleration is optional and disabled by default. Detailed audit records and snapshot views retain appropriate raw-event searches. Stable event identities support replay-aware counting; snapshots include completion markers, including successful empty snapshots.

### Audit and execution visibility

Trace the actor, resource, source address and recordset behind Zabbix-recorded changes. Audit access requires the relevant Zabbix Super admin permission and enabled audit logging. Known credential fields and script output are redacted from collected audit details.

Forward Zabbix agent/server logs for host-side command evidence. Complete process trees, UserParameter/plugin activity and identity-provider decisions require their additional log sources. API audit alone is not an exhaustive HTTP-access or operating-system process log.

An optional execution action can invoke predefined Zabbix scripts on allowlisted hosts. It is disabled by default and requires separate Splunk capability checks, profile enablement, both ID allowlists and explicit confirmation. It accepts no arbitrary command text, suppresses returned output, audits requests and does not retry execution automatically.

### Reliable collection and clear limits

Per-stream atomic checkpoints, bounded time-window splitting, late-arrival overlap and explicit overflow failures help operators detect collection gaps. Delivery can replay after interruption; use `instance,event_uid` for deduplication. Run one active collector per scope and keep inventory and high-volume metrics on suitable separate inputs.

Version 1.0.0 is a public beta for Linux Splunk Enterprise. Core integration was tested on Splunk 10.4.1 with Zabbix 6.0.49, 7.0.32 and 7.4.16. Other versions require acceptance testing. Splunk Cloud certification, cluster validation and large-scale performance guarantees are not claimed.

This independent Apache-2.0 project includes installation, configuration, architecture, search, coverage and troubleshooting guides. It is not affiliated with or endorsed by Splunk or Zabbix.

## Links and metadata

| Field | Value |
| --- | --- |
| Documentation | https://github.com/majidershadi/zabbix-vision-for-splunk#readme |
| Installation | https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/splunkbase/INSTALLATION.md |
| Troubleshooting | https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/splunkbase/TROUBLESHOOTING.md |
| Support | https://github.com/majidershadi/zabbix-vision-for-splunk/issues |
| Release | https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0 |
| Website | https://majidershadi.github.io/articles/zabbix-vision-for-splunk/ |
| License | Apache License 2.0 |
| Price / support | Free; developer support, no SLA |
| Suggested search keywords | Zabbix, monitoring, observability, audit, authentication, agent, API, TLS |
