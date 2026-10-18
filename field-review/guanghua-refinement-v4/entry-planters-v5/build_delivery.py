import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
O=Path(__file__).resolve().parent
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',21)
for key,label in [('4464','IMG_4464 近似视角'),('4485','IMG_4485 近似视角'),('pair-top','左右坛体俯视')]:
    a=Image.open(O/('before-'+key+'.png')).convert('RGB');b=Image.open(O/('after-'+key+'.png')).convert('RGB')
    assert a.size==b.size
    w,h=a.size;out=Image.new('RGB',(w*2,h+82),(244,244,241));d=ImageDraw.Draw(out)
    d.text((20,8),'修改前 · 最新 v4 基线',font=font,fill=(36,43,36));d.text((w+20,8),'修改后 · v5 灌木材质收口',font=font,fill=(36,43,36))
    d.text((20,46),label+'｜同相机、同分辨率；沿用现有几何',font=small,fill=(86,91,84))
    out.paste(a,(0,82));out.paste(b,(w,82));out.save(O/('comparison-'+key+'.jpg'),quality=94)
report=json.loads((O/'final-validation.json').read_text())
assert report.get('checkpoint_reopened') and report.get('render_complete')
text=f'''# 光华楼左右种植坛 · v5 验收版

按本轮最新指示收口：以最新稳定文件 `forecourt-refined-v4.blend` 为基础，只替换两侧红、绿灌木的材质；另存 `entry-planters-review-v5.blend`。不继续展开几何精修，未应用本目录中准备过的几何研究。

[打开验收图页](review.html) · [可编辑检查点](entry-planters-review-v5.blend) · [4464 同机位对照](comparison-4464.jpg) · [两坛俯视对照](comparison-pair-top.jpg)

|原验收项|本版完成情况|仍属推定或沿用内容|
|---|---|---|
|左右平面轮廓、弧线、前后位置|提供左右独立俯视及双坛同框，方便直接验收|轮廓与镜像关系沿用 v4，本版未重新修形|
|挡墙、压顶、底座连接|提供左右连接近景，保留可见石材轮廓|组件结构、墙与底座的布尔连接沿用 v4；本版未重做接头|
|坡脚、坡顶、平台标高及净带|全部保留现有坐标和几何|标高及坡道关系仍是 v4 的模型推定；不新增实测或净宽认证|
|红绿灌木表观|4 个对象换为带叶片叠层、方向/色调变化和微凹凸的独立材质；贴图已打包|分区、厚度、高低沿用现有几何；纹理叶片密度和品种为视觉推定|
|石板缝、外挑、小倒角、底部|沿用前版，输出无遮挡连接近景|本次材质收口不追加几何细部，也不声称修复了原有几何不足|

{report['protected_meshes']} 个其它网格的几何、世界变换、UV、材质槽和 modifier 摘要与来源一致；包括主草坪、楼体主体、西花园入口和已完成区域。全部网格的顶点、拓扑及世界变换保持。来源 SHA-256 保持，新检查点已重新打开，4 张新贴图均内嵌。

照片依据：IMG_4464、IMG_4485 为主，IMG_4480 为辅助。相机是人工近似，未做测量配准。没有现场尺度证据，本版不新增尺寸声明。

## 交付视图

- `comparison-4464.jpg`、`comparison-4485.jpg`：修改前后同机位对照。
- `comparison-pair-top.jpg`：两坛俯视对照。
- `after-west-top.png`、`after-east-top.png`：左右单坛俯视。
- `after-west-junction.png`、`after-east-junction.png`：隐藏灌木后的墙体连接近景。
- `final-validation.json`：检查点、保护对象、纹理打包和图像完成记录。

本版可供上述范围的视觉验收；“可验收”不等于现场几何测量认证，也不替代用户对轮廓和连接的最终判断。
'''
(O/'README.md').write_text(text,encoding='utf-8')
panels=[('comparison-4464.jpg','4464 近似机位 · 前后对照'),('comparison-4485.jpg','4485 近似机位 · 前后对照'),('comparison-pair-top.jpg','左右坛体 · 同机位俯视对照'),('after-west-top.png','左坛（西侧）独立俯视'),('after-east-top.png','右坛（东侧）独立俯视'),('after-west-junction.png','左侧墙体连接 · 隐藏灌木'),('after-east-junction.png','右侧墙体连接 · 隐藏灌木')]
html='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼左右种植坛 v5 验收</title><style>body{margin:0;background:#f1f2ee;color:#28372d;font:16px/1.6 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1440px;margin:auto;padding:26px}h1{font-size:26px;margin:0 0 12px}p{max-width:1100px}a{color:#365e4b}figure{margin:28px 0;background:white;padding:12px;border-radius:8px}figure img{width:100%;display:block}figcaption{font-weight:600;margin:0 0 10px}.refs{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.refs img{width:100%}button{padding:8px 13px;cursor:pointer;border:1px solid #9fab9e;background:white;border-radius:5px}.hidden{display:none}@media(max-width:750px){main{padding:16px}.refs{grid-template-columns:1fr}}</style><main><h1>光华楼左右种植坛 · v5 验收版</h1><p>按最新要求完成材质收口：两侧红绿灌木换为有叶片叠层与微凹凸的材质，现有坛体、坡道、平台及石材几何沿用 v4。主草坪、楼体主体、西花园入口和其它已完成区域保持。可编辑模型与贴图均另存。</p><p><a href="entry-planters-review-v5.blend">下载可编辑检查点</a> · <a href="README.md">逐项说明与推定边界</a> · <a href="final-validation.json">保存与保护验证</a></p><p>对照相机一致；4464/4485 是人工近似取景。绝对尺寸、隐藏轮廓及现有标高仍为模型推定，本版未追加几何修正。</p><button onclick="document.querySelector('.refs').classList.toggle('hidden')">展开／收起参考照片</button><div class="refs hidden">'''
for num in (4464,4485,4480):html+=f'<figure><figcaption>IMG_{num}</figcaption><img loading="lazy" src="../../../references/guanghua_lawn/img/img/IMG_{num}.jpeg"></figure>'
html+='</div>'
for path,label in panels:html+=f'<figure><figcaption>{label}</figcaption><a href="{path}"><img loading="lazy" src="{path}" alt="{label}"></a></figure>'
html+='</main></html>'
(O/'review.html').write_text(html,encoding='utf-8')
print('DELIVERY_COMPLETE',report['protected_meshes'])
