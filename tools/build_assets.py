"""Generate deterministic Splunk data models and Simple XML dashboards."""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1] / "zabbix_vision"


def write(path, text):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


def model(name, display, objects):
    data = {"modelName": name, "displayName": display, "description": display,
            "objectSummary": {}, "objects": []}
    for objname, constraint, fields in objects:
        base = [{"fieldName": field, "displayName": field.replace("_", " ").title(),
                 "type": kind, "owner": objname, "fieldSearch": field + "=*", "required": False,
                 "multivalue": False, "hidden": False, "editable": True, "comment": ""}
                for field, kind in fields.items()]
        data["objects"].append({"objectName": objname, "displayName": objname,
            "parentName": "BaseEvent", "lineage": [objname], "fields": base,
            "constraints": [{"search": constraint, "owner": objname}],
            "calculations": [], "objectType": "event"})
    write("default/data/models/" + name + ".json", json.dumps(data, indent=2) + "\n")


common = {"instance": "string", "event_uid": "string", "dataset": "string", "status": "string", "dest": "string"}
model("Zabbix_Operations", "Zabbix Operations", [
    ("Events", "`zabbix_index` sourcetype=zabbix:events", dict(common, severity="string", eventid="string", name="string")),
    ("Collector", "`zabbix_index` sourcetype=zabbix:collector", {"instance": "string", "stream": "string", "status": "string", "count": "number", "lag_seconds": "number", "duration_seconds": "number", "input_name": "string"}),
    ("History", "`zabbix_index` sourcetype=zabbix:history", dict(common, itemid="string", value="number", value_type="number")),
])
model("Zabbix_Security", "Zabbix Security", [
    ("Audit", "`zabbix_index` sourcetype=zabbix:audit", dict(common, action="string", user="string", src="string", resource="string", resource_name="string", category="string", recordsetid="string")),
    ("Execution", "`zabbix_index` sourcetype=zabbix:execution", {"instance": "string", "user": "string", "scriptid": "string", "hostid": "string", "status": "string", "request_id": "string"}),
])


def search(query):
    return '<search><query>' + escape(query) + '</query><earliest>$time.earliest$</earliest><latest>$time.latest$</latest></search>'


def panel(title, query, kind="table", options=""):
    if kind == "table":
        options = '<option name="count">5</option><option name="wrap">false</option>' + options
    return '<panel><title>' + escape(title) + '</title><' + kind + '>' + search(query) + options + '</' + kind + '></panel>'


def page(name, title, subtitle, rows, note=""):
    text = '<form version="1.1" theme="light" stylesheet="zabbix.css"><label>' + escape(title) + '</label>'
    text += '<description>' + escape(subtitle) + '</description><fieldset submitButton="false">'
    text += '<input type="time" token="time"><label>Time range</label><default><earliest>-24h@h</earliest><latest>now</latest></default></input>'
    text += '<input type="dropdown" token="instance" searchWhenChanged="true"><label>Zabbix instance</label><choice value="*">All instances</choice><default>*</default><fieldForLabel>instance</fieldForLabel><fieldForValue>instance</fieldForValue><search><query>`zabbix_events` earliest=-7d | stats count by instance | fields instance</query></search></input></fieldset>'
    text += '<row><panel><html><div class="zbx-banner"><span class="zbx-eyebrow">ZABBIX VISION / ' + escape(name.upper()) + '</span><h2>' + escape(title) + '</h2><p>' + escape(subtitle) + '</p></div></html></panel></row>'
    if note:
        text += '<row><panel><html><p class="zbx-note">' + escape(note) + '</p></html></panel></row>'
    text += ''.join('<row>' + ''.join(row) + '</row>' for row in rows) + '</form>\n'
    write('default/data/ui/views/' + name + '.xml', text)


