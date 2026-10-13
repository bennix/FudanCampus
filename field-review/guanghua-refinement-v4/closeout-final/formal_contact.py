"""Contact sheets for inspection; full-resolution render files remain unchanged."""
from pathlib import Path
import json, hashlib
from PIL import Image, ImageDraw

O = Path(__file__).resolve().parent
source_sha = hashlib.sha256((O/'guanghua-closeout-final.blend').read_bytes()).hexdigest()
rows = json.loads((O/'final-render-manifest.json').read_text(encoding='utf-8'))
rows = [r for r in rows if r['source_sha256'] == source_sha]
for part in range((len(rows)+8)//9):
    sheet = Image.new('RGB', (1800, 1431), '#eeeeee')
    draw = ImageDraw.Draw(sheet)
    for i, r in enumerate(rows[part*9:(part+1)*9]):
        image = Image.open(O/r['image']).convert('RGB')
        image.thumbnail((596, 447))
        x, y = i%3*600, i//3*477
        draw.text((x+8,y+7),r['view'],fill='black')
        sheet.paste(image, (x+(600-image.width)//2,y+26))
    path=O/f'formal-contact-{part+1}.jpg'
    sheet.save(path,quality=93)
    print(path)
