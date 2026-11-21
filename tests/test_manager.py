import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'zabbix_vision'/'bin'))
stub=types.ModuleType('splunk.persistconn.application')
stub.PersistentServerConnectionApplication=object
with patch.dict(sys.modules,{'splunk':types.ModuleType('splunk'),'splunk.persistconn':types.ModuleType('splunk.persistconn'),'splunk.persistconn.application':stub}):
    import zabbix_vision_manager


class FakeStore:
    calls=[]
    def __init__(self,key):
        self.key=key
    def require_capability(self,cap):
        return 'admin'
    def profile(self,name):
        return {'url':'https://zabbix.test','enable_execution':'false','allowed_script_ids':'1','allowed_host_ids':'2'}
    def secret(self,*args,**kwargs):
        return 'test-token'
    def call(self,path,method='GET',data=None,missing_ok=False):
        self.calls.append((path,method,data))
        return None if method=='GET' else {}


class FakeClient:
    calls=[]
    def __init__(self,*args):
        pass
    def discover(self):
        return '7.4.16'
    def call(self,*args,**kwargs):
        self.calls.append((args,kwargs))
        return {'response':'success'}


class ManagerTests(unittest.TestCase):
    def setUp(self):
        FakeStore.calls=[]
        FakeClient.calls=[]
        self.store_patch=patch.object(zabbix_vision_manager,'Store',FakeStore)
        self.client_patch=patch.object(zabbix_vision_manager,'Client',FakeClient)
        self.store_patch.start()
        self.client_patch.start()
        self.addCleanup(self.store_patch.stop)
        self.addCleanup(self.client_patch.stop)
    def invoke(self,body,session=True):
        req={'method':'POST','payload':json.dumps(body)}
        if session:
            req['session']={'authtoken':'caller-session'}
        return zabbix_vision_manager.Manager().handle(json.dumps(req))
    def test_no_session_is_rejected(self):
        self.assertEqual(self.invoke({},False)['status'],401)
    def test_first_save_requires_a_token(self):
        with patch.object(FakeStore, 'secret', return_value=None):
            result = self.invoke({'action': 'save', 'name': 'prod',
                                  'settings': {'url': 'https://zabbix.test'}})
        self.assertEqual(result['status'], 400)
        self.assertEqual(json.loads(result['payload'])['error'], 'Enter an API token for a new connection')

    def test_first_save_reports_rejected_setup_update_as_warning(self):
        from zabbix_vision_lib.splunk_store import ROOT, Store

        def request(path, **kwargs):
            method = kwargs['method']
            calls.append((method, path, kwargs['postargs']))
            if path == '/services/authentication/current-context':
                return response(200, {'username': 'admin', 'capabilities': ['admin_all_objects']})
            if method == 'GET' and path.startswith(ROOT + '/storage/passwords/'):
                if not any(method == 'POST' and endpoint == ROOT + '/storage/passwords'
                           for method, endpoint, data in calls):
                    return response(404)
                return response(200, {'encr_password': '$7$encrypted', 'clear_password': 'fixture-token'})
            if path == '/services/server/info':
                return response(200, {'version': '10.4.1'})
            if method == 'GET' and path.startswith(ROOT + '/configs/conf-zabbix_vision_connections/'):
                return response(404)
            if method == 'POST' and path == '/services/apps/local/zabbix_vision':
                return response(400, {'message': 'upstream marker must not be exposed'})
            return response(200)

        def response(status, content=None):
            return {'status': status}, json.dumps({'entry': [{'content': content or {}}]})

        calls = []
        with patch.object(zabbix_vision_manager, 'Store', side_effect=lambda token: Store(token, request)):
            result = self.invoke({'action': 'save', 'name': 'prod', 'token': 'fixture-token',
                                  'settings': {'url': 'https://zabbix.test'}})
        body = json.loads(result['payload'])
        self.assertEqual(result['status'], 200)
        self.assertEqual(body['saved'], 'prod')
        self.assertIn('HTTP 400', body['warning'])
        self.assertNotIn('upstream marker', result['payload'])
        self.assertNotIn('fixture-token', result['payload'])
        posts = [endpoint for method, endpoint, data in calls if method == 'POST']
        self.assertEqual(posts, [ROOT + '/storage/passwords', ROOT + '/configs/conf-zabbix_vision_connections',
                                 ROOT + '/configs/conf-app/install', '/services/apps/local/zabbix_vision'])

    def test_storage_rejection_remains_a_save_error(self):
        from zabbix_vision_lib.splunk_store import StoreError

        with patch.object(FakeStore, 'save_secret', create=True,
                          side_effect=StoreError('Splunk management API returned HTTP 400.')):
            result = self.invoke({'action': 'save', 'name': 'prod', 'token': 'fixture-token',
                                  'settings': {'url': 'https://zabbix.test'}})
        self.assertEqual(result['status'], 400)
        body = json.loads(result['payload'])
        self.assertEqual(body['source'], 'zabbix_vision')
        self.assertIn('Save the API token failed', body['error'])
        self.assertEqual(FakeStore.calls, [])

    def test_input_uses_enable_endpoint(self):
        result=self.invoke({'action':'input','name':'prod','settings':{'profile':'prod'}})
        self.assertEqual(result['status'],200)
        posts=[c for c in FakeStore.calls if c[1]=='POST']
        self.assertNotIn('disabled',posts[0][2])
        self.assertTrue(posts[-1][0].endswith('/enable'))
    def test_input_uses_disable_endpoint(self):
        self.invoke({'action':'input','name':'prod','settings':{'profile':'prod','disabled':'1'}})
        self.assertTrue(FakeStore.calls[-1][0].endswith('/disable'))
    def test_execution_disabled_never_calls_api(self):
        result=self.invoke({'action':'execute','name':'p','scriptid':'1','hostid':'2','confirmation':'EXECUTE'})
        self.assertEqual(result['status'],403)
        self.assertEqual(FakeClient.calls,[])
    def test_execution_no_automatic_retry(self):
        p={'url':'https://x','enable_execution':'true','allowed_script_ids':'1','allowed_host_ids':'2'}
        with patch.object(FakeStore,'profile',return_value=p), patch.object(zabbix_vision_manager,'audit') as audit:
            result=self.invoke({'action':'execute','name':'p','scriptid':'1','hostid':'2','confirmation':'EXECUTE'})
            self.assertEqual(result['status'],200)
            self.assertEqual(audit.call_count,2)
            self.assertEqual(FakeClient.calls[0][1],{'retry':False})
            self.assertTrue(json.loads(result['payload'])['output_omitted'])
    def test_execution_outside_host_allowlist(self):
        p={'url':'https://x','enable_execution':'true','allowed_script_ids':'1','allowed_host_ids':'2'}
        with patch.object(FakeStore,'profile',return_value=p):
            result=self.invoke({'action':'execute','name':'p','scriptid':'1','hostid':'99','confirmation':'EXECUTE'})
            self.assertEqual(result['status'],403)
            self.assertEqual(FakeClient.calls,[])


if __name__=='__main__':
    unittest.main()
