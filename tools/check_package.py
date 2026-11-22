import argparse
import ast
import configparser
import json
from pathlib import Path, PurePosixPath
import tarfile
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1] / 'zabbix_vision'
parser = argparse.ArgumentParser(description="Validate the app sources and optionally its archive permissions.")
parser.add_argument("--archive", type=Path, help="Path to the built Splunk app archive")
args = parser.parse_args()
counts = {'python':0,'xml':0,'json':0,'conf':0}
for path in root.rglob('*'):
    if not path.is_file():
        continue
    if path.suffix == '.py':
        ast.parse(path.read_text(encoding='utf-8'),feature_version=(3,9))
        counts['python']+=1
    elif path.suffix == '.xml':
        ET.parse(path)
        counts['xml']+=1
    elif path.suffix == '.json':
        json.loads(path.read_text(encoding='utf-8'))
        counts['json']+=1
    elif path.suffix == '.conf' and 'examples' not in path.parts:
        parser=configparser.ConfigParser(interpolation=None,strict=True)
        parser.read(path,encoding='utf-8')
        counts['conf']+=1
print('Validated',counts)

if args.archive:
    with tarfile.open(args.archive, "r:gz") as archive:
        for entry in archive.getmembers():
            if not entry.isfile():
                continue
            path = PurePosixPath(entry.name).relative_to(root.name)
            if entry.mode & 0o111 and path.parts[0] != "bin" and path.parent != PurePosixPath("appserver/controllers"):
                raise SystemExit(f"Unexpected execute permissions ({entry.mode:04o}) on {entry.name}")
        collector = archive.getmember(f"{root.name}/bin/zabbix_vision.py")
        if not collector.isfile() or (collector.mode & 0o111) != 0o111:
            raise SystemExit(f"Modular input must remain executable: {collector.name}")
        with archive.extractfile(collector) as entrypoint:
            shebang = entrypoint.readline()
            if not shebang.startswith(b"#!") or not shebang.endswith(b"python3\n"):
                raise SystemExit(f"Modular input must have a Linux-compatible Python shebang: {collector.name}")
    print("Validated packaged execute permissions:", args.archive)
