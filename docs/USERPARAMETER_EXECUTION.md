# Detecting UserParameter execution

**Use operating-system process telemetry for execution evidence.** Zabbix Vision 1.0.0 does not automatically collect Linux auditd or Windows Sysmon records, and its agent-command panel is not a UserParameter detector. The searches below run against separately forwarded OS telemetry. They are deployment examples, not a new certified runtime feature or an end-to-end lab acceptance result.

Zabbix defines a UserParameter as a key mapped to a command; on UNIX it runs the command through `/bin/sh`. This means process telemetry can reveal the shell and its external children. A collected item definition or returned item value alone does not prove which local command executed. See [Zabbix User parameters](https://www.zabbix.com/documentation/current/en/manual/config/items/userparameters).

## What each source establishes

| Source | What it can establish | Remaining gap |
| --- | --- | --- |
| Zabbix item/API data | Item key, host and returned values, subject to permissions and retention | Does not return a universal per-invocation UserParameter process log or all agent-local configuration |
| Remote-command logging | Relevant remotely invoked `system.run` commands | Do not assume all UserParameter/plugin execution is included |
| Linux auditd exec telemetry | Execution attempts under the selected UID, executable, PID/PPID and argument records | Effective-UID changes, container mapping, shell builtins and missing ancestry need separate handling |
| Windows Sysmon Event ID 1 | Process command line and parent identity with process GUID correlation | Rules must retain descendants; direct-parent filtering alone misses grandchildren |
| Instrumented UserParameter wrapper | Explicit item key and invocation start/end, when designed and deployed correctly | Requires changing the command definition; is not tamper-proof evidence of every descendant |

Use process evidence plus a reviewed inventory of `host, userparameter_key, configured_command, configuration_version`. Classify a match as **Zabbix-related process activity** until the command/key mapping or an explicit wrapper record supports stronger attribution. Different keys can execute the same command. Zabbix's agent-2 remote-command setting is documented separately from UserParameter behavior in the [agent configuration reference](https://www.zabbix.com/documentation/7.4/en/manual/appendix/config/zabbix_agent2_win).

## Linux: collect exec events for a dedicated service identity

Identify the real agent service UID with `id -u zabbix` and verify the running service's identity. Do not assume the username, UID or container-to-host UID mapping. For a dedicated non-root service UID, review a rule such as:

```text
# Example only: replace ACTUAL_ZABBIX_UID with the verified numeric UID.
# Add to the site's existing audit rules; do not erase or replace other rules.
-a always,exit -F arch=b64 -S execve,execveat -F euid=ACTUAL_ZABBIX_UID -k zabbix_exec
```

On systems that support and run a 32-bit ABI, add the appropriate `arch=b32` counterpart after verifying supported syscalls. Use your distribution's supported persistent rule-loading procedure. Check `auditctl -l` and `auditctl -s`, including lost events/backlog, and verify a harmless known check with `ausearch -k zabbix_exec -ts recent -i`. An immutable audit policy needs the organization's normal reboot/change process; do not disable it to apply this example.

Do not add `auid>=1000` blindly: daemon processes can have an unset login UID. Do not select effective UID 0 as a substitute for ancestry on a root-running agent; that would capture broad root activity. Use your existing EDR/eBPF process tree or a carefully scoped site policy in that case. Audit rule syntax, architecture selection and correlation keys are described by the [Linux Audit project](https://github.com/linux-audit/audit-userspace/blob/master/docs/audit.rules.7).

Forward the existing audit log through the site's Linux/auditd integration to a restricted index. Preserve SYSCALL, EXECVE, PROCTITLE and related records. The key often appears on the SYSCALL record only, so filtering raw input to `key=zabbix_exec` before correlation can discard its arguments.

### SPL: correlate records for each audited execution

Substitute your actual index and sourcetype. This example keeps original argument records for investigation; it does not pretend hex-encoded or split EXECVE arguments have already been decoded.

```spl
index=YOUR_OS_INDEX sourcetype=YOUR_AUDIT_SOURCETYPE
  ("type=SYSCALL" OR "type=EXECVE" OR "type=PROCTITLE" OR "type=CWD")
| rex field=_raw "msg=audit\((?<audit_id>[0-9.]+:[0-9]+)\)"
| rex field=_raw "\bkey=\"?(?<audit_rule>[^\s\"]+)"
| rex field=_raw "\bexe=\"(?<process_exe>[^\"]+)\""
| rex field=_raw "\bpid=(?<process_pid>[0-9]+)"
| rex field=_raw "\bppid=(?<parent_pid>[0-9]+)"
| rex field=_raw "\beuid=(?<effective_uid>[0-9]+)"
| rex field=_raw "\bsuccess=(?<exec_success>[^\s]+)"
| where isnotnull(audit_id)
| stats min(_time) AS _time values(audit_rule) AS audit_rule
    values(process_exe) AS process_exe values(process_pid) AS process_pid
    values(parent_pid) AS parent_pid values(effective_uid) AS effective_uid
    values(exec_success) AS exec_success values(_raw) AS evidence
    BY host source audit_id
| where mvfind(audit_rule,"^zabbix_exec$")>=0
| table _time host audit_id effective_uid process_exe process_pid parent_pid exec_success evidence
```

The result counts audit events, not raw lines or UserParameter invocations. A `success=yes` exec event means the kernel accepted execution, not that the script completed successfully. Build ancestry with PID, parent PID, host and process start/boot context; PID alone is reused. A UID filter can include unrelated jobs using the same account, and descendants that change identity can fall outside it. Shell builtins need not produce a separate exec event, although the invoking `/bin/sh -c ...` may provide command context.

## Windows: retain the process tree

Forward `Microsoft-Windows-Sysmon/Operational` through your existing Windows/Sysmon add-on. Event ID 1 supplies command line and process/parent GUIDs. Preserve child and descendant events, rather than collecting only events whose immediate parent is the Zabbix executable. Microsoft documents the fields and correlation purpose in [Sysmon events](https://learn.microsoft.com/en-us/windows/security/operating-system-security/sysmon/sysmon-events).

### SPL: find direct agent children

Substitute the index and adapt field names to the installed add-on. This is the **starting point**, not a recursive process-tree search:

```spl
index=YOUR_WINDOWS_INDEX EventCode=1
  (ParentImage="*\\zabbix_agentd.exe" OR ParentImage="*\\zabbix_agent2.exe")
| table _time host User ParentImage ParentProcessGuid ProcessGuid Image CommandLine
| sort -_time
```

For each returned ProcessGuid, search same-host Event ID 1 records with that value as ParentProcessGuid, continuing through descendants with a bounded time window. Use your EDR's process tree or a maintained recursive correlation workflow at scale. Do not use a truncating subsearch and then claim complete coverage. PowerShell/cmd scripts commonly create additional children.

Security Event 4688 can be used where Sysmon is unavailable, provided process-creation and command-line auditing are enabled. It has different field names and lacks Sysmon's process GUID identity; correlate host, PID and time carefully. Collection changes belong in the endpoint's existing audit policy.

## Confirm the exact UserParameter key

Maintain a reviewed mapping from agent configuration and its included files; item API data alone is insufficient. Record the configuration version/hash and host identity. Avoid indexing command definitions containing credentials into a broad-access index.

For exact per-key invocation accounting, a site-reviewed wrapper can emit a structured start/end record with `userparameter_key`, invocation UUID, host, timestamp, PID and exit code to a separate log. Keep item output on stdout unchanged, use a fixed command/argument list, and never log secrets or stdout/stderr by default. A wrapper changes the execution path and needs timeout, exit-code, permissions and concurrency tests before production. No wrapper is silently installed by this app.

## Acceptance checklist

1. Use one harmless UserParameter on an isolated agent and a deliberate poll; record the configured key and expected command.
2. Verify the source process event, correlated arguments and ancestry in Splunk. Repeat with a shell invoking an external child so descendant coverage is tested.
3. Verify that a failed exec is distinguished from a started process, and that process start is not reported as successful command completion.
4. Confirm the key mapping or wrapper record; otherwise label the detection as probable Zabbix-related activity.
5. Verify permissions, clock alignment, dropped-event counters, log forwarding, retention and no sensitive output exposure.
6. Build a local dashboard or saved search against the OS index. These records do not automatically populate the 1.0.0 agent-command panel or its Zabbix data models.

The release's existing live command test exercised a predefined remote command and agent log forwarding. **It did not verify auditd/Sysmon UserParameter detection end to end.** Keep that distinction in the marketplace description.
