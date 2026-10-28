# Splunkbase submission materials — 1.0.0

Status: prepared for submission; marketplace approval and Cloud certification are not claimed. Run/review AppInspect on the exact upload archive and resolve or document its findings before submitting.

## Listing fields

| Field | Copy / selection |
| --- | --- |
| App name | Zabbix Vision for Splunk |
| App ID | zabbix_vision |
| Version | 1.0.0 |
| Release status | Beta |
| Author | Majid Ershadi; use the owner's actual Splunk.com account username where required |
| Content type | App |
| License | Apache License 2.0 |
| Platform | Splunk Enterprise on Linux |
| Verified Splunk release | 10.4.1; choose additional compatibility labels only after acceptance testing |
| Zabbix compatibility | Live core integration: 6.0.49, 7.0.32, 7.4.16 |
| Suggested categories | IT Operations, Security, Utilities; select the closest current marketplace choices |
| Hosting | Splunkbase-hosted download, public access, if consistent with the owner's other apps |
| Support | Developer-supported through GitHub Issues; no SLA |
| Documentation | https://github.com/majidershadi/zabbix-vision-for-splunk#readme |
| Support URL | https://github.com/majidershadi/zabbix-vision-for-splunk/issues |
| Website | https://majidershadi.github.io/articles/zabbix-vision-for-splunk/ |
| Download | GitHub v1.0.0 release / final zabbix_vision-1.0.0.tar.gz |
| Icon | zabbix_vision/static/appIcon.png; high-resolution mark in docs/assets/ |
| Navigation logo | zabbix_vision/static/appLogo.png and appLogo_2x.png |

## Short description

Bring Zabbix operations, audit, authentication and agent command evidence into Splunk with secure API collection, flexible endpoints, certificate controls and investigation dashboards.

## Detailed description

Zabbix Vision for Splunk collects Zabbix API records and turns them into an operational and security investigation workspace. Connect multiple instances using API tokens, specify the actual frontend or API path, validate the connection and choose the streams appropriate to your environment.

Six dashboards cover event activity, authentication and configuration changes, current infrastructure snapshots, scoped history/trends, script activity and collector health. Two custom data models support tstats searches and optional acceleration. Search fields retain a redacted structured source payload, stable replay identities and source version information.

Transport controls include CA/hostname verification by default, custom CA bundles, mutual TLS with an optional separately stored key passphrase, TLS minimums, bounded timeouts/read retries and an explicit HTTP CONNECT proxy. Tokens use Splunk's native credential store. Splunk owns the encryption format: new writes use $8$ on 10.6+ and $7$ on earlier releases. Live encryption testing used $7$ on 10.4.1; 10.6+ live validation is pending.

Audit collection includes Zabbix-recorded login, logout, failed login and configuration changes, subject to audit logging and token permissions. Execution visibility combines Zabbix audit/alert operations with forwarded agent/server logs. A separate execution action can invoke predefined, allowlisted Zabbix scripts for allowlisted hosts only after explicit configuration and authorization. It is disabled by default, audited and never retried automatically.

Complete host process and identity-provider visibility requires the additional log sources described in the guide. Zabbix API audit is not a universal API-access or process-execution log. Install one active collector per scope, separate slower inventory inputs and scope metric collection by item IDs.

This independent project targets Splunk Enterprise. It is not endorsed by Zabbix or Splunk. The initial release is beta and requires deployment-specific acceptance. Splunk Cloud approval is not claimed.

## Release notes

Initial public release with 18 streams, six dashboards, two data models, native credential storage, certificate/mTLS controls, flexible API paths, version-aware authentication, bounded checkpointed collection and agent command evidence. Includes installation, configuration, architecture, search, troubleshooting and coverage guides. Read docs/RELEASE_1.0.0.md for tested versions and limitations.

## Privacy and data handling

No product telemetry, analytics beacon or vendor-operated backend is included. The app contacts the configured Zabbix endpoint and optional proxy. Administrators choose Splunk indexes and retention. Known secret fields and script-output fields are redacted; command text and business data may still be sensitive. Restrict index access and review source-side logging policy. Python/OS trust stores, normal Splunk platform services and deployment-specific network infrastructure remain external dependencies.

## Upload preparation

Use the install archive and checksum from the release, not the source ZIP. Verify the version in app.conf and app.manifest. Provide screenshots from the public branded app on a real Splunk installation; existing prototype screenshots are integration evidence and should not be misrepresented as final marketplace screenshots. Confirm the Splunk.com author username, public support contact and any required marketplace agreements in the submission UI. The owner completes legal acceptance and Splunk's review process.

Official process: [Publish apps to Splunkbase](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/), [listing information](https://dev.splunk.com/enterprise/docs/releaseapps/splunkbase/submit-splunkbase-apps/configure-app-information/).
