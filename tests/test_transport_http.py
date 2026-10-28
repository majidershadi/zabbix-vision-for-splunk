"""Real loopback HTTP transport tests, no mocked opener."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import threading
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'zabbix_vision'/'bin'))
from zabbix_vision_lib.client import Client, APIError


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.calls=[]
        self.status=200
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                outer.calls.append((self.path,dict(self.headers),data))
                self.send_response(outer.status)
                if outer.status == 302:
                    self.send_header('Location','http://127.0.0.1:1/steal')
                self.end_headers()
                self.wfile.write(json.dumps({'jsonrpc':'2.0','id':data['id'],'result':'7.4.16' if data['method']=='apiinfo.version' else [{'hostid':'1'}]}).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
    def client(self):
        return Client({'url':'http://127.0.0.1:%s/a/custom/prefix'%self.server.server_port,'allow_http':'true','retries':'0'},'loopback-test-token')
    def test_custom_prefix_and_header(self):
        self.assertEqual(self.client().call('host.get',{}),[{'hostid':'1'}])
        self.assertEqual(self.calls[0][0],'/a/custom/prefix/api_jsonrpc.php')
        self.assertNotIn('Authorization',self.calls[0][1])
        self.assertEqual(self.calls[1][1]['Authorization'],'Bearer loopback-test-token')
        self.assertNotIn('auth',self.calls[1][2])
    def test_redirect_does_not_send_token(self):
        self.status=302
        with self.assertRaises(APIError):
            self.client().call('host.get',{})
        self.assertEqual(len(self.calls),1)


if __name__=='__main__':
    unittest.main()
