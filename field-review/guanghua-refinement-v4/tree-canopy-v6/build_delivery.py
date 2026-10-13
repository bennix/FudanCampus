"""Assemble the reviewed native scene handoff. Originals and accepted v5 are untouched."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont,ImageStat
import json,hashlib,html
O=Path(__file__).resolve().parent;ROOT=O.parents[2]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
M=read(O/'version-manifest.json');V=read(O/'validation.json');R=read(O/'final-render-manifest.json');visual=read(O/'visual-review.json')
assert sha(Path(M['scene']))==M['scene_sha256']==V['scene_sha256']==visual['scene_sha256'];assert sha(Path(M['source']))==M['source_sha256'];assert len(R)==7
assert visual['render_inspection_completed'] and set(visual['images_reviewed'])=={r['image'] for r in R}
titles={'overall':'整体 · 草坪开敞与混合树列','top':'俯视 · 原树位与四株杉类树','west-platform':'西花园 · 枝叶轮廓','east-understory':'东花园 · 疏密与分枝','east-exit':'东侧出口 · 疏冠前景','south-walk':'南路 · 高干阔叶树与杉类树','south-elevation':'南侧立面 · 冠幅与间隙'}
for r in R:
    p=O/r['image'];assert r['model_sha256']==M['scene_sha256'] and sha(p)==r['image_sha256']
    with Image.open(p) as im:
        im.load();assert list(im.size)==r['resolution'] and max(ImageStat.Stat(im.convert('RGB')).stddev)>5
        im.convert('RGB').save(O/(r['view']+'.jpg'),quality=94)
for n in ['west-platform','east-understory']:
    with Image.open(O/f'diagnostic1-before-{n}.png') as im:im.convert('RGB').save(O/f'before-{n}.jpg',quality=94)
with Image.open(O/'diagnostic2-before-south-walk.png') as im:im.convert('RGB').save(O/'before-south-walk.jpg',quality=94)
for n,ref in [('west-platform','IMG_4390'),('east-understory','IMG_4582'),('south-walk','IMG_4597'),('east-exit','IMG_4568')]:
    p=ROOT/f'references/guanghua_lawn/img/img/{ref}.jpeg'
    with Image.open(p) as im:
        thumb=ImageOps.contain(im.convert('RGB'),(1400,1050));thumb.save(O/f'reference-{n}.jpg',quality=92)
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
contact=Image.new('RGB',(1640,1340),'#edf0eb');d=ImageDraw.Draw(contact)
d.text((25,17),'树冠复核 v6 | 不规则枝叶 · 降低圆团感 · 南路杉类树',font=font,fill='#243c31')
for i,key in enumerate(['overall','west-platform','south-elevation','east-understory']):
    x=25+(i%2)*815;y=70+(i//2)*625
    with Image.open(O/(key+'.jpg')) as im:thumb=ImageOps.contain(im,(790,568));contact.paste(thumb,(x+(790-thumb.width)//2,y+(568-thumb.height)//2))
    d.text((x,y+577),titles[key],font=small,fill='#31473b')
d.text((25,1310),'照片机位近似；新增树位与尺寸为推定。v5 与阶段源模型未改动。',font=small,fill='#58675c');contact.save(O/'delivery-contact.jpg',quality=94)
esc=html.escape
cards=''.join(f'<figure><a href="{r["view"]}.png"><img loading="lazy" src="{r["view"]}.jpg" alt="{titles[r["view"]]}"></a><figcaption>{titles[r["view"]]}</figcaption></figure>' for r in R)
comparison=''
for key,ref in [('west-platform','IMG_4390'),('east-understory','IMG_4582'),('south-walk','IMG_4597')]:
    comparison+=f'<section class="reference"><h2>{titles[key]}</h2><div class="three"><figure><img loading="lazy" src="reference-{key}.jpg"><figcaption>照片参考 {ref} · 相机仅近似</figcaption></figure><figure><img loading="lazy" src="before-{key}.jpg"><figcaption>统一 v5 · 相同模型机位</figcaption></figure><figure><a href="{key}.png"><img loading="lazy" src="{key}.jpg"></a><figcaption>当前 v6 · 沿枝分布的叶片</figcaption></figure></div></section>'
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼树冠复核 v6</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#edf0eb;color:#273d32;font:16px/1.65 "Microsoft YaHei",sans-serif}}main{{max-width:1480px;margin:auto;padding:30px}}h1{{font-size:29px;line-height:1.4;margin:0 0 12px}}h2{{font-size:21px;margin:28px 0 12px}}p{{max-width:1000px}}a{{color:#285c4e}}.links{{display:flex;gap:22px;flex-wrap:wrap}}.note{{background:#fff;padding:14px 20px;border-left:4px solid #879b70;border-radius:4px}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:22px}}figure{{margin:0;background:#fff;border-radius:8px;overflow:hidden}}figure img{{display:block;width:100%;aspect-ratio:4/3;object-fit:contain;background:#dae0d8}}figcaption{{padding:9px 13px;font-size:14px}}.three{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}}.slider{{position:relative;aspect-ratio:4/3;overflow:hidden;border-radius:8px}}.slider img{{position:absolute;width:100%;height:100%;object-fit:contain}}.slider .after{{clip-path:inset(0 0 0 50%)}}.divider{{position:absolute;left:50%;top:0;bottom:0;width:2px;background:white;box-shadow:0 0 4px #333}}.tags{{display:flex;justify-content:space-between}}input{{width:100%;accent-color:#315a45}}table{{border-collapse:collapse;width:100%;background:#fff}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #dde3da}}footer{{font-size:13px;margin-top:25px;color:#68756a}}@media(max-width:850px){{main{{padding:18px}}.grid,.three{{grid-template-columns:1fr}}}}</style>
<main><h1>光华楼树冠复核 v6</h1><p>根据“太密集、树形圆鼓鼓”的反馈修订：撤回新增阔叶背景树，树叶沿长短不一的枝条分布，保留冠层缺口；南路加入四株杉类树。</p><div class="links"><a href="guanghua-tree-canopy-v6.blend">可编辑复核场景</a><a href="README.md">交付记录</a><a href="delivery-contact.jpg">四图总览</a><a href="../scene-unified-v5/review.html">保留的统一 v5</a></div>
<p class="note">本页用于树形与疏密复核。非目标树的 1,794 个网格对象与 v5 逐项一致，包含楼前灌木、东直通道、车库文字和建筑。照片中的冠形用于约束外观，树枝、精确树位、尺度与杉类物种仍属推定。</p>
<h2>同机位整体前后对照</h2><div class="tags"><span>左侧：统一 v5</span><span>右侧：树冠 v6</span></div><div class="slider"><img src="../scene-unified-v5/overall.jpg" alt="v5"><img class="after" id="after" src="overall.jpg" alt="v6"><i class="divider" id="divider"></i></div><label>拖动分界线 <input id="compare" type="range" min="0" max="100" value="50"></label>
<h2>当前检查点 · 七个视角</h2><div class="grid">{cards}</div>{comparison}
<h2>本阶段检查</h2><table><tr><th>项目</th><th>结果</th></tr><tr><td>v5 文件与回溯资料</td><td>保留；v5 SHA256 未变</td></tr><tr><td>非目标树对象</td><td>1,794 件网格：几何、UV、材质、变换、可见性、属性一致；原文字与相机一致</td></tr><tr><td>新树与原树位</td><td>29 株花园树、16 株南路阔叶树沿用原树位；新增 4 株杉类树经过落地与净距检查</td></tr><tr><td>木质与叶片</td><td>49 个木质网格闭合、正体积，无零面积面；叶片薄面坐标有限</td></tr><tr><td>打包与交界</td><td>4 张楼前材质贴图保持内嵌；200 件东直通道与原 241 点交界检查所涉对象一致</td></tr><tr><td>树几何</td><td>本轮树三角面 {M['new_tree_triangles']:,}，相较被替换树减少 {abs(M['tree_triangle_change_percent']):.1f}%</td></tr></table>
<footer>当前模型 SHA256：{M['scene_sha256']}。全部正式图均从此模型重新打开后生成。近景之前/之后机位一致；照片视点未经精确标定。车库标识字幅与导出、校园网页切换另行处理。</footer></main><script>compare.addEventListener('input',()=>{{after.style.clipPath=`inset(0 0 0 ${{compare.value}}%)`;divider.style.left=compare.value+'%';}})</script></html>'''
(O/'review.html').write_text(page,encoding='utf-8')
brief=f'''# 光华楼树冠复核 v6

从统一 v5 继续，针对“太密集、圆鼓鼓”的反馈完成当前复核版。

[审阅页](review.html) · [可编辑场景](guanghua-tree-canopy-v6.blend) · [四图总览](delivery-contact.jpg)

- 替换原位 29 株花园树与 16 株南路阔叶树；叶片沿不规则细枝分布，保留冠层缺口、长短枝差异和树干倾斜；东侧原疏冠前景保持疏冠。
- 撤回第一版补入的阔叶背景树；南路只新增通过地面、硬景净距筛选的 4 株杉类树，表现直干、窄冠、细枝叶与不均匀层级。
- 第一批过满，第二批过疏；正式版补足细枝叶量，保持第二版的非球形分布。两批诊断与正式批次的模型 SHA 分别记录，诊断图不是最终图。

最终树几何 {M['new_tree_triangles']:,} 个三角面，被替换树原为 {M['old_replaced_tree_triangles']:,} 个，减少 {abs(M['tree_triangle_change_percent']):.2f}%。最终原生场景 {M['scene_bytes']/1024**2:.1f} MiB，较保留的 v5 {Path(M['source']).stat().st_size/1024**2:.1f} MiB 更小。

重开通过；1,794 个非目标树网格的几何、UV、材质节点、变换、可见性与属性全部与 v5 一致。所有原文字及相机保留，两个车库文字仍为“光华楼广场自行车库”。49 个木质网格闭合、正体积、无零面积面；叶片为开放薄面，不按封闭实体体积验收。4 张楼前纹理保持打包。200 件东直通道与 241 点交界审计涉及的网格逐项一致，因此原交界结果保持有效。

七张正式图使用同一最终检查点。总体与俯视同 v5 相机；花园近景之前/之后同机位；照片视点仅近似。南路原诊断第一批方向与参考不同，第二批及正式版已统一为向西看，使用第二批的 v5 对照图。

照片确认的是外观层次、粗干阔叶树与杉类树混植。枝条结构、绝对高度、精确新增树位、数量和具体杉种为推定。当前冠形是程序化复核版本，未声称完成逐树测绘或达到照片完全一致。草坪、道路、建筑、低层灌木、藤架及车库标识几何均沿用 v5。

v5、原始照片和其他阶段源模型本轮均未改动或删除。当前是独立复核场景，校园网页资产尚未切换。下一单项目建议复核车库标识字幅、可读性与模型导出中的文字保留。

模型 SHA256：`{M['scene_sha256']}`

复现：Blender 4.4.3 后台运行 `build_trees.py`；`validate_trees.py` 重开比对；`render_trees.py -- final` 重开同一检查点生成七图。`build_delivery.py` 在图像人工检查记录存在后生成本交付。`expected-snapshot.json`、`baseline-snapshot.json`、`validation.json` 与 `final-render-manifest.json` 保留完整验证记录。
'''
(O/'README.md').write_text(brief,encoding='utf-8')
write(O/'working-scene.json',dict(version='guanghua-tree-canopy-v6',scene=M['scene'],scene_sha256=M['scene_sha256'],source=M['source'],source_sha256=M['source_sha256'],status='native checkpoint validated; visual revision for user review',review=str(O/'review.html'),brief=str(O/'README.md')))
M['status']='native checkpoint validated; seven final renders inspected; visual revision for user review';M['render_manifest']='final-render-manifest.json';M['review']='review.html';write(O/'version-manifest.json',M)
print('DELIVERY_READY',M['scene_sha256'],flush=True)
