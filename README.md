# Zabbix Vision for Splunk

<img src="docs/assets/zabbix-vision-icon.png" width="100" height="100" alt="Zabbix Vision red eye and pulse mark with a green search chevron">

Zabbix Vision brings Zabbix operations, access and configuration audit, and agent command evidence into Splunk. It connects through API tokens, keeps credentials in native Splunk secure storage, and gives operators six dashboards for investigating what happened and whether collection is healthy.

**Initial public beta: 1.0.0 · Apache-2.0 · Linux Splunk Enterprise · App ID `zabbix_vision`**

[Download the install package](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0) · [Detailed engineering article](https://majidershadi.github.io/articles/zabbix-vision-for-splunk/) · [Report an issue](https://github.com/majidershadi/zabbix-vision-for-splunk/issues)

## Why this app exists

A working API request is only the beginning of a collector. The URL may have a reverse-proxy prefix. The next Zabbix release may accept a different authentication mechanism. An audit result can hit its row limit in one second. A login chart can look reassuring while an agent executes a command that the API does not describe completely.

This app treats those cases as part of the integration: explicit endpoint and certificate policy, version-aware authentication, bounded collection with visible failures, and separate evidence sources for API activity and agent processes. The [architecture guide](docs/ARCHITECTURE.md) explains how the implementation was created and why those decisions matter.

## Get started

1. Download `zabbix_vision-1.0.0.tar.gz` and verify its SHA-256. The source ZIP is not an install package.
2. Install on a Linux Splunk Enterprise search head or heavy forwarder, then restart Splunk. Universal forwarders cannot run the API collector.
3. Open **Administration → Connections & collection** as an administrator. Save the actual frontend/API URL and a dedicated Zabbix API token, then test it.
4. Create an input for `audit,events,problems,hosts,alerts`. Use a separate slower input for inventory and an explicitly scoped input for history/trends.
5. Set the destination index and the `zabbix_index` macro, grant search roles access, and check **Collector health** before relying on the dashboards.
6. Deploy the [agent/log examples](zabbix_vision/examples) where host-side command evidence is required.

Read the [installation guide](docs/INSTALLATION.md) for distributed placement, upgrades and the private-prototype migration.

## Included

| Area | Functionality |
| --- | --- |
| Connections | Multiple instances; root, `/zabbix`, arbitrary nested prefix, or full API URL; no guessed endpoint probing |
| Authentication | Version discovery; body auth for 6.0/6.2; Bearer for 6.4 onward; rejects body auth on 7.2+ |
| TLS | CA + hostname verification by default, custom CA, mutual TLS, encrypted key passphrase, TLS 1.2/1.3 minimum, explicit HTTP CONNECT proxy, explicit lab-only insecure options |
| Security | Native `storage/passwords`, no tokens in input/config stanzas, no secrets in responses/logs, admin-only setup, no system-token escalation |
| Audit | Change records, actors, source IPs, recordset correlation, resource metadata, structured redacted details |
| Authentication | Login, logout, failed login from Zabbix audit data; CIM authentication/change tags |
| Operations | Trigger events, current problems, acknowledgements/tags, hosts/interfaces/inventory, items, triggers, groups, templates, proxies, maintenance, services, SLA definitions |
| Other event sources | Discovery hosts/services, autoregistration, internal trigger/item/LLD events |
| Metrics | Explicitly scoped history types 0–4, optional binary history type 5 on 7.0+, closed-hour trends |
| Execution | Zabbix execute audit records, remote-command alert operations, agent/server log extraction, approved script execution with host/script allowlists and separate Splunk capability |
| Reliability | Bounded time-window splitting, nanosecond-aware history IDs, late-arrival overlap, per-stream atomic checkpoints, bounded retries and response sizes, explicit overflow errors |
| Dashboards | Operations, audit/authentication, infrastructure, metrics, scripts/agent activity, collector health; instance/time filters |
| Search | Zabbix Operations and Security data models; `tstats` panels; optional acceleration; deterministic event IDs |
| Monitoring | Collector health events, saved detection searches, Zabbix agent UserParameter health check |

## Documentation

| Guide | What it covers |
| --- | --- |
| [Installation](docs/INSTALLATION.md) | Collector placement, index scope, upgrades and prototype migration |
| [Connection and collection](docs/CONFIGURATION.md) | API permissions, URL prefixes, TLS/mTLS, proxy and polling controls |
| [Architecture / how it was built](docs/ARCHITECTURE.md) | Design decisions, runtime layers and development findings |
| [Dashboards and data models](docs/SEARCH.md) | tstats, optional acceleration, snapshots and example SPL |
| [Authentication and agent coverage](docs/COVERAGE.md) | API/log/OS boundaries and auditd/Sysmon guidance |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Common failures and safe diagnostic steps |
| [Build and release](docs/BUILD.md) | Tests, packaging and AppInspect workflow |
| [Validation evidence](docs/VALIDATION.md) | Actual tests and remaining acceptance gaps |
| [Release notes](docs/RELEASE_1.0.0.md) | Initial public release scope |
| [Splunkbase submission copy](SPLUNKBASE.md) | Descriptions, metadata, privacy and compatibility wording |
| [Splunkbase publishing kit](splunkbase/START_HERE.md) | Copy-ready listing fields, installation, release notes, troubleshooting and upload checklist |
| [Screenshot gallery and captions](splunkbase/SCREENSHOTS.md) | Seven current lab captures, PNG previews and publication context |
| [UserParameter execution detection](docs/USERPARAMETER_EXECUTION.md) | Linux auditd and Windows process telemetry, attribution and collection boundaries |

## Compatibility and evidence

Core integration was tested on **Splunk Enterprise 10.4.1** with official **Zabbix 6.0.49, 7.0.32 and 7.4.16** stacks. All 16 nonmetric streams succeeded on each; scoped history/trend calls and numeric history were also exercised on 7.4. The suite includes **33 automated tests** and **32 successful dashboard/selector searches**. See the validation guide for public-namespace checks and AppInspect results.

The implementation targets Splunk Enterprise 9.4+ and 10.x with Python 3.9-compatible syntax. The 6.2, 6.4 and 7.2 authentication branches retain protocol coverage, but those versions were not tested live. Small-lab success does not certify large deployments, clusters or every resource scenario. Splunk Cloud certification is not claimed.

## Secret storage and certificate policy

Tokens and optional private-key passphrases go to app-scoped `storage/passwords`. **Splunk performs encryption** with its own `splunk.secret`: new writes use `$8$` on 10.6+ and `$7$` on earlier releases. The app does not forge cipher strings or return saved credentials to the browser. `$7$` was verified live on 10.4.1; `$8$` is platform-delegated and covered by version/response tests, with live 10.6+ validation pending.

Old `$7$` credentials do not automatically become `$8$` after upgrade. Follow Splunk's supported re-encryption and backup procedure. Re-enter credentials when moving to an older or different Splunk instance. TLS keys remain service-account-protected files on the collector; the UI stores paths and the optional separate passphrase.

CA and hostname verification default on. The profile accepts custom CA bundles, client certificate/key pairs, TLS 1.2/1.3 minimums and an explicit HTTP CONNECT proxy. HTTP and disabled verification require explicit lab choices. Redirects are refused so credentials are not forwarded to an unexpected location.

## Audit and agent execution

`auditlog.get` requires a Zabbix Super admin user type and method permission. Enable audit logging and retain data beyond your maximum outage/backfill window. API-token use does not create a login record for every request. Web/proxy and identity-provider logs answer different questions.

Zabbix execute audit records, automated remote-command alert operations, app-requested execution audit and forwarded agent logs are separate evidence sources. Enable classic-agent `LogRemoteCommands` or agent-2 `Plugins.SystemRun.LogRemoteCommands`, then forward the actual logs. Local UserParameter/plugin execution and descendants may require auditd, Sysmon or EDR process trees. The [coverage guide](docs/COVERAGE.md) specifies the gaps.

Optional execution is disabled by default. It requires an administrator with `zabbix_execute_scripts`, an enabled profile, both host and script ID allowlists and explicit confirmation. Only predefined Zabbix scripts are accepted. The app audits the request, suppresses output, redacts script output in collected audit details and never automatically retries an execution. A timeout means the outcome needs investigation before another run.

## Reliability and search semantics

Time-based collection splits bounded windows and item scopes when a response reaches its limit. A saturated single second fails visibly and retains its checkpoint. Current-state snapshots carry completion markers, including empty results, so an old problem is not presented as a current problem after a successful empty snapshot.

Delivery is at least once to the modular-input output stream, without an end-to-end indexing transaction. Deduplicate by `instance,event_uid`. Overlap tolerates recent late arrivals and mutable records; updates outside that range need explicit reconciliation. A role-limited empty API result does not establish full infrastructure coverage.

Two custom data models serve tstats panels. Acceleration defaults off; set index scope before enabling summaries. Raw searches remain appropriate for long audit details and current snapshots. No acceleration throughput claim is made.

## Build from source

```bash
python -m pip install -r requirements-dev.txt
python tools/build_assets.py
python -m unittest discover -s tests -v
python tools/check_package.py
python tools/package.py
```

No third-party Python dependencies are bundled in the runtime. Development dependencies are for tests, documentation and asset generation. The original vector mark and its rendering script are included. See [BUILD.md](docs/BUILD.md) for release validation.

## Related work

- [REST Profiler](https://github.com/majidershadi/rest_profiler): reusable outbound API requests from Splunk.
- [VMware Vision](https://github.com/majidershadi/vmware-vision): searchable VMware activity from logs.
- [Engineering articles](https://majidershadi.github.io/articles/): implementation and operational context.

This is an original implementation. The [sample Zabbix add-on](https://github.com/babhalodia/Zabbix-Add-on-For-Splunk) was examined for behavior and limitations; its source is not copied or bundled.

## License and support

Copyright 2026 Majid Ershadi. [Apache License 2.0](LICENSE). Use [GitHub Issues](https://github.com/majidershadi/zabbix-vision-for-splunk/issues) with sanitized examples; see [SECURITY.md](SECURITY.md) for sensitive reports. Developer support has no SLA.

Zabbix Vision is an independent project. Zabbix and Splunk trademarks belong to their owners; no affiliation, endorsement, marketplace approval or certification is implied.

## Primary references

- [Zabbix API authentication](https://www.zabbix.com/documentation/current/en/manual/api)
- [Zabbix audit permissions](https://www.zabbix.com/documentation/current/en/manual/api/reference/auditlog/get)
- [Splunk credential endpoint](https://help.splunk.com/en/splunk-enterprise/leverage-rest-apis/rest-api-reference/9.0/access-endpoints/access-endpoint-descriptions)
- [Splunk 10.6 secret encryption](https://help.splunk.com/en/splunk-enterprise/administer/manage-users-and-security/10.6/install-splunk-enterprise-securely/deploy-secure-passwords-across-multiple-servers)
