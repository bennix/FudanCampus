from PIL import Image, ImageOps, ImageDraw
from pathlib import Path
O=Path(__file__).resolve().parent
root=O.parents[2]
ids=[4464,4485,4480,4568,4574,4567,4390,4582,4597,4424,4416,4468,4603,4547,4357,4453,4505,4492]
sheet=Image.new('RGB',(1500,300*6),'#eeeeee');draw=ImageDraw.Draw(sheet)
for i,pid in enumerate(ids):
 p=next((root/'references/guanghua_lawn').rglob(f'IMG_{pid}.jpeg'))
 im=ImageOps.exif_transpose(Image.open(p)); im.thumbnail((490,270))
 x=(i%3)*500;y=(i//3)*300
 sheet.paste(im,(x+(500-im.width)//2,y+24));draw.text((x+10,y+5),f'IMG_{pid}',fill='black')
sheet.save(O/'reference-contact.jpg')
