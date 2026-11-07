# Dashboard screenshots

Real captures from Splunk Enterprise 10.4.1. Images 01–07 show app version 1.0.0 on 30 October 2026. Image 08 shows 1.1.0 on 1 November 2026; the lab displays UTC timestamps from 31 October. The same dashboards are included in 1.1.1.

| Dashboard | Capture context |
| --- | --- |
| [Operations overview](screenshots/01-operations.png) | Two collector errors are visible before recovery of the disposable Zabbix stack. |
| [Audit and authentication](screenshots/02-audit-authentication.png) | Successful login and configuration changes; the failed-login panel is empty for this scope. |
| [Infrastructure inventory](screenshots/03-infrastructure.png) | Small test inventory, with historical prototype/public inputs and some empty resource panels. |
| [Scripts and agent activity](screenshots/04-agent-execution.png) | Harmless remote-command execution and forwarded agent evidence. |
| [Collector health](screenshots/05-collector-health.png) | Successful collection with backlog after downtime. Success alone does not establish that backfill is complete. |
| [Connections and TLS](screenshots/06-connections-tls.png) | New-profile form showing default certificate controls and empty secret fields. |
| [Metrics and trends](screenshots/07-metrics.png) | Scoped numeric history from the small acceptance lab. |
| [UserParameter executions](screenshots/08-userparameter-executions.png) | 58 matched successful invocations collected through Zabbix log history. Producer deployment is required; see [setup](USERPARAMETER_API.md). |

Open an image for full detail. These captures retain empty panels and horizontal table clipping as rendered by Splunk. Historical lab values do not represent current production status.
