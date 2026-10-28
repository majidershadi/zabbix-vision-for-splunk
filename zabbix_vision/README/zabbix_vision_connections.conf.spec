[<profile>]
url = <URL>
* Root frontend URL, arbitrary prefix, or full api_jsonrpc.php endpoint.
verify_tls = <boolean>
* Validate certificate chain and hostname. Default true.
allow_http = <boolean>
* Allow unencrypted HTTP in an isolated lab. Default false.
ca_bundle = <path>
* Optional PEM CA bundle on collector host.
client_cert = <path>
* Optional PEM client certificate chain for mutual TLS.
client_key = <path>
* PEM private key paired with client_cert; passphrase belongs in storage/passwords.
tls_min = 1.2|1.3
* Minimum TLS version. Default 1.2.
proxy_url = <URL>
* Explicit HTTP CONNECT proxy without embedded credentials. Default none.
timeout = <integer>
* HTTP timeout 1–300 seconds. Default 30.
retries = <integer>
* Retries 0–5 for read requests only. Default 3.
max_response_mb = <integer>
* Response byte limit 1–256 MiB. Default 32.
auth_mode = auto|bearer|body
* Auto uses body auth before 6.4 and Bearer from 6.4 onward.
enable_execution = <boolean>
* Default false. Execution requires both allowlists and Splunk capability.
allowed_script_ids = <comma-separated IDs>
* Approved predefined Zabbix script IDs.
allowed_host_ids = <comma-separated IDs>
* Approved host IDs.
