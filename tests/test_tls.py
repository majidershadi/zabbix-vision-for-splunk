"""Exercise real TLS handshakes; cryptography is a development-only dependency."""
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import json
from pathlib import Path
import ssl
import sys
import tempfile
import threading
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'zabbix_vision'/'bin'))
sys.path.insert(0,str(ROOT/'.tools'))
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID
    HAVE_CRYPTO=True
except ImportError:
    HAVE_CRYPTO=False
from zabbix_vision_lib.client import Client, APIError


@unittest.skipUnless(HAVE_CRYPTO,'Install cryptography for TLS integration tests')
class TLSTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)
        ca_key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
        ca_name=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'Zabbix Vision for Splunk Test CA')])
        now=datetime.now(timezone.utc)
        ca=(x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5))
            .not_valid_after(now+timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True,path_length=0),critical=True)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),critical=False)
            .add_extension(x509.KeyUsage(digital_signature=True,content_commitment=False,key_encipherment=False,data_encipherment=False,key_agreement=False,key_cert_sign=True,crl_sign=True,encipher_only=False,decipher_only=False),critical=True)
            .sign(ca_key,hashes.SHA256()))
        (self.path/'ca.pem').write_bytes(ca.public_bytes(serialization.Encoding.PEM))
        for name in ('server','client'):
            key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
            subject=x509.Name([x509.NameAttribute(NameOID.COMMON_NAME,'localhost' if name=='server' else 'test-client')])
            builder=(x509.CertificateBuilder().subject_name(subject).issuer_name(ca_name).public_key(key.public_key())
                .serial_number(x509.random_serial_number()).not_valid_before(now-timedelta(minutes=5)).not_valid_after(now+timedelta(days=1))
                .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),critical=False)
                .add_extension(x509.BasicConstraints(ca=False,path_length=None),critical=True)
                .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if name=='server' else ExtendedKeyUsageOID.CLIENT_AUTH]),critical=False))
            if name=='server':
                builder=builder.add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]),critical=False)
            cert=builder.sign(ca_key,hashes.SHA256())
            (self.path/(name+'.pem')).write_bytes(cert.public_bytes(serialization.Encoding.PEM))
            protection=serialization.BestAvailableEncryption(b'test-passphrase') if name=='client' else serialization.NoEncryption()
            (self.path/(name+'.key')).write_bytes(key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,protection))
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):
                pass
            def do_POST(self):
                data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({'jsonrpc':'2.0','id':data['id'],'result':'7.4.16'}).encode())
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.load_cert_chain(str(self.path/'server.pem'),str(self.path/'server.key'))
        self.context.load_verify_locations(str(self.path/'ca.pem'))
        self.server.socket=self.context.wrap_socket(self.server.socket,server_side=True)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def profile(self,hostname='localhost'):
        return {'url':'https://%s:%s/custom'%(hostname,self.server.server_port),'ca_bundle':str(self.path/'ca.pem'),'retries':'0'}

    def test_custom_ca_verified(self):
        self.assertEqual(Client(self.profile(),'test').discover(),'7.4.16')

    def test_unknown_ca_rejected(self):
        p=self.profile()
        del p['ca_bundle']
        with self.assertRaises(APIError):
            Client(p,'test').discover()

    def test_hostname_mismatch_rejected(self):
        with self.assertRaises(APIError):
            Client(self.profile('127.0.0.1'),'test').discover()

    def test_mutual_tls_encrypted_private_key(self):
        self.context.verify_mode=ssl.CERT_REQUIRED
        with self.assertRaises(APIError):
            Client(self.profile(),'test').discover()
        p=dict(self.profile(),client_cert=str(self.path/'client.pem'),client_key=str(self.path/'client.key'))
        self.assertEqual(Client(p,'test',key_password='test-passphrase').discover(),'7.4.16')


if __name__=='__main__':
    unittest.main()