raw = '`zabbix_events` instance=$instance|s$'
line = '<option name="charting.chart">line</option><option name="charting.chart.showMarkers">false</option>'
bar = '<option name="charting.chart">bar</option>'
single = '<option name="underLabel">selected time range</option>'
page('overview', 'Operations overview', 'From infrastructure health to the events that need your attention.', [
    [panel('Unique events', '| tstats dc(Events.event_uid) AS events FROM datamodel=Zabbix_Operations.Events WHERE Events.instance=$instance|s$', 'single', single),
     panel('High / disaster events', '| tstats dc(Events.event_uid) AS events FROM datamodel=Zabbix_Operations.Events WHERE Events.instance=$instance|s$ (Events.severity=high OR Events.severity=disaster)', 'single', single),
     panel('Collectors reporting errors', raw + ' sourcetype=zabbix:collector | stats latest(status) AS status by instance input_name stream | where status="error" | stats count', 'single', single)],
    [panel('Event activity', '| tstats dc(Events.event_uid) AS events FROM datamodel=Zabbix_Operations.Events WHERE Events.instance=$instance|s$ BY _time span=1h Events.severity | rename Events.severity AS severity | timechart span=1h sum(events) by severity', 'chart', line),
     panel('Affected hosts', raw + ' sourcetype=zabbix:events | dedup event_uid | stats count by dest | sort -count | head 12', 'chart', bar)],
    [panel('Recent problems and recoveries', raw + ' sourcetype=zabbix:events | dedup event_uid | table _time instance dest severity status name eventid | sort -_time')]
])
page('security', 'Audit & authentication', 'Trace access, failed logins, configuration changes, and administrative activity.', [
    [panel('Failed logins', '| tstats dc(Audit.event_uid) AS failures FROM datamodel=Zabbix_Security.Audit WHERE Audit.instance=$instance|s$ Audit.action=failed_login', 'single', single),
     panel('Successful logins', '| tstats dc(Audit.event_uid) AS logins FROM datamodel=Zabbix_Security.Audit WHERE Audit.instance=$instance|s$ Audit.action=login', 'single', single),
     panel('Changes', '| tstats dc(Audit.event_uid) AS changes FROM datamodel=Zabbix_Security.Audit WHERE Audit.instance=$instance|s$ Audit.category=change', 'single', single)],
    [panel('Authentication activity', '| tstats dc(Audit.event_uid) AS events FROM datamodel=Zabbix_Security.Audit WHERE Audit.instance=$instance|s$ Audit.category=authentication BY _time span=1h Audit.action | rename Audit.action AS action | timechart span=1h sum(events) by action', 'chart', line),
     panel('Failed login sources', raw + ' sourcetype=zabbix:audit action=failed_login | dedup event_uid | stats count values(user) AS users by src | sort -count')],
    [panel('Audit trail', raw + ' sourcetype=zabbix:audit | dedup event_uid | spath input=_raw path=raw.details output=details | table _time instance user src action resource resource_name recordsetid details | sort -_time')]
], 'Audit collection needs a Zabbix Super admin token with auditlog.get permission and audit logging enabled. API-token use is not a complete access log; forward frontend/proxy and identity-provider logs separately.')
page('inventory', 'Infrastructure inventory', 'Inspect the latest complete inventory snapshots for each connected server.', [
    [panel('Latest host inventory', raw + ' (sourcetype=zabbix:hosts OR (sourcetype=zabbix:snapshot snapshot_dataset=hosts)) | eventstats max(_time) AS last_snapshot by instance | where _time=last_snapshot AND dataset="hosts" | table instance dest name status raw.interfaces{}.* raw.inventory.*'),
     panel('Current problems (latest complete snapshot)', raw + ' (sourcetype=zabbix:problems OR (sourcetype=zabbix:snapshot snapshot_dataset=problems)) | eventstats max(_time) AS last_snapshot by instance | where _time=last_snapshot AND dataset="problems" | table instance severity name acknowledged eventid raw.tags{}.*')],
    [panel('Unsupported items', raw + ' (sourcetype=zabbix:items OR (sourcetype=zabbix:snapshot snapshot_dataset=items)) | eventstats max(_time) AS last_snapshot by instance | where _time=last_snapshot AND dataset="items" AND \'raw.state\'="1" | table instance dest itemid name key_ raw.error'),
     panel('Proxies / services / SLA / maintenance', raw + ' (sourcetype=zabbix:proxies OR sourcetype=zabbix:services OR sourcetype=zabbix:sla OR sourcetype=zabbix:maintenance) | sort 0 -_time | dedup instance dataset object_id | table _time instance dataset name raw')]
], 'Inventory panels use snapshot completion markers. Choose a range containing a recent successful snapshot; absence of rows is not proof of health. SLA records are definitions, not computed SLI percentages.')
page('metrics', 'Metrics & trends', 'Explore explicitly scoped item history and closed-hour trend aggregates.', [
    [panel('Numeric history', raw + ' sourcetype=zabbix:history (value_type=0 OR value_type=3) | dedup event_uid | eval series=instance.":".itemid | timechart span=5m avg(value) by series limit=12', 'chart', line)],
    [panel('Hourly trends', raw + ' sourcetype=zabbix:trends | dedup event_uid | eval series=instance.":".itemid | timechart span=1h avg(value_avg) by series limit=12', 'chart', line)],
    [panel('Log / text item history', raw + ' sourcetype=zabbix:history (value_type=1 OR value_type=2 OR value_type=4) | dedup event_uid | table _time instance itemid value raw.source raw.severity raw.logeventid')]
], 'Configure item IDs in a dedicated input. Numeric, character, log and text history are supported; binary history is opt-in on Zabbix 7.0+. History values may contain sensitive operational data.')
page('execution', 'Scripts & agent activity', 'Correlate requested executions, Zabbix command operations, and agent-side evidence.', [
    [panel('Manual executions recorded by Zabbix', raw + ' sourcetype=zabbix:audit action=execute | dedup event_uid | spath input=_raw path=raw.details output=details | table _time instance user src resource resource_name recordsetid details')],
    [panel('Automated remote-command operations', raw + ' sourcetype=zabbix:alerts raw.alerttype=1 | dedup event_uid | table _time instance eventid alertid status raw.actionid raw.esc_step raw.retries'),
     panel('Executions requested from Splunk', raw + ' sourcetype=zabbix:execution | stats latest(status) AS status min(_time) AS started by instance user scriptid hostid request_id | convert ctime(started)')],
    [panel('Agent command evidence', '`zabbix_events` (sourcetype=zabbix:agent OR sourcetype=zabbix:agent2 OR sourcetype=zabbix:server) command=* | table _time host source command | sort -_time')]
], 'Agent records use host identity and are not filtered by the API instance selector. Enable LogRemoteCommands (agent) or Plugins.SystemRun.LogRemoteCommands (agent 2), then forward their logs. UserParameter/plugin child processes also require OS process auditing for complete execution coverage.')
page('collector', 'Collector health', 'See API failures, ingestion delay, collection volume, and missing heartbeats.', [
    [panel('Latest stream health', raw + ' sourcetype=zabbix:collector | stats latest(status) AS status latest(error) AS error latest(lag_seconds) AS lag_seconds latest(count) AS rows latest(duration_seconds) AS duration_seconds max(_time) AS last_seen by instance input_name stream | eval heartbeat_age_seconds=now()-last_seen | convert ctime(last_seen)')],
    [panel('Collection volume', '| tstats sum(Collector.count) AS rows FROM datamodel=Zabbix_Operations.Collector WHERE Collector.instance=$instance|s$ BY _time span=15m Collector.stream | rename Collector.stream AS stream | timechart span=15m sum(rows) by stream', 'chart', line),
     panel('Collection delay', raw + ' sourcetype=zabbix:collector | timechart span=15m max(lag_seconds) by instance', 'chart', line)]
], 'No heartbeat can mean a disabled input or stopped Splunk. Configure the supplied saved searches and the external Zabbix agent health check. Errors retain the affected checkpoint; other streams continue.')

print('Generated data models and six dashboards.')
