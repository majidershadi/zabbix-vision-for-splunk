"""Render the original eye/pulse app mark into Splunk's required PNG sizes."""
import math
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.tools'))
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'zabbix_vision'/'static'
ASSETS=ROOT/'docs'/'assets'
STATIC.mkdir(parents=True,exist_ok=True)
ASSETS.mkdir(parents=True,exist_ok=True)
mark=Image.new('RGBA',(512,512),(0,0,0,0))
d=ImageDraw.Draw(mark)
d.rounded_rectangle((8,8,504,504),radius=100,fill='#d40000')
upper=[(x,256-109*math.sin(math.pi*(x-63)/386)) for x in range(63,450)]
lower=[(x,256+109*math.sin(math.pi*(x-63)/386)) for x in range(449,62,-1)]
d.polygon(upper+lower,fill='white')
d.ellipse((180,180,332,332),fill='#d40000')
d.line([(185,260),(202,260),(222,218),(247,294),(274,243),(294,260),(325,260)],fill='white',width=14,joint='curve')
d.rounded_rectangle((349,356,466,465),radius=25,fill='#206d3c')
d.line([(377,381),(414,409),(377,438)],fill='white',width=13,joint='curve')
for filename,size in [('appIcon.png',36),('appIcon_2x.png',72),('appIconAlt.png',36),('appIconAlt_2x.png',72)]:
    mark.resize((size,size),Image.Resampling.LANCZOS).save(STATIC/filename)
mark.save(ASSETS/'zabbix-vision-icon.png')
svg='''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><rect x="8" y="8" width="496" height="496" rx="100" fill="#d40000"/><path d="M63 256Q256 38 449 256Q256 474 63 256" fill="#fff"/><circle cx="256" cy="256" r="76" fill="#d40000"/><path d="M185 260h17l20-42 25 76 27-51 20 17h31" fill="none" stroke="white" stroke-width="14" stroke-linejoin="round"/><rect x="349" y="356" width="117" height="109" rx="25" fill="#206d3c"/><path d="m377 381 37 28-37 29" fill="none" stroke="white" stroke-width="13"/></svg>'''
(ASSETS/'zabbix-vision-icon.svg').write_text(svg)
fontpath=Path('C:/Windows/Fonts/segoeuib.ttf')
if not fontpath.exists():
    fontpath=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
for scale in (1,2):
    logo=Image.new('RGBA',(160*scale,40*scale),(0,0,0,0))
    logo.alpha_composite(mark.resize((36*scale,36*scale),Image.Resampling.LANCZOS),(0,2*scale))
    ld=ImageDraw.Draw(logo)
    ld.text((43*scale,1*scale),'Zabbix Vision',font=ImageFont.truetype(str(fontpath),15*scale),fill='#cf171e')
    ld.text((43*scale,23*scale),'for Splunk',font=ImageFont.truetype(str(fontpath),10*scale),fill='#636970')
    logo.save(STATIC/('appLogo.png' if scale==1 else 'appLogo_2x.png'))
print('Rendered six Splunk brand assets and editable SVG mark')
