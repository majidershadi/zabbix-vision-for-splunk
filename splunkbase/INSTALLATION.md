# Installation and first use

## Requirements

- Linux Splunk Enterprise. Live acceptance used 10.4.1. The implementation targets 9.4+ and 10.x with Python 3.9-compatible syntax; additional releases need acceptance testing.
- Network access from the collection host to the actual Zabbix frontend/API endpoint and any configured proxy.
- A dedicated Zabbix API token with the necessary method and host-group access. Audit needs `auditlog.get`, a Super admin user type, enabled audit logging and sufficient retention.
- A destination Splunk index, appropriate index retention, and search-role access. Check API polling and ingestion volume against your environment's capacity.
- For custom CA or mutual TLS, PEM files readable by the Splunk service account on the collector. Protect private keys with restrictive ownership and permissions.

## Placement

| Deployment | Placement |
| --- | --- |
| Small standalone Enterprise | Install the app and configure inputs on that instance. |
| Distributed Enterprise | Run one active collection scope on a heavy forwarder or designated Enterprise collector. Deploy parsing knowledge to the parsing tier and search knowledge/dashboards to the search tier. Configure profiles on the actual collector. |
| Universal forwarder | Use only for forwarding agent/server log files with the examples; it cannot run this API modular input. |
| Search-head cluster / Splunk Cloud | Not certified by this release. Do not assume that copying inputs to every member is supported. |

## Install the package

1. Download `zabbix_vision-1.0.0.tar.gz` and its SHA-256 file from the [release](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0).
2. Verify SHA-256 against `872443da22ae6b37df4c34225364b004ed6674c3dc56b79b18c3befbd2ca7692`. On Linux, use `sha256sum -c zabbix_vision-1.0.0.tar.gz.sha256` in the download directory. On Windows, use `Get-FileHash .\zabbix_vision-1.0.0.tar.gz -Algorithm SHA256` and compare.
3. Open **Apps → Manage Apps → Install app from file**, select the `.tar.gz`, install, then restart Splunk in your approved maintenance window. Do not install the GitHub source ZIP or the submission-kit ZIP.
4. Open **Zabbix Vision for Splunk**. The app directory and URL namespace are `zabbix_vision`. A bookmark containing `zabbix_connect` points to the earlier private prototype.

## Configure index scope

Create an index such as `zabbix` through your normal index-management process. Configure the app's `zabbix_index` macro on the search tier, either in Settings → Advanced search → Search macros (app context: Zabbix Vision) or in `local/macros.conf`:

```ini
[zabbix_index]
definition = index=zabbix
iseval = 0
```

Set the input's destination index to the same value. The execution-log monitor defaults to `main`; override its index in the existing stanza in `local/inputs.conf` when using another index:

```ini
[monitor://$SPLUNK_HOME/var/log/splunk/zabbix_vision_actions.log]
index = zabbix
```

Include forwarded agent/server logs in the macro scope and grant the intended roles access to all selected indexes. Avoid editing packaged `default/` files.

## Save and test a connection

1. As a Splunk administrator, open **Administration → Connections & collection**.
2. Choose a stable profile name, for example `production`.
3. Enter the actual frontend URL (`https://monitoring.example.com`, `/zabbix`, a custom prefix, or the full API path). The app appends `api_jsonrpc.php` to frontend paths; it does not discover unknown prefixes or follow redirects.
4. Enter a dedicated API token and keep authentication on **Automatic by Zabbix version**. Ensure a reverse proxy preserves the Authorization header for modern Zabbix releases.
5. Keep CA/hostname verification enabled. Configure custom CA/mTLS files if required. Paths refer to the collector, not the browser machine. Blank passphrase/token fields retain existing saved secrets during edits.
6. Save the profile, then select **Test saved connection**. Verify the reported server version and host/audit method access. Empty accessible results do not prove access to all resources.
7. Leave script execution disabled unless you separately configure and authorize that feature.

## Create collection inputs

Start with `audit,events,problems,hosts,alerts`, a 60-second interval and a deliberate initial lookback. Create a separate input for less-frequent inventory at 300–900 seconds. Use explicit item IDs in a separate history/trends input; the app does not collect every item's history automatically.

The input name is part of its checkpoint identity. Renaming an input starts a new backfill. Existing checkpoints take precedence over a changed initial-lookback value. Run each profile/stream scope on one active collector. Use an initial time range that includes successful collection.

## Verify before relying on the dashboards

1. Open **Collector health** and select the intended profile. Verify recent successful connection and stream records, a reasonable heartbeat age, and lag consistent with cadence and backfill.
2. Check raw data and the configured index scope:

```spl
`zabbix_events`
| stats count latest(_time) AS latest_event BY sourcetype instance
| convert ctime(latest_event)
```

3. Compare one known event/audit record against Zabbix. Confirm permissions and retention, rather than treating an empty result as a healthy complete inventory.
4. Check Operations, Audit and Inventory. Metrics requires a scoped metric input; agent evidence requires actual forwarded logs.
5. Optionally enable data-model acceleration after checking index scope and storage capacity. Models are `Zabbix_Operations` and `Zabbix_Security`; acceleration starts disabled and is not required for the dashboards to run.

## Add agent execution evidence

Use `zabbix_vision/examples/agent-execution-logging.conf` and `forwarder-inputs.conf` as reviewed examples. Enable the applicable remote-command logging setting and configure an actual file, journald or container-log forwarding path. Do not broaden remote-command execution permissions merely to collect logs. For UserParameter/plugin subprocesses and descendant processes, use your existing auditd/Sysmon/EDR pipeline. See [coverage details](../docs/COVERAGE.md).

## Upgrade, backup, rollback and removal

Back up `local/`, checkpoint state and Splunk's supported credential/key backups before upgrading. Install a later archive over the same app directory, preserve `local/`, restart and repeat the verification checks. For rollback, disable inputs, restore the compatible prior package and its matching configuration/state backup through your change process, then verify before resuming. Replays may occur; deduplicate by `instance,event_uid`. Do not copy encrypted secrets between unrelated Splunk instances.

For prototype migration, disable the old `zabbix_connect` inputs before enabling the corresponding `zabbix_vision` inputs, re-enter tokens through the new setup page, and plan backfill. No automatic profile/checkpoint migration is provided. Historical events remain searchable in their existing indexes.

For removal, disable inputs and monitors first, follow Splunk's supported app-removal process, and decide separately how to retain indexed data, backups and app-scoped credentials. Removing an app does not delete indexed history.
