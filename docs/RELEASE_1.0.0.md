# Zabbix Vision for Splunk 1.0.0

Initial public beta Ã‚Â· 29 October 2026 Ã‚Â· Apache-2.0 Ã‚Â· App ID `zabbix_vision`

This release brings Zabbix operations, access/change audit and agent command evidence into Splunk with native credential storage and explicit transport controls.

## Included

- Multiple token profiles with root, `/zabbix`, nested-prefix or full API URLs.
- Version-aware authentication for Zabbix 6.0 through the recent 7.x protocol generations.
- Verified TLS, custom CA, client certificate/key, separately stored key passphrase, minimum TLS and HTTP CONNECT proxy controls.
- Eighteen collection streams covering operations, inventory, audit, authentication, alerts, scoped history/trends and discovery/internal events.
- Bounded splitting, atomic stream checkpoints, replay identities and complete snapshot markers.
- Six dashboards, two optional accelerated data models, native field extractions and health checks.
- Agent/server command-log extraction and a restricted, separately authorized script execution path.
- Redaction for known credential fields and script output inside audit records.

## Validation and boundaries

Core integration was tested on Linux Splunk Enterprise 10.4.1 with Zabbix 6.0.49, 7.0.32 and 7.4.16; 33 automated tests and 32 dashboard searches passed. The public `zabbix_vision` namespace is a rename of the lab-tested private prototype and has automated regression coverage plus a live 7.4.16 profile/setup acceptance test. See VALIDATION.md for exact evidence and release checks.

`$7$` storage was verified live. `$8$` behavior delegates to Splunk 10.6+ native storage and was tested through version/response fixtures, not a live 10.6+ instance. Data-model acceleration is optional and not performance-benchmarked. Small lab methods sometimes returned empty results; nonempty trend aggregates were not verified.

Zabbix API records cannot establish every host process or API request. Configure agent/server/web logs and OS process auditing for the relevant gaps. Cloud certification, high availability, cluster validation and complete OS execution coverage are not claimed.

## Installation

Use `zabbix_vision-1.0.0.tar.gz` from this release and verify its checksum. Install on a Linux Enterprise collector/search tier as described in INSTALLATION.md. Execution defaults disabled and requires separate permissions and both allowlists.

Private `zabbix_connect` prototype users must disable old inputs, re-enter credentials in the new app namespace and plan checkpoint/backfill behavior. No unattended migration is performed.
