"""Convert browser captures to PNG and make proportionally reduced previews.

No UI data is generated or painted over. Previews use neutral letterboxing.
"""
import html
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.tools'))
from PIL import Image

MEDIA = ROOT / 'docs/screenshots/splunkbase'
ORIGINALS = ROOT / '.release/screenshots'
PREVIEWS = MEDIA / 'previews'
ORIGINALS.mkdir(parents=True, exist_ok=True)
PREVIEWS.mkdir(exist_ok=True)
for source in sorted(MEDIA.glob('*.jpg')):
    with Image.open(source) as capture:
        capture.convert('RGB').save(source.with_suffix('.png'), optimize=True)
    destination = ORIGINALS / source.name
    assert source.resolve().is_relative_to(ROOT)
    assert destination.resolve().is_relative_to(ROOT)
    source.replace(destination)

titles = {
    '01-operations': 'Operations overview',
    '02-audit-authentication': 'Audit & authentication',
    '03-infrastructure': 'Infrastructure inventory',
    '04-agent-execution': 'Scripts & agent activity',
    '05-collector-health': 'Collector health',
    '06-connections-tls': 'Connections and TLS controls',
    '07-metrics': 'Metrics & trends',
}
cards = []
for source in sorted(MEDIA.glob('*.png')):
    with Image.open(source) as capture:
        capture = capture.convert('RGB')
        capture.thumbnail((623, 350), Image.Resampling.LANCZOS)
        canvas = Image.new('RGB', (623, 350), '#edf1f4')
        canvas.paste(capture, ((623-capture.width)//2, (350-capture.height)//2))
        canvas.save(PREVIEWS / source.name, optimize=True)
    title = html.escape(titles[source.stem])
    path = '../docs/screenshots/splunkbase/' + source.name
    cards.append(f'<article><h2>{title}</h2><a href="{path}"><img src="{path}" alt="{title}: real Splunk lab capture"></a><p><a href="{path}" download>Full PNG</a> · <a href="../docs/screenshots/splunkbase/previews/{source.name}" download>623 × 350 preview</a></p></article>')

(ROOT / 'splunkbase/GALLERY.html').write_text('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Zabbix Vision — Splunkbase screenshots</title><style>body{margin:0;background:#eef2f5;color:#182c36;font:16px system-ui}header,main{max-width:1280px;margin:auto;padding:32px}header{border-top:8px solid #d40000}header img{width:54px;float:left;margin-right:18px}h1{margin:0 0 8px}p{line-height:1.6}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:24px;padding-top:0}article{background:white;padding:20px;border:1px solid #d9e1e6;border-radius:12px}h2{font-size:20px}article img{width:100%;height:430px;object-fit:contain;background:#eef2f5}a{color:#a70000}footer{max-width:1280px;margin:auto;padding:0 32px 40px}</style><header><img src="../docs/assets/zabbix-vision-icon.png" alt="App icon"><h1>Zabbix Vision for Splunk</h1><p>Splunkbase media kit · 1.0.0 beta · Captured 30 October 2026</p><p>Real Splunk Enterprise 10.4.1 screens. Click any image for full detail. Read <a href="SCREENSHOTS.md">captions and test-data context</a> before publishing. Previews are letterboxed, proportionally reduced captures; no data is altered.</p></header><main>''' + ''.join(cards) + '''</main><footer>Use START_HERE.md for the submission checklist. Empty panels, lab backfill lag and prototype history are explained in SCREENSHOTS.md.</footer></html>''', encoding='utf-8')
print('Prepared', len(cards), 'full PNG captures, 623x350 previews, and GALLERY.html')
