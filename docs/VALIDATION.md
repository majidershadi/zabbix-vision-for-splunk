# Validation evidence

Initial public beta 1.0.0 · 28 October 2026. Integration tests establish the behavior below; they are not vendor certification.

## Live core integration

| Component | Evidence |
| --- | --- |
| Linux Splunk Enterprise 10.4.1 | Installed private prototype, native modular input and persistent REST, credential storage, setup UI, two data models and dashboards |
| Zabbix 6.0.49 | Official disposable Docker stack; legacy body-token authentication; all 16 nonmetric streams succeeded |
| Zabbix 7.0.32 | Official disposable stack; Bearer token; all 16 nonmetric streams succeeded |
| Zabbix 7.4.16 | Official disposable stack; Bearer token; all 16 nonmetric streams plus scoped history/trend calls succeeded; numeric history indexed |
| Native encryption | $7$ observed live on 10.4.1; saved token retrieved through native secure storage |
| Splunk 10.6+ | $8$ selection covered by mocked version/native response fixtures and platform documentation; no running 10.6+ instance was tested |

The public app ID is `zabbix_vision`; the lab-tested private prototype used `zabbix_connect`. The namespace and branding changed for publication. The public build passes the same 33 automated tests and AppInspect 4.4.0 (see APPINSPECT.md). The renamed app was also installed on the 10.4.1 lab: native $7$ token save/retrieval, first-profile setup completion, Zabbix 7.4.16 host/audit access and all 32 dashboard searches passed. Its configuration uses a dedicated zabbix_vision_connections namespace. A deployment of the renamed app must re-create app-scoped credentials and inputs. Prototype screenshots record the actual earlier integration and are not final branded marketplace screenshots.

Methods sometimes returned empty lists in the small lab. That proves accepted protocol/parameters, not rich data coverage for every object. Nonempty trend aggregates were not verified. Intermediate Zabbix releases, other Splunk releases, distributed/cluster failover and Cloud were not tested live.

## Tests and searches

- 33 automated tests passed in the core test suite, including four real TLS handshakes: custom CA, untrusted CA, hostname mismatch and mutual TLS with encrypted private key.
- Transport tests exercised URL prefixes, authentication selection, token-safe redirect refusal, bounded read retries and no execution retry.
- Collector tests exercised bounded time splits, saturated seconds, late arrivals, output failure, checkpoint corruption, snapshot overflow and empty complete snapshots.
- Normalization tests covered secret and audit-script-output redaction and history nanosecond identity.
- Manager tests covered missing session, disabled execution, host allowlists and native input enable/disable endpoints.
- Python 3.9 syntax compatibility and app XML/JSON/config parsing were checked. Local test runtime was Python 3.13.8.
- All 32 dashboard and selector queries dispatched successfully in Splunk, including tstats. Acceleration remained off and performance was not benchmarked.
- Native `btool check` passed in the lab. This is not an AppInspect report.

## Live execution evidence

A predefined harmless script, `printf zabbix_connect_lab_ok`, ran on a disposable Zabbix 7.4 agent. App-mediated execution returned success. Splunk indexed requested/completed records with one correlation UUID, and a matching agent command log record.

With explicit operator approval, the existing lab administrator temporarily received the dedicated execution capability. Original capabilities were restored and profile execution was verified disabled during cleanup. No additional admin account was created.

The log test imported a Docker-log snapshot, not a permanent Docker forwarding service. Production forwarding and external collector-monitoring examples are supplied. The health utility, run as Splunk's service account, reported four inputs, no stale checkpoints and no errors; its UserParameter was not installed into a host agent.

A real nonexistent-user failed login, successful logins and configuration changes appeared in the security dashboard. Live audit inspection revealed script output in Zabbix details; the final implementation redacts that field. Previously indexed harmless test output remains historical data.

## Release validation

The GitHub release includes the exact install archive and checksum. Review the accompanying AppInspect report/status notes where available; local inspection never substitutes for Splunkbase review. Do not claim marketplace publication or Cloud compatibility until those processes succeed.

For complete process and access coverage, use the additional sources in [COVERAGE.md](COVERAGE.md).
