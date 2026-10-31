"""Strict, payload-minimizing normalization of opt-in execution log history."""
import hashlib
import json
import re
import uuid

SCHEMA = 'zabbix_userparameter_execution/v1'
NAME = re.compile(r'[A-Za-z0-9_.-]{1,128}')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON field')
        result[key] = value
    return result


def parse_record(value):
    if not isinstance(value, str) or len(value.encode('utf-8')) > 16384:
        raise ValueError('Record must be a JSON object of at most 16 KiB')
    try:
        record = json.loads(value, object_pairs_hook=unique_object)
    except (ValueError, RecursionError):
        raise ValueError('Invalid execution JSON') from None
    if not isinstance(record, dict) or record.get('schema') != SCHEMA:
        raise ValueError('Unsupported execution schema')
    result = {'schema': SCHEMA}
    try:
        result['invocation_id'] = str(uuid.UUID(record.get('invocation_id', '')))
    except (ValueError, TypeError, AttributeError):
        raise ValueError('Invalid invocation UUID') from None
    for field in ('userparameter_key', 'command_id'):
        if not isinstance(record.get(field), str) or not NAME.fullmatch(record[field]):
            raise ValueError('Invalid execution key or command identifier')
        result[field] = record[field]
    phase, status = record.get('phase'), record.get('status')
    allowed = {'start': {'started'}, 'end': {'success', 'failure', 'timeout', 'interrupted', 'spawn_failed'}}
    if not isinstance(phase, str) or not isinstance(status, str) or phase not in allowed or status not in allowed[phase]:
        raise ValueError('Invalid execution phase or status')
    result.update(phase=phase, status=status)
    for field, low, high in (('timestamp', 0, 4102444800), ('pid', 1, 2147483647)):
        value = record.get(field)
        if type(value) is not int or not low <= value <= high:
            raise ValueError('Invalid execution timestamp or PID')
        result[field] = value
    if phase == 'end':
        duration = record.get('duration_ms')
        code = record.get('exit_code')
        if type(duration) not in (float, int) or not 0 <= duration <= 2592000000:
            raise ValueError('Invalid execution duration')
        if code is not None and (type(code) is not int or not 0 <= code <= 255):
            raise ValueError('Invalid execution exit code')
        if (status == 'success' and code != 0) or (status == 'failure' and (code is None or code == 0)):
            raise ValueError('Execution status contradicts exit code')
        result.update(duration_ms=duration, exit_code=code)
    # Deliberately do not retain arbitrary fields, command arguments or output.
    return result


def normalize_execution(row, instance, version, collected, metadata):
    identity = [instance, 'userparameters', str(row['itemid']), row['clock'], row.get('ns', 0), row['value_type']]
    event = {'schema_version': 1, 'dataset': 'userparameter', 'instance': instance,
             'zabbix_version': version, 'collected_at': collected, 'event_time': int(row['clock']),
             'event_uid': hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest(),
             'itemid': str(row['itemid']), 'hostid': str(metadata['hostid']),
             'dest': metadata.get('hosts', [{}])[0].get('host', 'unknown') if metadata.get('hosts') else 'unknown',
             'evidence_source': 'zabbix_api_history', 'vendor_product': 'Zabbix',
             'history_clock': int(row['clock']), 'history_ns': int(row.get('ns', 0)),
             'status': 'invalid', 'parse_status': 'invalid'}
    try:
        record = parse_record(row.get('value'))
    except ValueError as exc:
        event['error'] = str(exc)  # Only parser-authored messages, never payloads.
        return event
    event.update(record)
    event['execution_time'] = event.pop('timestamp')
    event['parse_status'] = 'valid'
    # _time remains the Zabbix history clock, so host clock skew cannot hide records.
    return event
