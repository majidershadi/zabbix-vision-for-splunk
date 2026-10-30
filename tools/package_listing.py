"""Bundle public listing copy, guide and media beside the verified install package."""
from pathlib import Path
import zipfile
import argparse
import hashlib

root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--revision', help='Dated media-kit suffix, e.g. 2026-10-30')
args=parser.parse_args()
if args.revision and not all(c.isdigit() or c=='-' for c in args.revision):
    parser.error('revision must contain only digits and hyphens')
files=[root/p for p in ['README.md','SPLUNKBASE.md','LICENSE','NOTICE']]
files+=list((root/'docs').glob('*.md'))
files+=list((root/'docs/assets').glob('*'))
files+=[root/'docs/screenshots/zabbix-vision-security.png']
files+=list((root/'zabbix_vision/static').glob('*.png'))
files += [root/'dist'/name for name in ['zabbix_vision-1.0.0.tar.gz','zabbix_vision-1.0.0.tar.gz.sha256','appinspect.json']]
files += [root/'SECURITY.md']
files += [p for p in (root/'zabbix_vision/examples').rglob('*') if p.is_file()]
files += list((root/'docs/screenshots/splunkbase').rglob('*.png'))
files += list((root/'splunkbase').glob('*.md'))
files += list((root/'splunkbase').glob('*.html'))
suffix='-'+args.revision if args.revision else ''
target=root/('dist/zabbix_vision-splunkbase-kit-1.0.0'+suffix+'.zip')
manifest=[]
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(set(files)):
        archive.write(p,p.relative_to(root).as_posix())
        manifest.append(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(root).as_posix())
    archive.writestr('MANIFEST.sha256','\n'.join(manifest)+'\n')
target.with_suffix('.zip.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n',encoding='utf-8')
print(target)
