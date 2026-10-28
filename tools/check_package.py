import ast
import configparser
import json
from pathlib import Path
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1] / 'zabbix_vision'
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
