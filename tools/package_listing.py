"""Bundle public listing copy, guide and media beside the verified install package."""
from pathlib import Path
import zipfile

root=Path(__file__).resolve().parents[1]
files=[root/p for p in ['README.md','SPLUNKBASE.md','LICENSE','NOTICE']]
files+=list((root/'docs').glob('*.md'))
files+=list((root/'docs/assets').glob('*'))
files+=[root/'docs/screenshots/zabbix-vision-security.png']
files+=list((root/'zabbix_vision/static').glob('*.png'))
files += [root/'dist'/name for name in ['zabbix_vision-1.0.0.tar.gz','zabbix_vision-1.0.0.tar.gz.sha256','appinspect.json']]
target=root/'dist/zabbix_vision-splunkbase-kit-1.0.0.zip'
with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED) as archive:
    for p in files:
        archive.write(p,p.relative_to(root).as_posix())
print(target)
