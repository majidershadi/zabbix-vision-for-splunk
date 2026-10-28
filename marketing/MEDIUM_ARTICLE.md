# Zabbix Vision for Splunk: A Clearer Trail from Monitoring to Investigation

A trigger fires in Zabbix. The next question is often about something else: a configuration change, a failed login, an automated action or a command on the agent.

That is the gap I wanted Zabbix Vision for Splunk to address. It brings Zabbix operations and audit records into Splunk, adds investigation dashboards and provides a place to search forwarded agent command evidence. The first public beta is 1.0.0.

The [full engineering article](https://majidershadi.github.io/articles/zabbix-vision-for-splunk/) goes deeper into the implementation. The [GitHub repository](https://github.com/majidershadi/zabbix-vision-for-splunk) contains the source and guide, and the [release page](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0) contains the install package and checksum.

## The connection needs more than a token field

A simple collector usually starts with a URL, an API token and a loop. That can be enough for a demonstration. It becomes harder to maintain when the frontend lives behind a custom proxy path, the certificate comes from an internal CA or the next Zabbix release expects a different authentication mechanism.

Zabbix Vision accepts the actual frontend path or full API endpoint. Root, `/zabbix` and nested prefixes are all configuration choices. The client discovers the version before choosing legacy body authentication or a Bearer header. It rejects body authentication on 7.2 and later, and refuses redirects instead of following them with a token.

Profiles also expose CA verification, custom trust, client certificate/key files for mutual TLS, a separately stored key passphrase, minimum TLS and an explicit HTTP CONNECT proxy. Verified HTTPS is the default.

The token goes into native Splunk secure storage. Splunk owns the encryption format: new writes use `$8$` on 10.6+ and `$7$` on earlier releases. I verified `$7$` on a running 10.4.1 server; the 10.6+ behavior follows the platform and has fixture coverage, with live 10.6+ testing still pending. That distinction belongs in the release notes.

## A missing record can be more dangerous than a visible error

An audit API has a row limit. If a collector gets a full page and advances its timestamp anyway, it can miss records that share the same second. Nothing has to crash for the resulting history to be incomplete.

The collector splits bounded time windows when a response reaches its limit. For history it can split the item scope too. A saturated single second is an explicit failure with a retained checkpoint, so an operator can increase the limit or narrow the scope without the collector quietly skipping ahead.

Recent overlap catches late arrivals and changes to mutable records. Event identities help tolerate replay. Checkpoints advance after output, but the collector does not pretend that output and Splunk indexing form one transaction. A crash can replay data, and changes outside the overlap require deliberate reconciliation.

Current-state data needs another rule. An empty successful problem snapshot should clear the picture of current problems. Completion markers make that result visible, instead of leaving the last historical problem on screen forever.

## Six dashboards, with collection health in view

The release includes operations, audit/authentication, infrastructure inventory, metrics/trends, script/agent activity and collector health dashboards.

Two data models support `tstats` for the count and time-series questions that fit it. Raw searches handle structured audit details and latest snapshots. Acceleration is optional and starts disabled so the administrator can choose the index scope and summary storage.

There are eighteen collection streams, including operational events, audit records, current problems, inventory, alert operations, discovery/internal events and scoped history/trends. Metric collection needs explicit item IDs; it is not an invitation to ingest the entire history database by accident. Low-change inventory should run more slowly than event collection.

The collector itself emits stream status and lag. A small health utility can also be exposed through a Zabbix agent UserParameter. Monitoring should be able to tell you when its own bridge has stopped reporting.

## Agent activity is a separate evidence source

This is the boundary I would want to understand before installing any integration: the API cannot describe every process an agent starts.

Zabbix audit records can show a manual execution. Alert operations can show an automated remote-command operation. Agent logs can add command text when the appropriate remote-command logging is enabled. Those are useful sources, but they are not interchangeable.

For classic agents, review `LogRemoteCommands`; agent 2 uses `Plugins.SystemRun.LogRemoteCommands`. Forward the actual log through your existing collection pipeline. Keep the current execution policy rather than enabling broad `system.run` access for the sake of logging.

Local UserParameter commands, plugin processes and descendants may need Linux auditd, Windows Sysmon or an EDR process tree. Frontend access and identity-provider decisions can need web/proxy and identity logs too. The guide explains those gaps because an empty panel is not evidence that nothing happened.

## Optional execution stays narrow

The app can request a predefined Zabbix script, but only after separate authorization and configuration: an execution capability, an enabled profile, both script and host allowlists and explicit confirmation. It accepts IDs, not arbitrary command text.

Requests are audited before the call. Output is suppressed and commands are never automatically retried. A timeout leaves an outcome to investigate, not an instruction to run the command again.

Live testing revealed that Zabbix can also put script output into audit details. The final collector redacts that field. It is a useful reminder that sensitive output can reappear through a different stream even when the direct execution response is protected.

## What was tested

Core integration ran on Splunk Enterprise 10.4.1 with official disposable Zabbix 6.0.49, 7.0.32 and 7.4.16 stacks. All sixteen nonmetric streams succeeded on each. Scoped metric calls and numeric history were exercised on 7.4. The suite has 33 automated tests, including real TLS handshakes, and all 32 dashboard/selector searches passed in Splunk.

A harmless predefined command ran on a disposable agent through the app. Requested/completed audit records and the matching agent log were checked. Temporary test permissions were restored and execution was disabled afterward.

The initial release remains beta. Small lab success is not certification of every deployment or resource scenario, and local inspection is separate from Splunkbase review. The [validation guide](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/docs/VALIDATION.md) records the evidence and remaining gaps.

## Start with one question you can verify

Install one collector, choose a dedicated token, select a few streams and compare a known record with Zabbix. Set the index macro and check collector health before adding a broader inventory or metric scope.

You can find the [installable release here](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0). The [repository](https://github.com/majidershadi/zabbix-vision-for-splunk) includes deployment, certificate, search, troubleshooting and agent coverage guides. The [longer article on my site](https://majidershadi.github.io/articles/zabbix-vision-for-splunk/) explains the engineering decisions behind them.

---

Publication notes — remove this section before publishing: use the website article as Medium's canonical URL. Suggested tags: Splunk, Zabbix, Observability, Cybersecurity, Open Source. Use the supplied image with an accurate conceptual-illustration caption. After publishing, record the real Medium permalink in BACKLINK_PLAN.md. This file is a prepared draft; no Medium publication is implied.
