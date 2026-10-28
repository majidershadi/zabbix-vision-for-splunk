# Dashboards, data models and search

Six dashboards cover Operations overview, Audit & authentication, Infrastructure inventory, Metrics & trends, Scripts & agent activity and Collector health. Time and instance selectors apply to API-derived records. Agent log panels use host identity and explicitly do not apply the API instance selector.

## Models

| Model | Objects | Intended use |
| --- | --- | --- |
| Zabbix_Operations | Events, Collector, History | Event counts, collection volume and numeric history |
| Zabbix_Security | Audit, Execution | Access/change activity and app-requested execution |

Acceleration is disabled by default. After setting index scope, enable acceleration under Settings → Data models if useful; defaults are seven days for operations and 30 days for security. Estimate summary storage and rebuild summaries after index/field changes. Panels use summaries and unsummarized data, so they work before acceleration completes. No acceleration performance benchmark is claimed.

```spl
| tstats dc(Audit.event_uid) AS events
  FROM datamodel=Zabbix_Security.Audit
  WHERE Audit.category=authentication
  BY Audit.instance Audit.action Audit.user
```

```spl
`zabbix_events` sourcetype=zabbix:audit
| dedup instance event_uid
| spath input=_raw path=raw.details output=details
| table _time instance user src action resource resource_name recordsetid details
```

```spl
`zabbix_events` sourcetype=zabbix:execution
| stats min(_time) AS started latest(status) AS status
  BY instance user scriptid hostid request_id
```

Use `event_uid` for replay-tolerant counts. Inventory uses complete snapshot markers, including zero-row snapshots, rather than interpreting the last historical problem as a current problem. Choose a time range containing a recent successful snapshot. An inaccessible or failed stream is not an empty healthy snapshot.

The CIM-related Authentication/Change tags are search mappings, not certification of complete Enterprise Security coverage. API-token use is not a login per request. Pair audit records with web/proxy/identity-provider logs when that question matters.
