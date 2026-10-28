import io
import json
from pathlib import Path
import ssl
import sys
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'zabbix_vision' / 'bin'))
from zabbix_vision_lib.client import Client, APIError, NoRedirect, tls_context
from zabbix_vision_lib.config import endpoint, validate_profile, validate_input, ConfigError
from zabbix_vision_lib.collector import Collector, State, Overflow, bounded_window, snapshot_spec
from zabbix_vision_lib.normalize import normalize
from zabbix_vision_lib.splunk_store import Store, StoreError


class Response(io.BytesIO):
    pass


class RPC:
    def __init__(self, version='7.4.0', handler=None):
        self.version = version
        self.requests = []
        self.handler = handler

    def open(self, req, timeout):
        data = json.loads(req.data)
        self.requests.append((data, dict(req.header_items())))
        result = self.version if data['method'] == 'apiinfo.version' else self.handler(data) if self.handler else []
        return Response(json.dumps({'jsonrpc':'2.0','id':data['id'],'result':result}).encode())


class ConfigTests(unittest.TestCase):
    def test_paths(self):
        for prefix in ('', '/zabbix', '/a/custom/prefix', '/zabbix/'):
            self.assertEqual(endpoint('https://monitor.test' + prefix), 'https://monitor.test' + prefix.rstrip('/') + '/api_jsonrpc.php')
        self.assertEqual(endpoint('https://monitor.test/a/api_jsonrpc.php'), 'https://monitor.test/a/api_jsonrpc.php')

    def test_unsafe_urls(self):
        for url in ('http://x', 'https://user:pass@x', 'https://x/?token=x', 'file:///tmp/x', 'https://x/#x', 'https://x:bad'):
            with self.subTest(url=url), self.assertRaises(ConfigError):
                endpoint(url)

    def test_profile_guards(self):
        for change in ({'timeout':'0'}, {'tls_min':'1.0'}, {'client_key':'x'}, {'enable_execution':'true'}, {'proxy_url':'http://u:p@proxy'}, {'token':'no'}):
            with self.subTest(change=change), self.assertRaises(ConfigError):
                validate_profile(dict(url='https://x', **change))

    def test_metrics_need_scope(self):
        with self.assertRaises(ConfigError):
            validate_input({'profile':'prod', 'streams':'history'})

    def test_tls_defaults(self):
        ctx = tls_context(validate_profile({'url':'https://x'}))
        self.assertTrue(ctx.check_hostname)
        self.assertEqual(ctx.verify_mode, ssl.CERT_REQUIRED)
        self.assertEqual(ctx.minimum_version, ssl.TLSVersion.TLSv1_2)


class TransportTests(unittest.TestCase):
    def test_version_matrix(self):
        for version in ('6.0.40', '6.2.9', '6.4.21', '7.0.18', '7.2.7', '7.4.0', '8.0.0beta1'):
            with self.subTest(version=version):
                transport = RPC(version)
                client = Client({'url':'https://x/custom'}, 'SECRET', opener=transport)
                client.call('host.get', {})
                public, _ = transport.requests[0]
                private, headers = transport.requests[1]
                self.assertNotIn('auth', public)
                if tuple(map(int,version.split('.')[:2])) < (6,4):
                    self.assertEqual(private['auth'], 'SECRET')
                    self.assertNotIn('Authorization', headers)
                else:
                    self.assertNotIn('auth', private)
                    self.assertEqual(headers['Authorization'], 'Bearer SECRET')

    def test_no_legacy_downgrade(self):
        with self.assertRaises(ConfigError):
            Client({'url':'https://x','auth_mode':'body'}, 'secret', opener=RPC()).discover()

    def test_redirect_refused(self):
        with self.assertRaises(APIError):
            NoRedirect().redirect_request(None,None,302,'',{},'https://evil.test')

    def test_retry_and_no_execution_retry(self):
        class Failing:
            calls = 0
            def open(self, req, timeout):
                self.calls += 1
                raise urllib.error.URLError('SECRET SHOULD NOT LEAK')
        for retry, expected in ((True, 4), (False, 1)):
            opener = Failing()
            client = Client({'url':'https://x'}, 'secret', opener=opener, sleep=lambda _:None)
            client.version = (7,4,0)
            with self.assertRaises(APIError) as exc:
                client.call('script.execute' if not retry else 'host.get',{},retry=retry)
            self.assertEqual(opener.calls,expected)
            self.assertNotIn('SECRET',str(exc.exception))


class FakeClient:
    version = (7,4,0)
    version_text = '7.4.0'
    def __init__(self, rows):
        self.rows = rows
        self.calls = []
    def call(self, method, params):
        self.calls.append((method,params))
        if 'time_from' in params:
            return [r for r in self.rows if params['time_from'] <= int(r['clock']) <= params['time_till']][:params['limit']]
        return self.rows[:params['limit']]


