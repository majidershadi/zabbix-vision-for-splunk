# Authentication and agent execution coverage

For concrete OS collection and search examples, read [Detecting UserParameter execution](USERPARAMETER_EXECUTION.md). Version 1.0.0 does not automatically collect or normalize auditd/Sysmon process records into its agent-command panel; those sources require separate forwarding and searches.

| Activity | Collection source | Meaning and limitations |
| --- | --- | --- |
| Frontend/API user login, failed login, logout | `auditlog.get`, actions 8/9/4 | Zabbix-recorded authentication events; token usage does not imply a login event per call |
| Role, user, authentication, API-token configuration changes | `auditlog.get` | Actor/IP/resource/recordset and structured changes; sensitive fields are redacted |
| Manual execution through Zabbix | Audit action 7 | Audit evidence depends on Zabbix settings and operation type |
| Automated action remote commands | `alert.get`, `alerttype=1` | Operation status and event/action IDs; not full stdout/stderr or exhaustive process history |
| Commands requested from this app | `zabbix:execution` | Requested and completed/failed-or-unknown records; caller, profile, host/script IDs, correlation UUID |
| Remote `system.run` on classic agents | `LogRemoteCommands=1` + agent logs | Agent-side command text; failed/disallowed commands and subprocess outcomes may need other logs |
| Remote `system.run` on agent 2 | `Plugins.SystemRun.LogRemoteCommands=1` + agent logs | Does not log locally invoked HostMetadataItem/HostInterfaceItem/HostnameItem commands |
| UserParameter, plugin and script subprocesses | Linux auditd or Windows Sysmon/Security process creation | Required for complete host-level execution visibility; correlate parent chain to Zabbix service |
| Frontend HTTP/API request access and proxy denials | Web server / reverse proxy access/error logs | Configure request method/path/status and authenticated user where available; never log Authorization headers |
| SAML/LDAP/MFA provider decisions | Identity-provider logs | Events not necessarily mirrored in Zabbix audit |

## Agent logging

Deploy the applicable setting from `examples/agent-execution-logging.conf` to each agent and forward its file with the supplied `forwarder-inputs.conf` examples. A Windows service's log location can differ from the default path. Container stdout/journald needs a container/journal collector instead of file monitors.

Do not enable broad `AllowKey=system.run[*]` merely to obtain visibility. Preserve the agent's existing execution policy. Log records and script arguments may contain sensitive business data; use restricted indexes, appropriate retention and redaction at the source.

## Linux execution audit

Use the existing Splunk Linux/auditd integration. For hosts where Zabbix runs as a dedicated service UID, a site-specific rule can capture its exec calls, for example:

```text
# Substitute the actual numeric service UID. Review volume before deploying.
-a always,exit -F arch=b64 -S execve,execveat -F euid=ACTUAL_ZABBIX_UID -k zabbix_exec
```

Add a compatible 32-bit rule only where relevant. This records processes running under that effective UID; privilege changes, sudo and daemonized descendants may need broader rules or an EDR process tree. Audit EXECVE/SYSCALL/PROCTITLE records share audit serial IDs and must be correlated, not treated as one command per raw record.

## Windows execution audit

Use Sysmon Event ID 1 or Security 4688 with command-line auditing enabled. Forward with your existing Splunk Windows add-on. Correlate `ParentProcessGuid` / `ProcessGuid` across descendants of `zabbix_agentd.exe` or `zabbix_agent2.exe`; checking only the immediate parent misses grandchildren. Service-account filtering alone can include unrelated applications.

## App-controlled execution

An administrator must explicitly grant `zabbix_execute_scripts`, enable execution on the connection, and provide both script and host ID allowlists. The app uses the requesting user's Splunk session, not a system session. Zabbix independently checks the API token's role and host/script permissions.

The predefined Zabbix script determines whether execution happens on an agent, server or proxy. This app does not take arbitrary command text, manualinput, or URL scripts. It suppresses script output to avoid copying secrets into the UI/index. Requests are never automatically retried. A network timeout is **unknown**, so investigate the request UUID and Zabbix/agent logs before rerunning.

Monitor the execution audit file and Splunk's own `_audit` as part of your normal operational controls. An administrator with filesystem access can alter local logs; use centralized forwarding/retention when tamper resistance is needed.
