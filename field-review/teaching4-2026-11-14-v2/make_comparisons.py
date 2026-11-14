"""Lay out unaltered reference thumbnails and matched-camera renders for review."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
PHOTOS=HERE.parents[2]/'assets/17-第四教学楼'
font=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',24)
small=ImageFont.truetype('C:/Windows/Fonts/simhei.ttf',19)
rows=[('第二轮平面：东翼退让 / 花坛对齐 / 西侧草坪','第四教学楼二轮修改标注.png','plan'),
      ('第二轮背面：端部层间小窗 / 底层浅色细框 / 后门平台','背面二轮修改标注.jpg','rear'),
      ('第二轮正门：删除入口两侧封闭墙板','正面（不全）.jpg','entry'),
      ('第二轮正面：退让东翼与开敞入口','正面（微侧，仰拍）.jpg','front'),
      ('第二轮侧门：随退让东翼整体后移','正右侧（仰拍）雕像后方.jpg','side-door'),
      ('第二轮花坛：缩短并东移，雕塑一同调整','正面右下方雕像.jpg','sculpture')]
for title,photo,key in rows:
    sheet=Image.new('RGB',(1800,525),'#f1f0ec')
    draw=ImageDraw.Draw(sheet)
    draw.text((18,10),title,font=font,fill='#202020')
    for col,(label,path) in enumerate([
        ('用户标注／参考照片',PHOTOS/photo),
        ('第一轮模型',HERE/f'renders/before-{key}.png'),
        ('第二轮模型（已接入网页后验收）',HERE/f'renders/after-{key}.png')]):
        with Image.open(path) as source:
            thumb=ImageOps.contain(source.convert('RGB'),(588,410))
            sheet.paste(thumb,(col*600+(600-thumb.width)//2,76+(410-thumb.height)//2))
        draw.text((col*600+16,47),label,font=small,fill='#444444')
    draw.text((18,497),'照片与模型视点不同，仅用于构件核对；前后模型使用同一相机。尺寸为比例推定。',font=small,fill='#555555')
    sheet.save(HERE/f'comparison-{key}.jpg',quality=93)
print('COMPARISON_SHEETS_READY')
