"""Build a local DOCX draft with the supplied cover and existing evidence.
Uses stdlib OOXML and Pillow; never modifies models or historical prompt logs.
"""
from pathlib import Path
from xml.etree import ElementTree as E
import zipfile,hashlib,json,re,copy,io
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
REPO=ROOT/'FudanCampus'
FIG=HERE/'figures';FIG.mkdir(exist_ok=True)
FONT='C:/Windows/Fonts/simhei.ttf'
TITLE='基于实地多视角照片与Codex协同的校园建筑参数化细化'
font=lambda size:ImageFont.truetype(FONT,size)

def panel_image(path,size):
    im=ImageOps.exif_transpose(Image.open(path)).convert('RGB')
    return ImageOps.pad(im,size,color='white')

def triple(out,photo,model):
    canvas=Image.new('RGB',(1800,520),'white');d=ImageDraw.Draw(canvas)
    for i,(title,path) in enumerate([('(a) 实地参考原照',photo),('(b) Codex 程序化模型',model)]):
        assert d.textbbox((0,0),title,font=font(32))[2]<580
        d.text((i*600+18,12),title,font=font(32),fill='#222222')
        canvas.paste(panel_image(path,(590,410)),(i*600+5,62))
    title='(c) WebVR 头显视角〔模拟〕'
    assert d.textbbox((0,0),title,font=font(32))[2]<580
    d.text((1218,12),title,font=font(32),fill='#333333')
    building='teaching4' if 'teaching4' in out else 'chemistry'
    simulation=REPO/'field-review/webxr-2026-11-14'/f'{building}-simulation.png'
    if not simulation.exists():raise FileNotFoundError(simulation)
    canvas.paste(panel_image(simulation,(590,410)),(1205,62))
    d.text((18,484),'第三栏为站立视角模拟，非真实头显实测；三栏未作相机配准，仅作定性对比。',font=font(24),fill='#555555')
    canvas.save(FIG/out)

triple('fig02-teaching4-reference.png',ROOT/'assets/17-第四教学楼/正面（不全）.jpg',REPO/'field-review/teaching4-2026-11-14-v4/renders/after-front.png')
triple('fig04-chemistry-reference.png',ROOT/'assets/55-化学楼/正面.jpg',REPO/'field-review/chemistry-2026-11-14-v2/renders/after-front.png')
canvas=Image.new('RGB',(1600,570),'white');d=ImageDraw.Draw(canvas)
for i,(label,path) in enumerate([
    ('第三轮：浅色墙体，外围框缺失',REPO/'field-review/teaching4-2026-11-14-v3/renders/after-rear-window.png'),
    ('第四轮：浅色墙体与窗框同时保留',REPO/'field-review/teaching4-2026-11-14-v4/renders/after-rear-window.png')]):
    d.text((i*800+10,8),label,font=font(26),fill='black');canvas.paste(panel_image(path,(790,520)),(i*800+5,45))
canvas.save(FIG/'fig03-rear-window.png')
Image.open(REPO/'field-review/chemistry-2026-11-14-v2/renders/comparison.png').save(FIG/'fig05-chemistry-color.png')
canvas=Image.new('RGB',(1600,470),'white');d=ImageDraw.Draw(canvas)
labels=['实地照片与示意图','人工标注与空间约束','Codex生成几何脚本','Blender导出与回读','局部替换与网页验收']
for i,label in enumerate(labels):
    x=20+i*318;d.rounded_rectangle((x,80,x+280,220),radius=16,fill='#e5eff7',outline='#55738b',width=3)
    # Fit two lines at meaningful boundaries.
    cuts=['实地照片\n与示意图','人工标注\n与空间约束','Codex生成\n几何脚本','Blender导出\n与回读','局部替换\n与网页验收']
    d.multiline_text((x+25,112),cuts[i],font=font(27),fill='#24384a',spacing=12)
    if i<4:d.line((x+285,150,x+312,150),fill='#55738b',width=4);d.polygon([(x+312,150),(x+302,143),(x+302,157)],fill='#55738b')
