# Version 1.0.0 — public beta

Released 29 October 2026. Submission documentation and screenshots refreshed 30 October 2026; the application binary is unchanged.

## New in this release

- Multiple API-token connection profiles with root, `/zabbix`, custom-prefix and full API URLs.
- Zabbix-version-aware authentication and modern Bearer-header support.
- Native Splunk credential storage, custom CA, mutual TLS, protected key passphrases, TLS minimums and HTTP CONNECT proxy settings.
- Eighteen configurable streams for operations, audit, inventory, alerts, discovery, scoped history and trends.
- Atomic per-stream checkpoints, bounded collection windows, replay identities and complete snapshot markers.
- Six investigation dashboards, two custom data models, optional acceleration and collector-health monitoring.
- Redacted audit details, authentication activity, agent/server command-log extraction and a separately authorized, disabled-by-default script execution action.
- Installation, configuration, architecture, coverage, search and troubleshooting guides.

## Tested environment

Core integration: Linux Splunk Enterprise 10.4.1 with Zabbix 6.0.49, 7.0.32 and 7.4.16. Automated release validation: 33 passing tests and 32 successful dashboard/selector searches. The public namespace also passed live 7.4.16 connection/setup checks. Local AppInspect 4.4.0: 0 errors, 0 failures, 10 warnings; see the attached report and warning review.

## Known limitations

- Beta: deployment-specific acceptance remains required. Other Splunk/Zabbix releases, clusters, high availability and large-scale behavior are not certified.
- Splunk Cloud approval and marketplace approval are not claimed.
- `$7$` storage was verified live; `$8$` uses the Splunk 10.6+ platform and fixture coverage, with live 10.6+ testing pending.
- Data-model acceleration has not been performance-benchmarked. Nonempty trend aggregates were not verified in the initial small lab.
- API audit is not an exhaustive API-access or OS-process log. Forward the additional sources described in the coverage guide.
- A saturated time window fails visibly instead of silently dropping data. Tune page limits, item scope and cadence based on actual volume.
- Execution timeouts have unknown outcomes and are never automatically retried; investigate before another attempt.

## Upgrade / prototype migration

This is the first public release. Install into `zabbix_vision`. Users of the private `zabbix_connect` prototype must disable corresponding old inputs, re-enter credentials and plan backfill. Do not copy encrypted secret strings or assume checkpoint migration.

## Screenshot-kit update

The old lab prototype's missing icon files were restored and verified. The public release already contained the required icons. New screenshots show the current public app with real disposable-lab data and documented empty/error conditions; no new runtime version was created for this media update.
