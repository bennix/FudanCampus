from pathlib import Path
import json,html
O=Path('field-review/guanghua-refinement-v4');D=json.loads((O/'photo-object-index.json').read_text(encoding='utf-8'));A=json.loads((O/'baseline-objects.json').read_text());pts={}
for a in A:
 if a['id'] and a['id'] not in ['GROUND','BOUNDARY','VEGETATION','CONTEXT_GUANGHUA','LAWN','PLAZA']:
  pts.setdefault(a['id'],[]).append(a['bounds'])
svg='<svg viewBox="0 0 900 570" style="width:100%;background:#edf1e6"><text x="20" y="22">北 ↑　模型推定坐标示意；不是测绘地图或GPS对象定位</text>'
for fid,bs in pts.items():
 if fid not in {x['location_id'] for p in D['photos'] for x in p['objects']}:continue
 x=(min(b[0][0] for b in bs)+max(b[0][1] for b in bs))/2;y=(min(b[1][0] for b in bs)+max(b[1][1] for b in bs))/2
 x=(x+90)*4;y=535-y*4
 svg+=f'<g onclick="document.querySelector(\'#q\').value=\'{fid}\';filter()" style="cursor:pointer"><circle cx="{x}" cy="{y}" r="7" fill="#aa693b"/><text x="{x+9}" y="{y+4}" font-size="12">{fid}</text></g>'
svg+='</svg>'
cards=[]
for p in D['photos']:
 ids=', '.join(x['location_id']+' '+x['status'] for x in p['objects']) or '未定位/环境'
 text=' '.join([p['photo_id'],p['route_segment'],ids,p['supports']]);src='../../'+p['file']
 cards.append(f'<article data-search="{html.escape(text)}"><a href="{src}"><img loading="lazy" src="{src}"></a><h3>{p["photo_id"]} · {p["route_segment"]}</h3><b>{ids}</b><p>{p["supports"]}</p><p class="muted">{p["limits"]}</p></article>')
page='''<!doctype html><meta charset="utf-8"><title>光华楼照片—对象索引 v4</title><style>body{font:15px system-ui;margin:24px;background:#faf9f4;color:#25382c}header{max-width:1100px;margin:auto}input{font:inherit;padding:12px;width:90%}main{display:grid;grid-template-columns:repeat(auto-fill,minmax(350px,1fr));gap:18px;margin-top:20px}article{background:white;padding:12px;border:1px solid #ddd}img{width:100%;aspect-ratio:4/3;object-fit:contain}.muted{font-size:12px;color:#777}h3{margin:8px 0}</style><header><h1>光华楼草坪与花园 · 照片索引 v4</h1><p>305张逐图记录 · 259张有地点关联 · 46张保留未定位或环境记录。点击照片打开原图。ESKY_N东北双顶存在已确认，但尚未可靠定位，未加入下图。</p>'''+svg+'''<input id="q" placeholder="检索地点ID、照片序号、路段或观察内容" oninput="filter()"><p id="count"></p><p><a href="edit-contract.md">几何编辑约束</a> · <a href="photo-object-index.json">可更新JSON索引</a> · <a href="association-changelog.json">对应关系变更依据</a></p></header><main>'''+''.join(cards)+'''</main><script>function filter(){let q=document.querySelector('#q').value.toLowerCase(),n=0;document.querySelectorAll('article').forEach(a=>{let yes=a.dataset.search.toLowerCase().includes(q);a.style.display=yes?'':'none';n+=yes});document.querySelector('#count').textContent=n+' 张照片'}filter()</script>'''
(O/'photo-map.html').write_text(page,encoding='utf-8')
