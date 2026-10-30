# Support, privacy and license copy

## Support

Developer-supported through [GitHub Issues](https://github.com/majidershadi/zabbix-vision-for-splunk/issues). No support SLA is offered. Include version information and sanitized diagnostics as described in the troubleshooting guide. For sensitive vulnerability reports, follow [SECURITY.md](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/SECURITY.md).

## Data handling

The app has no product telemetry, analytics beacon, advertising or vendor-operated backend. It connects to the configured Zabbix endpoint and optional HTTP CONNECT proxy, and writes selected records into the administrator's Splunk deployment. Normal Splunk platform services and deployment-specific infrastructure remain separate dependencies.

API tokens and optional private-key passphrases use Splunk's native credential store. Certificate/key files stay on the configured collection host; the setup UI stores their paths. Secrets are not returned to the browser after saving.

Collected records can contain usernames, source addresses, host names, resource details, configuration changes and command text. Known credential fields and script output in audit details are redacted, but arbitrary business data may still be sensitive. Administrators control index access, forwarding, retention, source-side logging and any additional redaction required by their organization.

Removing the application does not automatically remove previously indexed events, backups or all separately administered credentials. Apply your retention and decommissioning procedures.

## License and ownership

Copyright 2026 Majid Ershadi. Licensed under the Apache License, Version 2.0; see the bundled LICENSE and NOTICE. Runtime code uses Python's standard library and Splunk-provided interfaces; development tools are not bundled with the app runtime.

Zabbix Vision for Splunk is an independent community project. Zabbix and Splunk trademarks belong to their respective owners. No affiliation, endorsement, Splunkbase approval or Splunk Cloud certification is implied. The red eye/pulse application mark is original project artwork.
