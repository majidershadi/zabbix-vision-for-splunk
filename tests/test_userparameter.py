import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'zabbix_vision/bin'))
from zabbix_vision_lib.userparameter import parse_record, normalize_execution, SCHEMA
from zabbix_vision_lib.config import validate_input, ConfigError
from zabbix_vision_lib.collector import Collector, State


def record(**changes):
    value = dict(schema=SCHEMA, invocation_id='c77f4921-2651-4c92-b408-01cc4a038bc1',
                 userparameter_key='vision.health', command_id='health', pid=123,
                 timestamp=100, phase='start', status='started')
    value.update(changes)
    return value


class ExecutionParserTests(unittest.TestCase):
    def test_allowlist_omits_all_unknown_payloads(self):
        result = parse_record(json.dumps(record(password='SECRET', stdout='SECRET', argv=['SECRET'], command='SECRET')))
        self.assertNotIn('SECRET', json.dumps(result))
        self.assertEqual(result['phase'], 'start')

    def test_bad_records_do_not_echo_payload(self):
        for value in ('SECRET', '[]', '{', '{"schema":"SECRET","schema":"SECRET"}', json.dumps(record(phase=[])), json.dumps(record(status={})),
                      json.dumps(record(invocation_id='SECRET')), json.dumps(record(timestamp=True)),
                      json.dumps(record(userparameter_key='x\nSECRET')), 'x'*16385):
            with self.subTest(value=value[:70]), self.assertRaises(ValueError) as exc:
                parse_record(value)
            self.assertNotIn('SECRET', str(exc.exception))

    def test_end_validation(self):
        end = record(phase='end', status='success', duration_ms=1.5, exit_code=0)
        self.assertEqual(parse_record(json.dumps(end))['duration_ms'], 1.5)
        for changes in ({'exit_code': 3}, {'duration_ms': float('nan')}, {'duration_ms': 10**1000}, {'duration_ms': -1}, {'exit_code': True}):
            with self.assertRaises(ValueError):
                parse_record(json.dumps(dict(end, **changes)))

    def test_normalization_identity_and_metadata(self):
        row = dict(itemid='12', clock='110', ns='9', value_type=2, value=json.dumps(record(host='FORGED')))
        metadata = dict(hostid='4', hosts=[{'host':'actual-zabbix-host'}])
        a = normalize_execution(row, 'prod', '7.4', 120, metadata)
        b = normalize_execution(row, 'prod', '7.4', 130, metadata)
        self.assertEqual(a['event_uid'], b['event_uid'])
        self.assertEqual(a['event_time'], 110)
        self.assertEqual(a['execution_time'], 100)
        self.assertEqual(a['dest'], 'actual-zabbix-host')
        self.assertNotIn('FORGED', json.dumps(a))

    def test_invalid_event_is_visible_without_raw_data(self):
        event = normalize_execution(dict(itemid='12', clock=100, value_type=2, value='SECRET'),
                                    'prod', '7.4', 120, dict(hostid='4'))
        self.assertEqual(event['parse_status'], 'invalid')
        self.assertNotIn('SECRET', json.dumps(event))
        self.assertNotIn('raw', event)


class FakeAPI:
    version = (7, 4, 0)
    version_text = '7.4.0'
    missing = False
    value_type = '2'
    def __init__(self):
        self.calls = []
    def call(self, method, params):
        self.calls.append((method, params))
        if method == 'item.get':
            return [] if self.missing else [dict(itemid='12', hostid='4', value_type=self.value_type, hosts=[{'host':'agent'}])]
        return [dict(itemid='12', clock=100, ns=1, value=json.dumps(record())),
                dict(itemid='12', clock=100, ns=2, value='SECRET-invalid')] if params['history'] == 2 else []


