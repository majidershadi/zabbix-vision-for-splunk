# Install Zabbix Vision for Splunk

## Choose the collector

Use a Linux Splunk Enterprise instance with outbound HTTPS access to the Zabbix frontend. A standalone search head can collect in a small installation; use one heavy forwarder for production collection and install search knowledge on the search heads. Universal forwarders cannot run this modular input. Enable each collection scope on one collector only.

The live acceptance environment is Splunk Enterprise 10.4.1. The implementation targets 9.4+ and 10.x, with Python 3.9-compatible syntax; other Splunk releases require acceptance testing. Cloud deployment and search-head clusters are not certified.

## Install

1. Download `zabbix_vision-1.0.0.tar.gz` and its SHA-256 file from [GitHub Releases](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0).
2. Verify the checksum. The GitHub source ZIP is not the install package.
3. In Splunk, use **Apps → Manage Apps → Install app from file**. Select the archive and restart Splunk.
4. Create your destination index, grant the appropriate search roles access, and set the `zabbix_index` macro in `local/macros.conf`. The default is `index=main`.
5. Open **Zabbix Vision for Splunk → Administration → Connections & collection** as an administrator.
6. Save a profile with its frontend URL and API token, then select **Test saved connection**.
7. Create an input. Start with `audit,events,problems,hosts,alerts`, a 60-second interval and an initial lookback matching your retention.
8. Open Collector health. Check each selected stream and its lag, then verify a known event against the original Zabbix record.

For production, keep low-change inventory in a separate 300–900-second input. History/trends need a separate input with explicit item IDs. Input names are checkpoint identities; changing a name starts a new backfill.

## Index configuration

```ini
# local/macros.conf on the search tier
[zabbix_index]
definition = index=zabbix
```

Set each collection input's destination index to `zabbix`. The app's own execution log monitor defaults to `main`; override its `index` under the existing monitor stanza in `local/inputs.conf` as well. Forwarded agent/server logs must be in the macro's search scope. For several indexes, use a properly parenthesized index expression in the macro and grant access to each index.

The app exports parsing/field knowledge for its sourcetypes. Deploy the corresponding props/transforms to the parsing and search tiers in a distributed environment. Installing a profile on a search head does not configure a remote collector.

## Upgrade and removal

Back up `local/`, checkpoint files and Splunk's supported secret/key backups. Install a later archive over the same `zabbix_vision` directory and restart. Keep `local/` out of public packages. Disable inputs before removing the app; indexed events remain governed by index retention.

The private prototype was named `zabbix_connect`. This public app uses `zabbix_vision`, a different app/credential namespace. Disable prototype inputs before enabling the new app, re-enter tokens through Setup, and plan the backfill. Do not copy native encrypted values across Splunk instances or hand-edit their format. Historical prototype events keep their original sourcetypes and remain searchable in the selected indexes.
