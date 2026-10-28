# Zabbix Vision for Splunk: Operations, Access and Agent Activity in One Investigation

The API connection is the easy part. The harder questions are whether a newer Zabbix release still accepts the token, whether an audit response was truncated, and whether the command on an agent is represented in the data you collected.

I built Zabbix Vision for Splunk around those questions. It collects Zabbix operations and audit records, provides a place to search forwarded agent command logs, and exposes its own collection health. The initial public release is 1.0.0 beta.

This article explains the decisions behind the app, the deployment path and the evidence behind its compatibility claims. The [source and installation guide](https://github.com/majidershadi/zabbix-vision-for-splunk) and [release package](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0) are on GitHub.

## Start with the questions an operator asks

An infrastructure dashboard can tell you that a trigger fired. During an investigation, the next questions usually cross several systems: who changed the item, whether an account failed to log in, which action issued a remote command, and whether the agent recorded it.

Those are related questions, but their evidence comes from different places. Trigger events are not configuration audit records. A remote-command alert operation is not a complete process tree. A token being used to call the API does not imply a fresh login event for each request.

Zabbix Vision keeps those distinctions visible. Six dashboards cover operations, authentication/change audit, infrastructure snapshots, scoped metrics, script/agent activity and collector health. The goal is to make the available evidence easier to investigate without presenting missing evidence as certainty.

## A frontend path is configuration, not an assumption

Zabbix may be served from the root of a domain, from `/zabbix`, or from a path chosen by a reverse proxy. A collector that always appends `/zabbix` will work in one environment and fail in another.

The connection profile accepts the frontend path or the complete `api_jsonrpc.php` URL. A root address becomes a root API endpoint; a nested address keeps its prefix. The client does not probe a list of guessed paths with a live token. It also refuses redirects, which makes an incorrectly configured proxy visible and avoids forwarding credentials to an unexpected destination.

Version discovery is unauthenticated. Once the version is known, automatic mode uses legacy JSON-body authentication for the 6.0/6.2 generation and Bearer authentication from 6.4 onward. It rejects body authentication on 7.2 and later. A reverse proxy must preserve the Authorization header for the newer path.

## Certificate controls belong beside the URL

Transport policy is part of a connection's identity. The default is verified HTTPS, including the hostname. Administrators can supply a custom CA bundle, client certificate and private key for mutual TLS, an optional encrypted-key passphrase and a minimum TLS version. An explicit HTTP CONNECT proxy is supported; authenticated proxy URLs are not.

Certificate and key paths refer to files on the collector. Saving a path does not upload a key from the browser. File ownership and directory permissions still matter, especially when a heavy forwarder runs under a service account. HTTP and disabled verification exist as explicit isolated-lab choices, rather than settings an operator should need for a normal production deployment.

The test suite exercises actual TLS handshakes for custom trust, untrusted certificates, hostname mismatch and mutual TLS with an encrypted private key. That is more useful than only testing whether a checkbox produces a configuration value.

## Let Splunk own secret encryption

The API token and optional key passphrase use Splunk's app-scoped `storage/passwords` endpoint. Profiles and inputs contain configuration references rather than a clear-text token. Saved secrets are not read back into the setup form.

Splunk performs the encryption with its own `splunk.secret`. New writes use `$8$` on Enterprise 10.6 and later and `$7$` on earlier releases. The app checks the prefix where the native response exposes it; it does not implement a competing encryption format or relabel old ciphertext.

The evidence matters here: `$7$` was verified on a running 10.4.1 instance. The 10.6+ branch follows Splunk's documented native behavior and has version/response test coverage, but was not validated on a running 10.6+ server. Upgrading Splunk does not automatically convert every old credential. Use Splunk's supported migration and backup procedure, and re-enter credentials when moving between instances.

## Collection has to know when it may be incomplete

A fixed row limit is a useful API safeguard. Treating every response below an arbitrary maximum as a complete history is much less useful. If many audit records share one timestamp, advancing a checkpoint to that timestamp can skip records that were never returned.

The collector queries bounded inclusive time ranges and splits them when the response reaches the configured limit. History scopes can also split by item IDs. If one second for one remaining scope still reaches the limit, collection fails visibly and retains that checkpoint. The operator can increase the page size or narrow scope, with evidence of what stopped.

Checkpoints are atomic and independent by stream. A failed audit call should not prevent a host inventory snapshot from being collected. A recent overlap catches late arrivals and changes to mutable records; nanoseconds and value type distinguish history samples that share a second.

This is at-least-once output to Splunk's modular-input stream, not a transactional indexing acknowledgement. A crash can cause replay. Stable event IDs allow replay-tolerant counts, while changes arriving outside the overlap require explicit reconciliation.

## Current inventory needs a different search from historical events

The last problem you observed is not necessarily the problem that exists now. A successful snapshot containing zero problems is meaningful. Without a completion marker, an empty result can leave a dashboard showing yesterday's problem indefinitely.

Snapshots therefore include completion markers, even when they contain no rows. Inventory searches use the latest complete snapshot within the chosen time range. A failed collection does not produce a reassuring empty snapshot.

There are eighteen streams in the release. The API coverage includes audit, trigger events, current problems, hosts, items, triggers, groups, templates, proxies, services, SLA definitions, maintenance, alert operations, discovery, autoregistration, internal events and explicitly scoped history/trends. SLA definitions do not claim to be calculated SLI percentages. Trends exclude the current incomplete hour.

Use separate input cadences. Low-change inventory can run every five or fifteen minutes, while events need a shorter interval. Metric collection requires item IDs so that enabling a stream does not accidentally ask for every history value in the estate.

## Data models help the searches that fit them

Two custom models organize the data: `Zabbix_Operations` for events, collector records and history, and `Zabbix_Security` for audit and app execution. Count and time-series panels can use `tstats`; long audit details and latest-snapshot questions use scoped raw searches.

Acceleration is off by default. An administrator can set index scope, estimate storage and enable summaries when appropriate. Dashboard queries use both summarized and unsummarized data, so a new installation can answer searches before summaries complete. There is no claim that every query becomes faster or that acceleration has been benchmarked for every workload.

```spl
| tstats dc(Audit.event_uid) AS events
  FROM datamodel=Zabbix_Security.Audit
  WHERE Audit.category=authentication
  BY Audit.instance Audit.action Audit.user
```

The collection-health dashboard is equally important. It shows latest stream status, collection delay, duration and heartbeat age. The companion health utility can be called from a Zabbix agent UserParameter so the collector is monitored outside its own Splunk dashboard.

## Agent execution requires agent evidence

The app correlates four useful sources: Zabbix manual-execution audit, automated remote-command alert operations, executions requested from the app and forwarded agent/server logs.

Classic agents support `LogRemoteCommands`; agent 2 uses `Plugins.SystemRun.LogRemoteCommands`. Enabling those settings does not forward the file, so the deployment guide also provides input examples. Do not broaden `AllowKey=system.run[*]` simply to obtain visibility. Preserve the execution policy and collect the evidence the agent already has permission to produce.

Local UserParameter commands, plugin processes and descendants may not appear in those remote-command logs. For host-level completeness, use Linux auditd, Windows Sysmon or an existing EDR process tree. Web/proxy logs and identity-provider logs fill different authentication/access gaps. The app documents those boundaries rather than implying the API can answer all of them.

## A deliberately narrow execution path

Optional execution accepts an existing Zabbix script ID and host ID. It requires a separate Splunk capability, an enabled profile, both allowlists and explicit confirmation. The requesting user's session is used; Zabbix still applies the token's own permissions.

The app writes its request audit before execution, records the outcome and suppresses output. It never automatically retries a command. A network timeout means the result may be unknown, so the request UUID and Zabbix/agent logs should be checked before another run.

One live test also exposed a less obvious leak path: Zabbix can include script output inside its audit details. The final implementation redacts that field as well. Protecting an execution response is incomplete if the same output is copied into a different collection stream moments later.

## How it was built and tested

This is an original standard-library Python implementation integrated with Splunk's modular-input and persistent REST interfaces. A small existing Zabbix add-on was inspected for behavior, including its fixed prefix, body token and timestamp checkpoint. Its code is not bundled. The broader design grew around the compatibility and operational questions those choices raised.

Core live testing used Splunk Enterprise 10.4.1 and disposable official Zabbix 6.0.49, 7.0.32 and 7.4.16 stacks. All sixteen nonmetric streams succeeded on each. Scoped history/trend calls and numeric history were exercised on 7.4. The suite contains 33 automated tests, and all 32 generated dashboard/selector searches dispatched successfully in Splunk.

A harmless predefined script executed on a disposable agent through the app. Splunk recorded requested/completed audit entries and a matching agent command record. Temporary test capability changes were restored and execution was disabled after the test. The log import was a snapshot for acceptance testing, not a claim that a permanent Docker log pipeline was installed.

The public app ID is `zabbix_vision`, renamed from the private prototype for release. The guide explains its credential/checkpoint namespace and first-run setup. Local AppInspect is part of preparing the package; marketplace review and Cloud certification remain separate processes. The [validation record](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/docs/VALIDATION.md) states what was tested and what was not.

## Deploy it with a small, verifiable scope

Start with one collector, a dedicated token and a few streams. Set the index macro, test the profile, inspect collector health and compare one known event with Zabbix. Add slower inventory and a small metric scope after that path works. Give audit collection its required permissions deliberately, and keep retention longer than the outage you intend to recover from.

The [release](https://github.com/majidershadi/zabbix-vision-for-splunk/releases/tag/v1.0.0) contains the install archive and checksum. The [repository](https://github.com/majidershadi/zabbix-vision-for-splunk) includes configuration, search, architecture, troubleshooting and coverage guides, plus Splunkbase submission materials. This initial beta is intended for deployment-specific acceptance before wider use.

Related engineering work: [REST Profiler](https://majidershadi.github.io/articles/rest-profiler-1-1/), [VMware Vision](https://github.com/majidershadi/vmware-vision), and [building secure Splunk apps](https://majidershadi.github.io/articles/building-secure-splunk-apps/).
