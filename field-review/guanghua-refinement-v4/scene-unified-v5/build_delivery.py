"""Create a compact, traceable handoff for the unified scene after visual review."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageStat
import json,hashlib,html
O=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
M=read(O/'version-manifest.json');V=read(O/'validation.json');R=read(O/'render-manifest.json')
assert M['scene_sha256']==V['scene_sha256']==sha(Path(M['scene']))
review=read(O/'visual-review.json')
assert review['passed'] and review['scene_sha256']==M['scene_sha256'] and len(review['formal_images_reviewed'])==5
titles={'overall':'统一总场景 · 两侧花园、楼前种植坛与东直通道',
 'top':'全场景俯视 · 保持模型中全部可见内容',
 'entry-planters':'楼前左右种植坛 · 四个红绿灌木材质',
 'east-straight-path':'东直通道 · 矩形错缝铺装与齐平浅弧槽边带',
 'entry-material-detail':'楼前材质近景 · IMG_4464 近似机位'}
assert len(R)==5
for r in R:
    p=O/r['image'];assert p.exists() and r['image_sha256']==sha(p)
    assert r['model_sha256']==M['scene_sha256']
    with Image.open(p) as im:
        im.load();assert im.size==(r['width'],r['height']);assert max(ImageStat.Stat(im.convert('RGB')).stddev)>5
        im.convert('RGB').save(O/(r['view']+'.jpg'),quality=94)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
canvas=Image.new('RGB',(1640,1340),'#edf0eb');d=ImageDraw.Draw(canvas)
d.text((28,17),'光华楼前总场景统一 v5 | 三项成果已合并',font=font,fill='#283e33')
for i,r in enumerate(R[:4]):
    x=25+(i%2)*815;y=70+(i//2)*630
    with Image.open(O/r['image']) as im:
        thumb=ImageOps.contain(im.convert('RGB'),(790,570));canvas.paste(thumb,(x+(790-thumb.width)//2,y+(570-thumb.height)//2))
    d.text((x,y+579),titles[r['view']].split(' · ')[0],font=small,fill='#31473b')
d.text((25,1310),'全部图像来自同一检查点；树位、尺度、槽深与用途继承原推定标记。',font=small,fill='#58675c')
canvas.save(O/'delivery-contact.jpg',quality=94)
sha_short=M['scene_sha256'][:16]
brief=f'''# 光华楼前总场景统一 v5 · 交付简报

日期：2026-09-30。三项同源成果已合入 `guanghua-unified-v5.blend`，新整体图均从该检查点重新打开后生成。

[审阅页](review.html) · [可编辑总场景](guanghua-unified-v5.blend) · [整体图](overall.png) · [四图总览](delivery-contact.jpg)

|成果|继承来源|统一结果|
|---|---|---|
|东西花园植被|garden-vegetation-v3|609 个新增网格对象、10 处园内核心材质与旧植物隐藏状态完整保持；新增网格对象数包含树、灌木等组成部分，不等于植株数量|
|楼前左右坛灌木|entry-planters-v5|4 个红绿灌木对象的材质与 metadata 保持，4 张贴图内嵌；坛体与坡道几何沿用 v4|
|草坪东直通道|straight-path-a-v1|200 个通道实体，其中 198 个浅弧槽边带；4 个邻接对象局部裁切保持，73 段旧重复石边删除保持|

三方差异审计无对象冲突。统一场景含 {V['mesh_objects']} 个网格对象，全部按来源逐对象比对：几何/拓扑、世界变换、UV与面设置、材质节点/贴图内容、modifier 几何参数、metadata 和渲染/视口可见性一致。{V['content_owners']['base']} 个白名单外的 v4 网格保持；楼体主体、西入口、曲径和已完成硬景均保留。

**验证通过：** 检查点重开；v4 与三份来源 SHA-256 保持；必要 feature_id 保持；全部网格坐标有限；使用到的图像贴图已打包。200 个通道实体闭合、正体积、零退化面。广场交界全宽重新取 241 点，连续覆盖；最大板面高差约 {V['maximum_stone_face_step']:.8f} 场景单位，指定邻接对象在通道范围内投影交叠面积为 0。填缝处保留原设计的 0.0025 浅凹。

**统一版本入口：** [current-scene.json](../current-scene.json)。后续整体检查、渲染与细化从本版开始。模型 SHA-256：`{M['scene_sha256']}`；五张正式图的模型哈希、相机、分辨率与设置见 [渲染清单](render-manifest.json)。

[全场景俯视](top.png) · [楼前双坛](entry-planters.png) · [楼前材质近景](entry-material-detail.png) · [东直通道](east-straight-path.png) · [差异审计](source-audit.json) · [重开验证](validation.json)

本轮完成成果合并与视觉核验，没有新增几何精修。树位、尺寸、标高、槽深及用途继承各分支的推定标记；校验限定内容保持和指定通道交界，不等于现场测量或全场景碰撞认证。校园网页资产尚未切换到本统一版。

下一单一建议目标：以后续整体图为依据集中审阅三处改动，再决定下一轮细化范围。
'''
(O/'README.md').write_text(brief,encoding='utf-8')
cards=''.join(f'<figure><a href="{r["image"]}"><img src="{r["view"]}.jpg" alt="{titles[r["view"]]}" loading="lazy"></a><figcaption>{titles[r["view"]]}<a href="{r["image"]}">查看原图</a></figcaption></figure>' for r in R)
page=f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼前总场景统一 v5 · 交付简报</title><style>
*{{box-sizing:border-box}}body{{margin:0;color:#263d31;background:#edf0eb;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1450px;margin:auto;padding:32px 25px}}h1{{font-size:32px;margin:7px 0}}h2{{font-size:23px;margin-top:32px}}p{{max-width:1070px}}.tag{{font-size:13px;color:#5d7365;letter-spacing:.08em}}.links{{display:flex;gap:20px;flex-wrap:wrap;margin:18px 0}}a{{color:#315b41}}.status{{display:flex;gap:10px;flex-wrap:wrap;margin:20px 0}}.status span{{background:#dce9d9;padding:5px 12px;border-radius:6px}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}figure{{margin:0;background:#fff;border-radius:10px;overflow:hidden}}figure img{{width:100%;height:auto;display:block}}figcaption{{padding:12px 16px}}figcaption a{{float:right}}table{{width:100%;border-collapse:collapse;background:#fff}}td,th{{padding:12px 15px;border-bottom:1px solid #dce4dc;text-align:left}}th{{background:#dfe7de}}.note{{font-size:14px;color:#607064}}.compare{{position:relative;aspect-ratio:4/3;overflow:hidden}}.compare>img,.after{{position:absolute;inset:0;width:100%;height:100%}}.after img{{width:100%;height:100%}}.after{{clip-path:inset(0 35% 0 0)}}.label{{position:absolute;top:12px;padding:3px 10px;color:white;background:#284b39cc;border-radius:5px}}.left{{left:12px}}.right{{right:12px}}input{{width:calc(100% - 40px);margin:16px 20px}}code{{overflow-wrap:anywhere;font-size:13px}}@media(max-width:800px){{main{{padding:22px 14px}}h1{{font-size:25px}}.grid{{grid-template-columns:1fr}}td,th{{padding:9px}}}}
</style></head><body><main><div class="tag">2026-09-30 · GUANGHUA UNIFIED V5</div><h1>三项成果，统一到同一总场景</h1><p>完整继承花园植被、楼前红绿灌木材质与东直通道的已完成改动。以下五张正式图均重新打开同一个统一检查点生成，使用保存的模型可见性，没有为出图隐藏任何场景网格。</p><div class="status"><span>三方差异无冲突</span><span>检查点重开通过</span><span>来源文件保持</span><span>241 点广场交界通过</span></div><div class="links"><a href="guanghua-unified-v5.blend">可编辑总场景 .blend</a><a href="README.md">交付简报</a><a href="../current-scene.json">当前版本入口</a><a href="delivery-contact.jpg">四图总览</a></div>
<table><thead><tr><th>成果</th><th>继承来源</th><th>保留内容</th></tr></thead><tbody><tr><td>东西花园植被</td><td>garden-vegetation-v3</td><td>609 个新增网格组成部分、10 处园内核心材质、旧植物隐藏状态</td></tr><tr><td>楼前灌木材质</td><td>entry-planters-v5</td><td>4 个灌木对象，4 张贴图内嵌，坛体几何沿用 v4</td></tr><tr><td>东直通道</td><td>straight-path-a-v1</td><td>200 个实体，4 个邻接局部裁切，73 段旧重复石边删除</td></tr></tbody></table>
<h2>统一场景正式渲染</h2><div class="grid">{cards}</div>
<h2>同机位整体对照</h2><p class="note">右侧为已完成植被、尚未合入灌木材质及通道的独立场景；左侧为本统一总场景。拖动查看整体图中的成果差异。</p><figure><div class="compare"><img src="../garden-vegetation-v3/final-overall.jpg" alt="独立植被版整体图"><div class="after"><img src="overall.jpg" alt="统一版整体图"></div><span class="label left">统一 v5</span><span class="label right">独立植被版</span></div><input type="range" min="0" max="100" value="65" aria-label="同机位整体对照" oninput="this.previousElementSibling.querySelector('.after').style.clipPath='inset(0 '+(100-this.value)+'% 0 0)'"></figure>
<h2>核验与后续起点</h2><p>{V['mesh_objects']} 个网格对象按各自来源逐对象一致，{V['content_owners']['base']} 个 v4 白名单外对象保持。检查点重开、坐标有限、feature_id、贴图打包通过。200 个通道实体闭合、正体积、无退化面；广场接口全宽 241 点连续覆盖，指定邻接投影交叠为 0。</p><p>后续整体渲染从 <strong>guanghua-unified-v5.blend</strong> 开始。文件 SHA-256：<code>{M['scene_sha256']}</code>。</p><div class="links"><a href="source-audit.json">三方差异审计</a><a href="validation.json">重开与接口核验</a><a href="version-manifest.json">版本来源清单</a><a href="render-manifest.json">图像/相机与模型哈希</a></div><p class="note">本轮完成合并与视觉核验。树位、尺寸、标高、槽深及用途继承原推定标记；本核验不等于现场测量或全场景碰撞认证。校园网页资产尚未切换到本版。</p></main></body></html>'''
(O/'review.html').write_text(page,encoding='utf-8')
M['status']='complete: merged, reopened, validated, rendered, visually reviewed';M['brief']='README.md';M['review']='review.html';write(O/'version-manifest.json',M)
write(O.parent/'current-scene.json',{'version':M['version'],'date':M['date'],'scene':M['scene'],'scene_sha256':M['scene_sha256'],
 'manifest':str(O/'version-manifest.json'),'review':str(O/'review.html'),'brief':str(O/'README.md'),
 'instruction':'后续整体渲染与细化从此统一检查点开始；禁止从仅含单项改动的分支文件覆盖总场景。'})
# Verify every generated local link, including the inherited comparison image.
from html.parser import HTMLParser
class Links(HTMLParser):
    def handle_starttag(self,tag,attrs):
        for key,value in attrs:
            if key in ('href','src') and value and not value.startswith(('http:','https:','#')):assert (O/value).exists(),value
Links().feed(page)
print('DELIVERY_READY',M['scene_sha256'],flush=True)