class ExecutionCollectorTests(unittest.TestCase):
    def test_scope_is_required_and_unique(self):
        for scope in ('', '12,12', '-1', ','.join(str(i) for i in range(1,1002))):
            with self.assertRaises(ConfigError):
                validate_input(dict(profile='prod', streams='userparameters', userparameter_item_ids=scope))

    def test_collection_and_overlap_dedup(self):
        api, emitted = FakeAPI(), []
        with tempfile.TemporaryDirectory() as folder:
            collector = Collector(api, dict(profile='prod', streams='userparameters', userparameter_item_ids='12',
                                  page_size='10'), State(folder,'test'), emitted.append, clock=lambda:120)
            collector.run()
            self.assertEqual([e['parse_status'] for e in emitted if e['dataset']=='userparameter'], ['valid','invalid'])
            self.assertNotIn('SECRET', json.dumps(emitted))
            emitted.clear()
            collector.run()
            self.assertFalse(any(e['dataset']=='userparameter' for e in emitted))
            self.assertEqual({p['history'] for m,p in api.calls if m=='history.get'}, {2,4})

    def test_missing_or_numeric_item_does_not_advance_checkpoint(self):
        for missing, value_type in ((True,'2'), (False,'3')):
            with tempfile.TemporaryDirectory() as folder:
                api, emitted = FakeAPI(), []
                api.missing, api.value_type = missing, value_type
                state = State(folder,'test')
                Collector(api, dict(profile='prod', streams='userparameters', userparameter_item_ids='12'),
                          state, emitted.append, clock=lambda:120).run()
                self.assertEqual(emitted[-1]['status'], 'error')
                self.assertIsNone(state.load('userparameters'))

    def test_output_failure_retains_checkpoint_for_replay(self):
        with tempfile.TemporaryDirectory() as folder:
            state = State(folder, 'test')
            def emit(event):
                if event['dataset']=='userparameter':
                    raise OSError('sink down')
            Collector(FakeAPI(), dict(profile='prod', streams='userparameters', userparameter_item_ids='12'),
                      state, emit, clock=lambda:120).run()
            self.assertIsNone(state.load('userparameters'))


@unittest.skipUnless(sys.platform.startswith('linux'), 'Wrapper uses Linux process groups and flock')
class WrapperTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root/'execution.jsonl'
        self.config = self.root/'config.json'
        self.wrapper = ROOT/'zabbix_vision/examples/userparameter-wrapper.py'
    def configure(self, code, timeout=2):
        self.config.write_text(json.dumps({'log_file':str(self.log), 'commands':{'vision.health':{
            'argv':[sys.executable,'-c',code], 'timeout_seconds':timeout,'command_id':'health'}}}))
        self.config.chmod(0o600)
    def invoke(self):
        return subprocess.run([sys.executable,str(self.wrapper),'--config',str(self.config),'--key','vision.health'],
                              capture_output=True, text=True, timeout=10)
    def records(self):
        return [parse_record(line) for line in self.log.read_text().splitlines()]
    def test_success_preserves_output_and_omits_it_from_audit(self):
        self.configure("print('SECRET-result')")
        result = self.invoke()
        self.assertEqual((result.returncode,result.stdout), (0,'SECRET-result\n'))
        a,b = self.records()
        self.assertEqual(a['invocation_id'], b['invocation_id'])
        self.assertEqual(b['status'], 'success')
        self.assertNotIn('SECRET', self.log.read_text())
    def test_failure_preserves_exit_status(self):
        self.configure('import sys; sys.exit(7)')
        self.assertEqual(self.invoke().returncode, 7)
        self.assertEqual(self.records()[-1]['exit_code'], 7)
    def test_timeout_is_recorded(self):
        self.configure('import time; time.sleep(30)', timeout=1)
        self.assertEqual(self.invoke().returncode, 124)
        self.assertEqual(self.records()[-1]['status'], 'timeout')
    def test_start_log_failure_prevents_command(self):
        marker = self.root/'must-not-exist'
        self.configure('from pathlib import Path; Path(%r).touch()' % str(marker))
        self.log.symlink_to(self.root/'other')
        self.assertEqual(self.invoke().returncode, 125)
        self.assertFalse(marker.exists())
    def test_writable_configuration_rejected(self):
        self.configure("print('not run')")
        self.config.chmod(0o666)
        self.assertEqual(self.invoke().returncode, 125)
        self.assertFalse(self.log.exists())
    def test_term_records_interruption(self):
        self.configure('import time; time.sleep(30)', timeout=30)
        proc = subprocess.Popen([sys.executable,str(self.wrapper),'--config',str(self.config),'--key','vision.health'],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if self.log.exists() and self.log.stat().st_size:
                    break
                time.sleep(.02)
            time.sleep(.1)
            proc.terminate()
            proc.communicate(timeout=5)
            self.assertEqual(proc.returncode, 130)
            self.assertEqual(self.records()[-1]['status'], 'interrupted')
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.communicate()


if __name__ == '__main__':
    unittest.main()
