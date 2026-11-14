"""Lay out unaltered reference thumbnails and matched-camera renders for review."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
PHOTOS=HERE.parents[2]/'assets/17-第四教学楼'
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
small=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',19)
rows=[('正面：两组右窗 / 阳台 / 凹进门厅','正面（微侧，仰拍）.jpg','front'),
      ('背面：楼梯塔高度 / 四列分格窄窗','背面.jpg','rear'),
      ('右端：小侧门 / 金属雨棚 / 台阶扶手','正右侧（仰拍）雕像后方.jpg','side-door'),
      ('雕塑：凹弧书口 / 石材纹理 / 花坛','正面右下方雕像.jpg','sculpture')]
for title,photo,key in rows:
    sheet=Image.new('RGB',(1800,525),'#f1f0ec')
    draw=ImageDraw.Draw(sheet)
    draw.text((18,10),title,font=font,fill='#202020')
    for col,(label,path) in enumerate([
        ('实地照片（含原有人工标线）',PHOTOS/photo),
        ('细化前',HERE/f'renders/before-{key}.png'),
        ('候选 v1（待人工验收）',HERE/f'renders/after-{key}.png')]):
        with Image.open(path) as source:
            thumb=ImageOps.contain(source.convert('RGB'),(588,410))
            sheet.paste(thumb,(col*600+(600-thumb.width)//2,76+(410-thumb.height)//2))
        draw.text((col*600+16,47),label,font=small,fill='#444444')
    draw.text((18,497),'照片与模型视点不同，仅用于构件核对；前后模型使用同一相机。尺寸为比例推定。',font=small,fill='#555555')
    sheet.save(HERE/f'comparison-{key}.jpg',quality=93)
print('COMPARISON_SHEETS_READY')
