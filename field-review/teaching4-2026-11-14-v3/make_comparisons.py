"""Lay out unaltered reference thumbnails and matched-camera renders for review."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
PHOTOS=HERE.parents[2]/'assets/17-第四教学楼'
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
small=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',19)
rows=[('第三轮标注窗：去外围黑框，保留浅色内部窗格','背面三轮修改标注.jpg','rear-window'),
      ('第三轮前庭：扩大草坪，补较大阔叶树','正面（不全）.jpg','front'),
      ('第三轮平面：草坪两端对齐 / 局部树木','第四教学楼二轮修改标注.png','plan'),
      ('第三轮背面：标注窗及楼旁树木','背面.jpg','rear')]
for title,photo,key in rows:
    sheet=Image.new('RGB',(1800,525),'#f1f0ec')
    draw=ImageDraw.Draw(sheet)
    draw.text((18,10),title,font=font,fill='#202020')
    for col,(label,path) in enumerate([
        ('用户标注／参考照片',PHOTOS/photo),
        ('第二轮模型',HERE/f'renders/before-{key}.png'),
        ('第三轮模型',HERE/f'renders/after-{key}.png')]):
        with Image.open(path) as source:
            thumb=ImageOps.contain(source.convert('RGB'),(588,410))
            sheet.paste(thumb,(col*600+(600-thumb.width)//2,76+(410-thumb.height)//2))
        draw.text((col*600+16,47),label,font=small,fill='#444444')
    draw.text((18,497),'照片与模型视点不同，仅用于构件核对；前后模型使用同一相机。尺寸为比例推定。',font=small,fill='#555555')
    sheet.save(HERE/f'comparison-{key}.jpg',quality=93)
print('COMPARISON_SHEETS_READY')
