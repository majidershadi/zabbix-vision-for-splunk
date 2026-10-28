[zabbix_vision://<name>]
profile = <string>
* Required connection profile stored in zabbix_vision_connections.conf.
streams = <comma-separated strings>
* audit,events,problems,hosts,items,triggers,hostgroups,templates,proxies,services,sla,maintenance,alerts,history,trends,discovery,autoregistration,internal
interval = <integer>
* Polling interval in seconds; minimum 10, default 60.
index = <string>
* Existing destination index. Default main.
page_size = <integer>
* API response row limit. Default 1000. Full windows are bisected; saturated seconds stop with an error.
lookback = <integer>
* Initial history in seconds. Default 3600.
overlap = <integer>
* Revisit this many seconds for late data/updates. Default 120.
settle_delay = <integer>
* Delay before collecting recent data. Default 10 seconds.
window = <integer>
* Backfill window in seconds per poll. Default 3600.
item_ids = <comma-separated IDs>
* Required for history and trends. Limit to needed items.
history_types = <comma-separated integers>
* 0 float, 1 string, 2 log, 3 unsigned, 4 text, 5 binary. Default 0,1,2,3,4.
snapshot_limit = <integer>
* Maximum inventory rows. Default 100000. A full result raises an overflow error.
disabled = <boolean>
* Disable this input.
