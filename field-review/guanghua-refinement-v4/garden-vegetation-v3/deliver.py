from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
import json,html
O=Path(__file__).resolve().parent;R=O.parents[2]
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
titles={'east-exit':'东花园 · 出口近景','east-garden':'东花园 · 灌木与树冠','west-garden':'西花园 · 种植层次','west-platform':'西花园 · 平台近景','east-understory':'东花园 · 林下灌木','overall':'东西花园 · 全景'}
for key in titles:
    assert (O/('final-'+key+'.png')).exists(),key
    with Image.open(O/('final-'+key+'.png')) as im:im.convert('RGB').save(O/('final-'+key+'.jpg'),quality=93)
canvas=Image.new('RGB',(1840,1570),'#eef1e9');d=ImageDraw.Draw(canvas)
d.text((30,22),'东西花园植被 · 最终渲染',font=font,fill='#213d2d')
for i,key in enumerate(['west-garden','east-garden','west-platform','east-exit']):
    x=30+(i%2)*915;y=84+(i//2)*732
    im=Image.open(O/('final-'+key+'.png')).convert('RGB');im.thumbnail((885,665));canvas.paste(im,(x,y))
    d.text((x,y+674),titles[key],font=small,fill='#284033')
canvas.save(O/'final-contact.jpg',quality=94)
for key,photo in [('east-exit',4568),('west-platform',4390),('east-understory',4582)]:
    sheet=Image.new('RGB',(1840,780),'#eef1e9');d=ImageDraw.Draw(sheet)
    d.text((28,20),titles[key]+' · 照片与模型观感对照',font=font,fill='#213d2d')
    for i,(path,label) in enumerate([(R/f'references/guanghua_lawn/img/img/IMG_{photo}.jpeg',f'现场照片 IMG_{photo}'),(O/('final-'+key+'.png'),'本轮渲染（近似视角）')]):
        im=Image.open(path).convert('RGB');im=ImageOps.contain(im,(885,665));x=30+i*915;sheet.paste(im,(x,75));d.text((x,742),label,font=small,fill='#284033')
    sheet.save(O/('photo-comparison-'+key+'.jpg'),quality=94)
report=json.loads((O/'validation.json').read_text(encoding='utf-8'))
assert report.get('renders_complete') and report.get('checkpoint_reopened')
cards=''.join(f'<figure><a href="final-{k}.png"><img src="final-{k}.jpg" alt="{v}" loading="lazy"></a><figcaption>{v} <a href="final-{k}.png">原图</a></figcaption></figure>' for k,v in titles.items())
comparisons=''.join(f'<figure><img src="photo-comparison-{k}.jpg" alt="照片对照" loading="lazy"><figcaption>{titles[k]} · 现场照片与近似视角</figcaption></figure>' for k in ['east-exit','west-platform','east-understory'])
sliders=''.join(f'<article><h3>{titles[k]}</h3><div class="compare"><img src="before-{k}.png" alt="修改前"><div class="after"><img src="final-{k}.jpg" alt="修改后"></div><span class="left">修改后</span><span class="right">修改前</span></div><input type="range" min="0" max="100" value="65" aria-label="前后对比" oninput="this.previousElementSibling.querySelector(\'.after\').style.clipPath=\'inset(0 \'+(100-this.value)+\'% 0 0)\'"></article>' for k in ['west-garden','east-garden','east-exit'])
page=f'''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>东西花园植被 · 最终渲染</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#edf0e7;color:#253d2c;font:16px/1.65 system-ui,"Microsoft YaHei",sans-serif}}main{{max-width:1500px;margin:auto;padding:36px 25px}}h1{{font-size:32px;margin:0 0 8px}}h2{{font-size:24px;margin-top:40px}}p{{max-width:960px}}a{{color:#3e6248}}.links{{display:flex;gap:22px;flex-wrap:wrap;padding:14px 0}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px}}figure,article{{margin:0;background:white;border-radius:12px;overflow:hidden;box-shadow:0 4px 20px #1538210c}}img{{display:block;width:100%;height:auto}}figcaption{{padding:13px 18px}}figcaption a{{float:right}}article h3{{margin:12px 18px}}.compare{{position:relative;aspect-ratio:4/3}}.compare>img,.after{{position:absolute;inset:0;width:100%;height:100%}}.after{{clip-path:inset(0 35% 0 0)}}.left,.right{{position:absolute;top:12px;padding:3px 10px;background:#163a2abd;color:white;border-radius:5px}}.left{{left:12px}}.right{{right:12px}}input{{display:block;width:calc(100% - 32px);margin:18px 16px}}.evidence figure{{margin-bottom:18px}}.note{{font-size:14px;color:#637263}}@media(max-width:800px){{.grid{{grid-template-columns:1fr}}main{{padding:24px 14px}}h1{{font-size:25px}}}}
</style><main><h1>东西花园植被 · 最终渲染</h1><p>重点补足林下灌木与地被，改善树冠、枝条、绿篱和藤叶的层次。西花园采用成熟密冠和混合灌木背景，东花园保留疏叶枝系并补足常绿种植。</p><div class="links"><a href="garden-vegetation-v3.blend">可编辑 Blender 模型</a><a href="final-contact.jpg">渲染总览</a><a href="validation.json">完成记录</a></div><div class="grid">{cards}</div><h2>同机位前后对比</h2><p class="note">拖动滑块查看。本轮已保留现有通道、楼前两侧花坛、台阶、栏杆、主草坪及建筑；对照中的旧铺装与构筑物由其他任务继续处理。</p><div class="grid">{sliders}</div><h2>照片观感对照</h2><div class="evidence">{comparisons}</div><p class="note">照片确认植物层次与大致习性。额外灌木密度按用户要求补充，株数、种类、尺度与相机位置均为视觉推定。结果为独立渲染检查点，未覆盖其他任务文件。</p></main></html>'''
(O/'review.html').write_text(page,encoding='utf-8')
(O/'README.md').write_text(f'''# 东西花园植被 v3 · 渲染交付

已完成 {len(report['trees'])} 处树形重建/增补、{len(report['shrubs'])} 组低灌木与 {len(report['tall_understory_added'])} 组高灌木；另细化绿篱、藤架叶层、园地细草及落叶，补回环树座椅中的树。

来源为 `../forecourt-refinement-v4/forecourt-refined-v4.blend`。原文件未覆盖，其他两个任务目录未修改。所有原有网格的几何和世界变换保持；{report['protected_meshes_verified_after_reopen']} 个受保护网格的 UV、材质槽和 modifier 摘要保持。仅园内十处植物核心换为独立材质，旧粗略园内植物隐藏保留。

两轮诊断后已修正树冠过透和不自然的地面块状覆盖。最终检查点重开及有限坐标核对通过，六张 1800 × 1350 正式渲染已完成并检查。

- `review.html`：全部渲染、同机位前后滑块、三组照片对照。
- `final-contact.jpg`：四个重点视角的渲染总览。
- `garden-vegetation-v3.blend`：可编辑检查点。

主参考为 IMG_4377、4384、4390、4547、4568、4574、4582。树位、尺度和额外灌木密度为视觉推定，未作为逐株测量重建。通道、楼前花坛及其他硬质构筑物保持来源模型。
''',encoding='utf-8')
print('DELIVERY_COMPLETE',flush=True)
