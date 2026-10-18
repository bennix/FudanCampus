"""Read-only source photo inventory and derived contact sheets for survey review."""
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont
import json, math, hashlib, concurrent.futures

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'references/guanghua_lawn/img/img'
OUT = ROOT / 'field-review/guanghua-lawn-survey-v1'
OUT.mkdir(exist_ok=True)
(OUT / 'thumbs').mkdir(exist_ok=True)
(OUT / 'sheets').mkdir(exist_ok=True)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)

def dms(v): return float(v[0])+float(v[1])/60+float(v[2])/3600
def read(p):
    with Image.open(p) as im:
        e=im.getexif(); sub=e.get_ifd(34665); gps=e.get_ifd(34853)
        lat=dms(gps[2])*(-1 if gps.get(1)=='S' else 1) if 2 in gps else None
        lon=dms(gps[4])*(-1 if gps.get(3)=='W' else 1) if 4 in gps else None
        row=dict(file=p.name,number=int(p.stem.split('_')[-1]),width=im.width,height=im.height,
                 time=sub.get(36867,e.get(306)),offset=sub.get(36881),lat=lat,lon=lon,
                 heading=float(gps[17]) if 17 in gps else None,
                 gps_error_m=float(gps[31]) if 31 in gps else None,
                 focal35=sub.get(41989),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        t=ImageOps.exif_transpose(im).convert('RGB');t.thumbnail((600,450))
        t.save(OUT/'thumbs'/p.name,quality=84)
        return row

with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    rows=list(pool.map(read,sorted(SRC.glob('*.jpeg'))))
rows.sort(key=lambda r:(r['time'] or '',r['number']))
for i,r in enumerate(rows): r['sequence']=i+1
(OUT/'photos.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
for start in range(0,len(rows),20):
    sheet=Image.new('RGB',(2000,1320),'#f4f2eb');draw=ImageDraw.Draw(sheet)
    for j,r in enumerate(rows[start:start+20]):
        x=(j%5)*400;y=(j//5)*330
        with Image.open(OUT/'thumbs'/r['file']) as im:
            im.thumbnail((390,292));sheet.paste(im,(x+(400-im.width)//2,y+(292-im.height)//2))
        draw.text((x+8,y+296),f"{r['sequence']:03d}  {r['file']}  {(r['time'] or '')[-8:]}",font=font,fill='#162e2a')
    sheet.save(OUT/'sheets'/f'sheet-{start//20+1:02}.jpg',quality=92)
print(json.dumps(dict(count=len(rows),gps=sum(r['lat'] is not None for r in rows),headings=sum(r['heading'] is not None for r in rows),first=rows[0]['time'],last=rows[-1]['time'],min_number=min(r['number'] for r in rows),max_number=max(r['number'] for r in rows))))
