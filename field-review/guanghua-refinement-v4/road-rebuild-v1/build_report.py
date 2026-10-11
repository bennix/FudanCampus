import json,html,os,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;R=O.parents[2];B=O/'diagnostic-03'
P=json.loads((B/'profile.json').read_text());D=json.loads((B/'mesh-payload.json').read_text())
def svghead(w,h):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}"><rect width="100%" height="100%" fill="#faf9f5"/>'
def profile_panel(samples,label,ox,oy,width=440,height=210):
    length=samples[-1]['s'];zmax=2.0
    points=' '.join(f'{ox+p["s"]/length*width:.2f},{oy+height-p["z"]/zmax*height:.2f}' for p in samples)
    out=f'<text x="{ox}" y="{oy-20}" font-size="18">{label}</text>'
    for z in [0,.5,1,1.5,2]:
        y=oy+height-z/zmax*height
        out+=f'<path d="M{ox},{y}h{width}" stroke="#ddd"/><text x="{ox-34}" y="{y+4}" font-size="12">{z:.1f}</text>'
    out+=f'<polyline points="{points}" fill="none" stroke="#aa5639" stroke-width="3"/><text x="{ox}" y="{oy+height+25}" font-size="13">0</text><text x="{ox+width-50}" y="{oy+height+25}" font-size="13">{length:.2f} m</text>'
    return out
