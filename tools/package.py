"""Build an installable Splunk package containing only the application directory."""
import hashlib
import gzip
import shutil
from pathlib import Path
import tarfile

root = Path(__file__).resolve().parents[1]
output = root / "dist"
output.mkdir(exist_ok=True)
target = output / "zabbix_vision-1.0.0.tar.gz"
docs = root / 'zabbix_vision' / 'README'
docs.mkdir(exist_ok=True)
for path in (root / 'docs').glob('*.md'):
    shutil.copyfile(path, docs / path.name)
(docs / 'OVERVIEW.md').write_text((root / 'README.md').read_text(encoding='utf-8').replace('(docs/', '(').replace('src="docs/assets/', 'src="assets/'),encoding='utf-8')
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