class CollectorTests(unittest.TestCase):
    def test_bisect_no_loss(self):
        rows = [{'auditid':'cuid'+str(i),'clock':str(i//3)} for i in range(30)]
        actual = list(bounded_window(FakeClient(rows),'auditlog.get',{},0,10,5))
        self.assertEqual(actual,rows)

    def test_saturated_second_fails_closed(self):
        client = FakeClient([{'clock':'10','auditid':str(i)} for i in range(5)])
        with self.assertRaises(Overflow):
            list(bounded_window(client,'auditlog.get',{},10,10,5))

    def test_checkpoints_overlap_and_late_arrival(self):
        with tempfile.TemporaryDirectory() as tmp:
            rows = [{'auditid':'cuid1','clock':'950','action':'8'}]
            client = FakeClient(rows)
            emitted = []
            state = State(tmp,'test')
            c = Collector(client,{'profile':'prod','streams':'audit'},state,emitted.append,clock=lambda:1000)
            c.run()
            self.assertEqual(len([e for e in emitted if e['dataset']=='audit']),1)
            emitted.clear()
            c.run()
            self.assertEqual(len([e for e in emitted if e['dataset']=='audit']),0)
            rows.append({'auditid':'late','clock':'951','action':'9'})
            c.run()
            self.assertEqual(len([e for e in emitted if e['dataset']=='audit']),1)

    def test_partial_failure_does_not_advance(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = State(tmp,'test')
            state.save('audit',{'until':950,'seen':{}})
            def broken(_):
                raise BrokenPipeError()
            c = Collector(FakeClient([{'clock':'951','auditid':'1'}]),{'profile':'prod','streams':'audit'},state,broken,clock=lambda:1000)
            with self.assertRaises(BrokenPipeError):
                c.run()
            self.assertEqual(state.load('audit')['until'],950)

    def test_corrupt_checkpoint_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = State(tmp,'test')
            state.path('audit').write_text('{')
            with self.assertRaises(APIError):
                state.load('audit')

    def test_zero_problem_snapshot_marker(self):
        emitted=[]
        with tempfile.TemporaryDirectory() as tmp:
            Collector(FakeClient([]),{'profile':'p','streams':'problems'},State(tmp,'t'),emitted.append,clock=lambda:1000).run()
        self.assertEqual(emitted[0]['dataset'],'snapshot')
        self.assertEqual(emitted[0]['count'],0)

    def test_snapshot_overflow_does_not_emit_inventory(self):
        emitted=[]
        with tempfile.TemporaryDirectory() as tmp:
            Collector(FakeClient([{},{}]),{'profile':'p','streams':'hosts','snapshot_limit':'2'},State(tmp,'t'),emitted.append,clock=lambda:1000).run()
        self.assertEqual(len(emitted),1)
        self.assertEqual(emitted[0]['status'],'error')

    def test_proxy_version_fields(self):
        self.assertIn('host',snapshot_spec('proxies',(6,0,0))[1]['output'])
        self.assertIn('name',snapshot_spec('proxies',(7,0,0))[1]['output'])


class NormalizationTests(unittest.TestCase):
    def test_auth_and_secret_redaction(self):
        e = normalize('audit',{'auditid':'cuid','clock':'100','action':'9','username':'alice','ip':'127.0.0.1','details':'{"user.password":["update","secret","old"],"user.name":["update","a","b"]}'},'prod','7.4.0',101)
        self.assertEqual(e['status'],'failure')
        self.assertEqual(e['category'],'authentication')
        self.assertEqual(e['raw']['details']['user.password'],'[REDACTED]')
        self.assertNotIn('secret',json.dumps(e))
        self.assertEqual(e['user'],'alice')

    def test_script_output_in_audit_is_redacted(self):
        e = normalize('audit', {'auditid':'execution', 'clock':'100', 'action':'7',
            'details':json.dumps({'script.output':['add','sensitive-command-result'],
                                  'script.hostid':['add','10084']})}, 'prod','7.4.0',101)
        self.assertNotIn('sensitive-command-result',json.dumps(e))
        self.assertEqual(e['raw']['details']['script.output'],'[REDACTED]')
        self.assertEqual(e['raw']['details']['script.hostid'],['add','10084'])

    def test_nanosecond_identity(self):
        a = normalize('history',{'itemid':'1','clock':'100','ns':'1','value_type':0},'p','7.4.0',101)
        b = normalize('history',{'itemid':'1','clock':'100','ns':'2','value_type':0},'p','7.4.0',101)
        self.assertNotEqual(a['event_uid'],b['event_uid'])


class SecretTests(unittest.TestCase):
    def test_native_cipher_matrix(self):
        for version,prefix in (('9.4.13','$7$'),('10.4.1','$7$'),('10.6.0','$8$'),('11.0.0','$8$')):
            calls=[]
            def request(path, **kwargs):
                calls.append((path,kwargs))
                value = {'version':version} if path=='/services/server/info' else {'encr_password':prefix+'encrypted','clear_password':'secret'}
                return {'status':200}, json.dumps({'entry':[{'content':value}]})
            result = Store('SESSION',request).save_secret('p','secret')
            self.assertEqual(result['observed_cipher'],prefix)
            self.assertEqual(result['expected_cipher'],prefix)
            self.assertNotIn('secret',json.dumps(result))
            self.assertTrue(all(x[1]['sessionKey']=='SESSION' for x in calls))


if __name__ == '__main__':
    unittest.main()