s=svghead(1100,380)+'<g font-family="Arial,sans-serif" fill="#233831"><text x="35" y="30" font-size="22">Unmeasured profile hypothesis — NOT site-accepted</text>'
s+=profile_panel(P['main_samples'],f'Main path: peak grade {P["max_longitudinal_grade"]:.1%}',70,100)
s+=profile_panel(P['branch_samples'],f'West connector: peak grade {P["branch_max_grade"]:.1%}',620,100)
s+='<text x="35" y="365" font-size="14">Metres are model units. Profiles test mesh continuity; elevations require photo-based reassessment.</text></g></svg>'
(B/'profile.svg').write_text(s,encoding='utf-8')
road=D['road'];verts=road['vertices'][:len(road['vertices'])//2];faces=road['faces'][:road['top_faces']]
x0=min(v[0] for v in verts);x1=max(v[0] for v in verts);y0=min(v[1] for v in verts);y1=max(v[1] for v in verts)
scale=min(800/(x1-x0),680/(y1-y0))
def xy(v):return (60+(v[0]-x0)*scale,80+(y1-v[1])*scale)
edges=set(tuple(sorted((a,b))) for f in faces for a,b in zip(f,f[1:]+f[:1]))
s=svghead(960,840)+'<g font-family="Arial,sans-serif"><text x="30" y="30" font-size="22">West exit: constrained road mesh / north up</text><text x="30" y="55" font-size="14">Single connected surface; existing spatial layout remains inferred.</text>'
s+='<path fill="none" stroke="#758b83" stroke-width="0.35" d="'
for a,b in sorted(edges):
    ax,ay=xy(verts[a]);bx,by=xy(verts[b]);s+=f'M{ax:.2f},{ay:.2f}L{bx:.2f},{by:.2f}'
s+='"/>'
for name,node in D['network']['nodes'].items():
    if 'xy' not in node:continue
    x,y=xy(node['xy']);s+=f'<circle cx="{x}" cy="{y}" r="4" fill="#ba573d"/><text x="{x+7}" y="{y-7}" font-size="13">{name}</text>'
s+='</g></svg>';(B/'wireframe.svg').write_text(s,encoding='utf-8')
photo=os.path.relpath(R/'references/guanghua_lawn/img/img/IMG_4568.jpeg',O).replace('\\','/')
def img(path,caption):return f'<figure><a href="{path}"><img loading="lazy" src="{path}"></a><figcaption>{caption}</figcaption></figure>'
root='diagnostic-03/'
page='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>西出口道路生成小样</title><style>body{font:16px/1.6 system-ui;margin:30px auto;max-width:1280px;padding:0 24px;color:#24372f;background:#f7f6f1}h1{font-size:28px}h2{font-size:21px;margin-top:36px}.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}figure{margin:0;background:white;padding:12px;border:1px solid #ddd}img{width:100%;height:370px;object-fit:contain}figcaption{font-size:14px}strong{color:#a44e30}.notice{padding:18px;background:#efe2d2}a{color:#315e4c}table{border-collapse:collapse}td,th{padding:10px;border-bottom:1px solid #ccc}@media(max-width:800px){.row{grid-template-columns:1fr}}</style>
<h1>西出口道路生成小样</h1><p class="notice"><strong>生成器与网格检查通过；现场剖面未通过验收。</strong> 本页展示局部技术小样，不能作为全场精修完成版。其余 EPATH 仍保留旧问题。</p>
<p>固定流程：二维路网与轮廓 → 约束三角网格 → 独立高程 → 扣除路面的肩部 → 统一加厚。原 stage01、整体 v3、305 张原图及既有 GLB 未覆盖。</p>
<table><tr><th>检查</th><th>结果</th></tr><tr><td>生成器代表性测试</td><td>10 项通过</td></tr><tr><td>局部道路</td><td>1 个连通表面；无重复面、内部开放边；实体闭合正体积</td></tr><tr><td>保护</td><td>336 个文件哈希一致；非 EPATH 几何和材质不变；小样范围外剩余路面顶点不变</td></tr><tr><td>未解决</td><td>当前测试剖面主路最大纵坡约 21.3%，短连接段约 58.7%；均不是现场测量值。肩部仍有明显陡坎与分片感。</td></tr></table>
<h2>同机位纯色顶视：前 / 后</h2><div class="row">'''
page+=img(root+'before-top-neutral.png','原 stage01：道路被肩部遮挡，交叉处有黑斑。')+img(root+'after-top-neutral.png','第三批：连续道路、明确支路节点，洞口内部不再填土。')+'</div>'
page+='<h2>同机位纯色出口视角：前 / 后</h2><div class="row">'+img(root+'before-exit-neutral.png','原 stage01；近似相机，未标定。')+img(root+'after-exit-neutral.png','局部网格已连续；高度假设仍需重做。')+'</div>'
page+='<h2>照片与纹理版：仅近似视角</h2><div class="row">'+img(photo,'IMG_4568 原照片；未编辑原图。')+img(root+'after-exit-textured.png','没有用纹理掩盖几何问题；铺装尺度尚未精修。')+'</div>'
page+='<h2>侧视与网格</h2><div class="row">'+img(root+'after-side-neutral.png','侧视保留显示道路隆起和肩部陡坎，不能按现场通过。')+img(root+'wireframe.svg','约束三角网格与接口节点。')+'</div>'
page+='<h2>剖面假设</h2>'+img(root+'profile.svg','保留梯脚 1.75 模型米、试设节点 1.20 模型米，导致局部坡度偏大。它是待否证的假设，不是推荐坡度。')
page+='''<h2>批次与下一步</h2><p>diagnostic-01：失败，路面过宽且肩部侵入洞口。diagnostic-02：纠正上述问题，但草坪边接口仍保留旧高差。diagnostic-03：接口与既有直道同高并移除重叠；仍停留在技术小样状态。</p><p><strong>下一步先用现有照片复核 ETERR 上平台、短梯、采光顶基座与花园地面之间的相对高差，再修改独立剖面参数。</strong> 在此之前不扩展到北出口或西花园，不发布 GLB。</p>
<p><a href="diagnostic-03/west-exit-study.blend">局部 Blender 小样</a> · <a href="diagnostic-03/independent-validation.json">独立检查报告</a> · <a href="sample-settings.json">可调整参数</a> · <a href="../road-generation-plan.md">完整方法计划</a></p></html>'''
(O/'review.html').write_text(page,encoding='utf-8')
print('REVIEW_READY')
