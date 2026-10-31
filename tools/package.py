"""Build an installable Splunk package containing only the application directory."""
import hashlib
import json
import gzip
import shutil
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parents[1]
output = root / "dist"
output.mkdir(exist_ok=True)
version = json.loads((root / "zabbix_vision/app.manifest").read_text())["info"]["id"]["version"]
target = output / ("zabbix_vision-" + version + ".tar.gz")
docs = root / 'zabbix_vision' / 'README'
docs.mkdir(exist_ok=True)
for path in (root / 'docs').glob('*.md'):
    shutil.copyfile(path, docs / path.name)
overview = (root / 'README.md').read_text(encoding='utf-8')
overview = overview.replace('(docs/', '(').replace('src="docs/assets/', 'src="assets/')
overview = overview.replace('(zabbix_vision/examples)', '(../examples)')
overview = overview.replace('(splunkbase/', '(https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/splunkbase/')
overview = overview.replace('(SPLUNKBASE.md)', '(https://github.com/majidershadi/zabbix-vision-for-splunk/blob/main/SPLUNKBASE.md)')
(docs / 'OVERVIEW.md').write_text(overview, encoding='utf-8')
shutil.copytree(root / 'docs' / 'assets', docs / 'assets', dirs_exist_ok=True)
with target.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as compressed, tarfile.open(fileobj=compressed,mode='w',format=tarfile.PAX_FORMAT) as archive:
    for path in sorted((root / "zabbix_vision").rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts or "local" in path.parts or path.suffix == ".pyc":
            continue
        info = archive.gettarinfo(str(path), arcname=str(path.relative_to(root)).replace("\\", "/"))
        info.uid = info.gid = 0
        info.uname = info.gname = ""
        info.mode = 0o755 if path.suffix == ".py" else 0o644
        info.mtime = 0
        with path.open("rb") as f:
            archive.addfile(info, f)
digest = hashlib.sha256(target.read_bytes()).hexdigest()
target.with_suffix(target.suffix + ".sha256").write_text(digest + "  " + target.name + "\n")
print(str(target))
