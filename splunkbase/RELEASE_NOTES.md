# Zabbix Vision for Splunk 1.1.0

Public beta · 1 November 2026 · Apache-2.0 · App ID `zabbix_vision`

Adds UserParameter execution evidence through Zabbix API history. Install this version to use the new `userparameters` stream and **UserParameter executions** dashboard. Endpoint instrumentation is opt-in; the API cannot reconstruct unrecorded command activity.

## Added

- Dedicated scoped Log/Text execution-history collection with Zabbix item/host metadata validation.
- Strict versioned JSON parser, invocation UUIDs, producer timing, duration, exit codes and visible invalid-record diagnostics without raw payloads.
- Linux fixed-command wrapper with start/end logging, unchanged stdout/stderr, exit-code preservation, bounded timeout, process-group timeout cleanup and no automatic retries.
- Seventh dashboard, new Security data-model object, reusable invocation-correlation macro and two disabled-by-default detection searches.
- Setup field, input specification, agent/log-item examples and complete API-path installation guide.

## Upgrade

Back up local configuration, checkpoints and supported credential/key backups, then install over `zabbix_vision` and restart. Existing inputs without execution-item IDs retain checkpoint identity. Create a separate input for the new stream. Deploy the wrapper/compatible producer and Zabbix log item before enabling collection. Existing accelerated Security models need summary rebuild/reconfiguration for the new object.

## Boundaries

The wrapper supports Linux with Python 3.9+ and fixed commands/simple keys. Flexible UserParameter arguments and a Windows wrapper are not included. Evidence is producer-reported; independent OS auditing remains necessary for comprehensive descendant-process coverage. Missing completion records are incomplete evidence, not a running-process assertion. Secrets/output/arguments are omitted from dedicated execution records; generic history and item snapshots have different retention behavior.

See USERPARAMETER_API.md for deployment and troubleshooting, and VALIDATION.md for test evidence and AppInspect status. Splunkbase/Splunk Cloud approval is not claimed.

## Validation

48 Linux tests and 39 live Splunk dashboard/selector searches passed. Real Agent 2 wrapper executions reached Splunk through Zabbix 7.4.16 Log history with matched start/end evidence. Local AppInspect 4.4.0: zero errors/failures and 11 documented warnings. See [validation evidence](https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/docs/VALIDATION.md).
