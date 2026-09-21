from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
p=r'C:/Users/22624/xwechat_files/wxid_kzd6hj99l89u22_f94f/msg/file/2026-09/fudan(1).ttf'
codes=[217,218,219,220]
im=Image.new('RGB',(1400,600),'white')
d=ImageDraw.Draw(im)
for i,c in enumerate(codes):
    x=0;y=i*150
    f=ImageFont.truetype(p,180)
    b=f.getbbox(chr(c)); w=b[2]-b[0]
    if w>1300: f=ImageFont.truetype(p,max(8,int(180*1300/w)))
    b=f.getbbox(chr(c))
    d.text((x+3,y+2),str(c),fill='red')
    d.text((x+48-b[0],y+20-b[1]),chr(c),font=f,fill='black')
im.save('E:/BlenderModel/FudanCampus/fudan_font_glyphs.png')