d.line((1445,240,1445,315,460,315,460,245),fill='#a85c4b',width=4)
d.polygon([(460,235),(453,250),(467,250)],fill='#a85c4b')
d.text((650,337),'人工反馈：体块、开敞关系、构件保留、颜色与资源是否更新',font=font(25),fill='#7a4236')
d.text((25,415),'边界：备份旧版，只修改17/55；推定尺寸与未实测结果单独标明。',font=font(24),fill='#555555')
canvas.save(FIG/'fig01-pipeline.png')

# Appendix A copies immutable historical evidence into a separate paper bundle.
logs=sorted((REPO/'prompts_log').rglob('*'))
index=[];interactions=[]
with zipfile.ZipFile(HERE/'附录A_历史交互与输出.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in logs:
        if not p.is_file():continue
        data=p.read_bytes();rel=p.relative_to(REPO).as_posix()
        archive.writestr(rel,data);index.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        if p.name in ['interaction.txt','user-prompt.txt','decisions-and-errors.md']:
            interactions.append((rel,data.decode('utf-8-sig')))
    archive.writestr('文件索引.json',json.dumps(index,ensure_ascii=False,indent=2).encode('utf8'))
(HERE/'附录A_文件索引.json').write_text(json.dumps(index,ensure_ascii=False,indent=2),encoding='utf8')

inventory=[]
for folder in ['17-第四教学楼','55-化学楼']:
    for p in sorted((ROOT/'assets'/folder).iterdir()):
        if p.suffix.lower() not in ['.png','.jpg','.jpeg']:continue
        im=Image.open(p);exif=im.getexif();date=exif.get(36867) or exif.get(306)
        kind='人工标注' if '标注' in p.name else '地图/形状示意截图' if '形状' in p.name else '实拍照片'
        inventory.append(dict(id=f'B{len(inventory)+1:02d}',building=folder,path=p.relative_to(ROOT).as_posix(),
                              filename=p.name,pixels=list(im.size),bytes=p.stat().st_size,type=kind,
                              exif_date=str(date) if date else '未知/未读取到',
                              source='用户实地拍摄' if kind=='实拍照片' else '高德地图截图，用户确认；截图日期/缩放级别待核' if kind=='地图/形状示意截图' else '用户制作标注，制作时间未核实',
                              sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
guide=REPO/'web/public/campus-map.png';guide_image=Image.open(guide)
inventory.append(dict(id='B19',building='既有校园导览图',path=guide.relative_to(ROOT).as_posix(),filename=guide.name,pixels=list(guide_image.size),bytes=guide.stat().st_size,type='既有校园导览图/比例尺校核',exif_date='未知',source='既有项目资产；图面标题为Fudan University Campus Map，原发布方/年份待核；不能混同用户高德截图',sha256=hashlib.sha256(guide.read_bytes()).hexdigest()))
gaode=ROOT/'assets/比例尺-来源高德地图.jpeg';gaode_image=Image.open(gaode)
inventory.append(dict(id='B20',building='55-化学楼尺度参照',path=gaode.relative_to(ROOT).as_posix(),filename=gaode.name,pixels=list(gaode_image.size),bytes=gaode.stat().st_size,type='高德地图/25米比例尺截图',exif_date='未知；分析日期2026-11-15不等于截图日期',source='高德地图，用户确认；同幅25米标尺与化学楼主体，用于地图估算，非实地测距',sha256=hashlib.sha256(gaode.read_bytes()).hexdigest()))
(HERE/'附录B_参考图像元数据.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf8')

NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
    'a':'http://schemas.openxmlformats.org/drawingml/2006/main',
    'pic':'http://schemas.openxmlformats.org/drawingml/2006/picture',
    'rel':'http://schemas.openxmlformats.org/package/2006/relationships',
    'ct':'http://schemas.openxmlformats.org/package/2006/content-types'}
for prefix,uri in NS.items():E.register_namespace(prefix,uri)
def q(tag):prefix,local=tag.split(':');return '{'+NS[prefix]+'}'+local
def sub(parent,tag,attrs=None,text=None):
    e=E.SubElement(parent,q(tag),{q(k) if ':' in k else k:str(v) for k,v in (attrs or {}).items()})
    if text is not None:e.text=text
    return e
def paragraph(text='',size=24,bold=False,align=None,indent=True,keep=False,mono=False):
    p=E.Element(q('w:p'));pr=sub(p,'w:pPr');sub(pr,'w:spacing',{'w:line':360,'w:lineRule':'auto','w:after':60})
    if align:sub(pr,'w:jc',{'w:val':align})
    if indent:sub(pr,'w:ind',{'w:firstLine':480})
    if keep:sub(pr,'w:keepNext')
    r=sub(p,'w:r');rp=sub(r,'w:rPr')
    sub(rp,'w:rFonts',{'w:ascii':'Consolas' if mono else 'Times New Roman','w:hAnsi':'Consolas' if mono else 'Times New Roman','w:eastAsia':'宋体'})
    sub(rp,'w:sz',{'w:val':size});sub(rp,'w:szCs',{'w:val':size})
    if bold:sub(rp,'w:b')
    sub(r,'w:t',{'xml:space':'preserve'} if False else {},text=text)
    return p
def table(rows):
    tbl=E.Element(q('w:tbl'));pr=sub(tbl,'w:tblPr');sub(pr,'w:tblW',{'w:w':0,'w:type':'auto'})
    borders=sub(pr,'w:tblBorders')
    for edge in ['top','left','bottom','right','insideH','insideV']:sub(borders,'w:'+edge,{'w:val':'single','w:sz':4,'w:color':'B0B0B0'})
    grid=sub(tbl,'w:tblGrid')
    for _ in rows[0]:sub(grid,'w:gridCol',{'w:w':int(9000/len(rows[0]))})
    for i,row in enumerate(rows):
        tr=sub(tbl,'w:tr')
        if i==0:sub(sub(tr,'w:trPr'),'w:tblHeader')
        for value in row:
            tc=sub(tr,'w:tc');tcp=sub(tc,'w:tcPr');sub(tcp,'w:tcW',{'w:w':int(9000/len(row)),'w:type':'dxa'})
            if i==0:sub(tcp,'w:shd',{'w:fill':'E9EEF3'})
            tc.append(paragraph(str(value),size=20,bold=i==0,indent=False))
    return tbl

template=ROOT/'虚拟现导引_论文封面.docx'
with zipfile.ZipFile(template) as z:files={name:z.read(name) for name in z.namelist()}
document=E.fromstring(files['word/document.xml']);body=document.find(q('w:body'))
# ElementTree renames extension namespace prefixes; remove the old, now stale
# compatibility prefix list rather than leaving undefined w14/w15/wp14 names.
document.attrib.pop('{http://schemas.openxmlformats.org/markup-compatibility/2006}Ignorable',None)
# Keep the supplied cover's layout; replace only author placeholders and title.
for p in body.findall('w:p',NS):
    text=''.join(p.itertext())
    replacement=None
    if '学生姓名' in text:replacement='学生姓名：［待填写］    学号：［待填写］    专业：［待填写］'
    if '论文名称' in text:replacement='论文名称：'+TITLE
    if replacement:
        pp=p.find(q('w:pPr'))
        for c in list(p):
            if c is not pp:p.remove(c)
        r=sub(p,'w:r');rp=sub(r,'w:rPr');sub(rp,'w:rFonts',{'w:eastAsia':'宋体','w:ascii':'Times New Roman'});sub(rp,'w:sz',{'w:val':24});sub(r,'w:t',text=replacement)
cover_section=body.find(q('w:sectPr'))
if cover_section is not None:body.remove(cover_section)
else:cover_section=E.Element(q('w:sectPr'))
breakp=E.Element(q('w:p'));bp=sub(breakp,'w:pPr');bp.append(copy.deepcopy(cover_section));cover_copy=bp.find(q('w:sectPr'));section_type=E.Element(q('w:type'),{q('w:val'):'nextPage'});cover_copy.insert(0,section_type);body.append(breakp)
rels=E.fromstring(files['word/_rels/document.xml.rels'])
types=E.fromstring(files['[Content_Types].xml'])
image_count=0
def add_image(path,caption):
    global image_count
    image_count+=1;rid=f'rIdPaperImage{image_count}';name=f'paper-figure-{image_count}.png'
    files['word/media/'+name]=path.read_bytes()
    sub(rels,'rel:Relationship',{'Id':rid,'Type':NS['r']+'/image','Target':'media/'+name})
    im=Image.open(path);width=5600000;height=round(width*im.height/im.width)
    p=E.Element(q('w:p'));sub(sub(p,'w:pPr'),'w:jc',{'w:val':'center'})
    inline=sub(sub(sub(p,'w:r'),'w:drawing'),'wp:inline');sub(inline,'wp:extent',{'cx':width,'cy':height});sub(inline,'wp:docPr',{'id':100+image_count,'name':caption})
    graphic=sub(inline,'a:graphic');gd=sub(graphic,'a:graphicData',{'uri':NS['pic']});pic=sub(gd,'pic:pic');nv=sub(pic,'pic:nvPicPr');sub(nv,'pic:cNvPr',{'id':0,'name':name});sub(nv,'pic:cNvPicPr')
    fill=sub(pic,'pic:blipFill');sub(fill,'a:blip',{'r:embed':rid});sub(sub(fill,'a:stretch'),'a:fillRect')
    shape=sub(pic,'pic:spPr');xf=sub(shape,'a:xfrm');sub(xf,'a:off',{'x':0,'y':0});sub(xf,'a:ext',{'cx':width,'cy':height});sub(sub(shape,'a:prstGeom',{'prst':'rect'}),'a:avLst')
    body.append(p);body.append(paragraph(caption,size=21,align='center',indent=False))

text=(HERE/'正文初稿.txt').read_text(encoding='utf8');lines=text.splitlines();i=0;table_no=0
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line.startswith('【图'):
        path,caption=line.split('】',1)[1].split('|',1);add_image(HERE/path,caption);continue
    if line.startswith('【表'):
        table_no+=1;body.append(paragraph(f'表{table_no}　'+{1:'建筑构件解构与推定参数',2:'最终正式模型及远景资源统计',3:'软件渲染环境下受控对照（每组3轮）',4:'外部开发效能研究及适用边界'}[table_no],size=21,align='center',indent=False,keep=True))
        rows=[line.split('】',1)[1].split('|')]
        while i<len(lines) and lines[i]!='【表终】':rows.append(lines[i].split('|'));i+=1
        i+=1;body.append(table(rows));continue
    if line=='【附录A全文】':
        for name,content in interactions:
            body.append(paragraph(name,size=22,bold=True,indent=False,keep=True))
            for raw in content.splitlines():
                if raw.strip():body.append(paragraph(raw,size=19,indent=False))
        continue
    if line=='【附录B表】':
        body.append(paragraph('表B1　参考图像清单（完整哈希见附带JSON）',size=21,align='center',indent=False,keep=True))
        body.append(table([['编号/建筑','文件名','类型/像素','拍摄日期','SHA256前12位']]+[[a['id']+'/'+a['building'].split('-')[0],a['filename'],a['type']+'\n'+'×'.join(map(str,a['pixels'])),a['exif_date'],a['sha256'][:12]] for a in inventory]))
        continue
    if line=='【附录C表】':
        body.append(paragraph('表C1　关键代码与复现入口',size=21,align='center',indent=False,keep=True))
        entries=[('scripts/teaching4_geometry.py','第四教学楼参数化生成'),('scripts/chemistry_geometry.py','化学楼轮廓、窗与门廊'),('field-review/teaching4-2026-11-14-v4/build_review.py','第四教学楼生成、渲染及回读'),('field-review/chemistry-2026-11-14-v2/build_review.py','化学楼生成与指定砖色'),('field-review/chemistry-2026-11-14-v2/verify_color.py','导出色值与几何字节比较'),('scripts/build_lods.py + web/pack-lods.mjs','目标LOD生成与打包'),('web/build-walk-collision.mjs + scripts/union_walk_interiors.py','碰撞与屋顶投影'),('web/lib/campus-lod.ts + lod-policy.ts','既有LOD加载与预算策略'),('web/lib/campus-walk.ts + web/app/page.tsx','既有步行与网页入口'),('web/lib/head-simulation.ts + immersive-policy.ts','米制站立视角、无侧倾转头、指数平滑'),('web/lib/campus-lab.ts + frame-metrics.ts','模拟/WebXR入口、截图与原始帧统计'),('web/experiment-browser.mjs','本地CDP实验复现'),('scripts/check_chemistry_gaode_scale.py','高德25米同幅读数、模型参数与尺度关系校核'),('scripts/check_teaching4_map_scale.py','旧导览图比例尺不自洽记录'),('tools/Enter-Blender.ps1','Blender4.4.3 CLI入口')]
        body.append(table([['仓库内路径','作用']]+entries))
        for cmd in ['. ./tools/Enter-Blender.ps1','blender --version','cd web','npm run dev -- --host 127.0.0.1 --port 5173','npm run test:lod','npm run test:walk','npm run build:pages']:
            body.append(paragraph(cmd,size=20,indent=False,mono=True))
        continue
    is_heading=bool(re.match(r'^\d+(\.\d+)?\s',line)) or line in ['摘要','参考文献'] or line.startswith('附录')
    if i<=2:body.append(paragraph(line,size=32 if i==1 else 26,bold=True,align='center',indent=False,keep=True))
    elif is_heading:
        p=paragraph(line,size=28 if not re.match(r'^\d+\.\d+',line) else 25,bold=True,indent=False,keep=True)
        sub(p.find(q('w:pPr')),'w:outlineLvl',{'w:val':1 if re.match(r'^\d+\.\d+',line) else 0});body.append(p)
    else:body.append(paragraph(line,indent=not line.startswith(('作者','课程','关键词','['))))

section=sub(body,'w:sectPr');sub(section,'w:footerReference',{'w:type':'default','r:id':'rIdPaperFooter'});sub(section,'w:pgSz',{'w:w':11906,'w:h':16838})
sub(section,'w:pgMar',{'w:top':1440,'w:right':1440,'w:bottom':1440,'w:left':1440,'w:header':720,'w:footer':720,'w:gutter':0})
sub(section,'w:pgNumType',{'w:start':1})
footer=E.Element(q('w:ftr'));p=sub(footer,'w:p');sub(sub(p,'w:pPr'),'w:jc',{'w:val':'center'})
run=sub(p,'w:r');sub(run,'w:fldChar',{'w:fldCharType':'begin'});sub(sub(p,'w:r'),'w:instrText',text=' PAGE ');sub(sub(p,'w:r'),'w:fldChar',{'w:fldCharType':'end'})
files['word/footer-paper.xml']=E.tostring(footer,encoding='utf-8',xml_declaration=True)
sub(rels,'rel:Relationship',{'Id':'rIdPaperFooter','Type':NS['r']+'/footer','Target':'footer-paper.xml'})
sub(types,'ct:Override',{'PartName':'/word/footer-paper.xml','ContentType':'application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml'})
if not any(e.get('Extension')=='png' for e in types):sub(types,'ct:Default',{'Extension':'png','ContentType':'image/png'})
files['word/document.xml']=E.tostring(document,encoding='utf-8',xml_declaration=True)
files['word/_rels/document.xml.rels']=E.tostring(rels,encoding='utf-8',xml_declaration=True)
files['[Content_Types].xml']=E.tostring(types,encoding='utf-8',xml_declaration=True)
output=HERE/'课程论文更新稿_三联图对比分析.docx'
with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED) as z:
    for name,data in files.items():z.writestr(name,data)
with zipfile.ZipFile(output) as z:
    assert z.testzip() is None
    for name in z.namelist():
        if name.endswith('.xml'):E.fromstring(z.read(name))
body_count=len(re.findall('[\u4e00-\u9fff]',text.split('\n参考文献\n')[0]))
report={'正文汉字数_含摘要表格图题':body_count,'摘要字符数':len(text.split('摘要\n')[1].split('\n\n关键词')[0]),
        '参考图像数':len(inventory),'插图数':image_count,'附录A纳入文件数':len(index),'附录A正文全文文件数':len(interactions),
        '封面模板':template.name,'身份信息':'待作者填写','头显截图与FPS':'模拟图与桌面性能对照已补；真实设备未实测','DOCX_ZIP和XML检查':'通过'}
(HERE/'初稿检查结果.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(report,ensure_ascii=False));print(output)
