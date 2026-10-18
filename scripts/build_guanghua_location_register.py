"""Freeze stable location IDs and produce a durable photo-to-place handoff.
This script never changes originals or Blender/GLB checkpoints.
"""
from pathlib import Path
import json,html,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-lawn-survey-v1'
D=json.loads((OUT/'survey.json').read_text(encoding='utf-8'))
MODEL=OUT/'model'
primary={'LAWN':4474,'PLAZA':4474,'DING':4348,'WPATH':4363,'WTERR':4378,'WB1':4416,'WB2':4424,'WGLASS':4332,'WGLASS2':4409,'WSKY1':4354,'WSKY2':4448,'WOPEN':4453,'EOPEN':4493,'ESKY':4574,'ETERR':4562,'ERAMP':4539,'EPATH':4582,'SIGN':4603,'FLOWER':4609,'WOPEN_S':4357,'EOPEN_S':4505}
groups={'LAWN':['S0','N0','E0','S1'],'PLAZA':['NW','N0','NE'],'DING':['SW0','W1'],'WPATH':['W1','NW'],'WTERR':['W2'],'WB1':['W3'],'WB2':['W3'],'WGLASS':['SW0'],'WGLASS2':['W3'],'WSKY1':['W1'],'WSKY2':['NW'],'WOPEN':['NW'],'EOPEN':['NE'],'ESKY':['E3','E0'],'ETERR':['E2'],'ERAMP':['E1'],'EPATH':['E3','E0'],'SIGN':['S2'],'FLOWER':['S2'],'WOPEN_S':['W1'],'EOPEN_S':['E0','E3']}
next_steps={
 'LAWN':'用南北向全景约束四角与北侧圆角，保持中部连续草地；先校正长宽比。',
 'PLAZA':'与楼前台阶、两侧花钵和草坪北边缘对齐；再校正铺装网格尺寸。',
 'DING':'先确认方鼎轮廓、四足、双耳和三层基座比例；铭文与纹饰另列细化。',
 'WPATH':'按连续照片核对每个转弯和支路，区分园路与草坪边直道。',
 'WTERR':'核对两段台阶及中间平台、X形栏杆、双采光顶与拼石平台的相互位置。',
 'WB1':'以开门照片核对门洞、蓝色招牌和两侧挡墙；地下深处未知。',
 'WB2':'以关门照片核对多扇门分缝、招牌和门洞；勿与南门合并。',
 'WGLASS':'核对长条低平台、通风百叶与一端玻璃罩的连接。',
 'WGLASS2':'核对西侧玻璃入口的罩体、框架和周边车行入口；与西南罩分开。',
 'WSKY1':'核对采光顶、百叶基座与 WOPEN_S 的邻接关系；不重复建楼梯口。',
 'WSKY2':'4448 可确认并排两个采光顶；按同一组构筑物精修。',
 'WOPEN':'靠北广场的西侧楼梯口；与 WOPEN_S 区分，核对踏步、扶手和绿篱开口。',
 'EOPEN':'靠北广场的东侧楼梯口；以 4493 为主，勿合并为 4505 的中段楼梯口。',
 'ESKY':'与 EOPEN_S 相邻，4505 与 4574 是不同方向的关联证据，不能据此复制一组。',
 'ETERR':'核对从东路登上的宽台阶、多个错层平台、弧形花池与座椅。',
 'ERAMP':'核对下坡车道曲线、挡墙和藤架立柱跨度；不推测车库内部。',
 'EPATH':'核对曲径接草坪直道、采光顶及阶梯花园支路的连接关系。',
 'SIGN':'核对 FUDAN 字体比例、底座、红色心形框和座椅；当前为简化形体。',
 'FLOWER':'核对两个倾斜圆环与绿植、花坛的方向；不可当成竖直雕塑框。',
 'WOPEN_S':'4354/4357 与 WSKY1 为同一邻接组；不同于靠楼前的 WOPEN。',
 'EOPEN_S':'4505/4574 属于相邻采光顶和中段楼梯口的相向视图；不同于 EOPEN。',
}
features=[]
photos=[]
for i,f in enumerate(D['features'],1):
 fid=f['id'];features.append({**f,'map_number':f'{i:02}','stable_id':fid,'primary_photo':primary[fid],'supporting_photos':f['photos'],'context_zones':groups[fid], 'context_rule':'Same route segment only; does not prove that every photo depicts this object.', 'model_object_prefix':fid+'__','model_checkpoint':'model/guanghua-lawn-v1.blend','next_refinement':next_steps[fid]})
for p in D['photos']:
 direct=[f['id'] for f in features if p['number'] in f['photos']]
 candidates=[f['id'] for f in features if p['zone'] in f['context_zones'] and f['id'] not in direct]
 photos.append({'file':p['file'],'number':p['number'],'sequence':p['sequence'],'time':p['time'],'time_offset':p['offset'],'route_zone':p['zone'],'route_zone_name':p['zone_name'],'evidence_locations':direct,'same_route_candidates':candidates,'association_level':'landmark_evidence' if direct else 'route_context_only','same_route_candidates_are_confirmed':False,'camera_xy':[p['x'],p['y']],'camera_heading':p['local_heading'],'gps_error_m':p['gps_error_m'],'subject_coordinate':None,'sha256':p['sha256'],'original':'../../references/guanghua_lawn/img/img/'+p['file']})
linked=sum(bool(p['evidence_locations']) for p in photos)
register={'version':1,'status':'Preparation complete; modeling paused at user request on 2026-09-27','scale_status':'比例推定；无实测距离控制','rules':['地点 ID 永久保留，后续精修不重新编号。','拍摄者 GPS 与被摄对象位置分开。','same_route_candidates 仅是检索候选，绝不作为已确认对象标签。','新增或修正对应时保留来源照片、判断理由与版本。','接触表级审阅覆盖全部照片；对象级确认仅限 evidence_locations。'],'counts':{'photos':len(photos),'route_zones':len(D['zones']),'locations':len(features),'landmark_evidence_photos':linked,'route_context_only_photos':len(photos)-linked},'zones':D['zones'],'locations':features,'photos':photos}
(OUT/'location-register.json').write_text(json.dumps(register,ensure_ascii=False,indent=2),encoding='utf-8')

# Stable per-location notes are a compact handoff for subsequent sessions.
lines=['# 光华楼草坪 · 精修入口','', '**当前状态：总体准备已完成；按用户要求，建模停在第一版场地检查点。**','',f'305 张照片均已按时间与行走路段归档，分成 15 段路线。21 个地点使用固定 ID；其中 {linked} 张已作为具体地点的证据照片，其余 {305-linked} 张保留为路线背景，不能称为已经逐对象精准标注。','', '## 从哪里开始','', '- [照片地图](index.html)：浏览全部照片，点地图编号查看地点证据。','- [地点目录](locations.html)：按地点名称查主参考与相关照片。','- [三维预览](viewer.html)：当前模型仅供比例与关系检查。','- [完整照片—地点索引](location-register.json)：同时保留明确证据与未确认候选。','', '## 固定地点编号','', '| 图号 | 固定 ID | 地点 | 主参考 | 下一次精修重点 |','|---|---|---|---|---|']
for f in features:lines.append(f"| {f['map_number']} | `{f['id']}` | [{f['name']}](index.html#{f['id']}) | IMG_{f['primary_photo']} | {f['next_refinement']} |")
lines+=['','## 容易混淆的对象','', '- 西侧两个围栏楼梯口：北侧 `WOPEN`；中段 `WOPEN_S`。','- 东侧两个围栏楼梯口：北侧 `EOPEN`；中段 `EOPEN_S`。','- `WSKY2` 是西北并排双采光顶；`WTERR` 内还包含另一对平台采光顶。','- `ESKY` 与 `EOPEN_S` 相邻：4505、4574 等照片提供相向观察，不能当成两个重复地点。','- 两处西侧自行车库门分别为 `WB1` / `WB2`；东侧藤架车道为 `ERAMP`。','', '## 下次继续时的约定','', '可以直接说“精修西花园高台”或“精修 WTERR”。先读该地点的主参考，再看证据照片和相邻路线段；把当前模型作为需要校正的假设，不把它当成真实测绘。','', '每轮只锁定一个部位，保存新检查点和固定视角对比；地点 ID、照片原名和原始 GPS 保持稳定。位置、宽度与标高明确属于推定。北侧光华楼仅是从已有项目复用的比例参照。','', '### 当前文件','', '- 布局检查点：`model/guanghua-lawn-stage01-layout.blend`','- 场地检查点：`model/guanghua-lawn-v1.blend`','- 含建筑参照导出：`model/guanghua-lawn-v1.glb`','- 仅场地导出：`model/guanghua-lawn-site-only.glb`','- 构件证据清单：`model/component-evidence.json`','', '原始 JPEG、现有校园模型和受保护资产保留；后续继续前先检查此目录及 Git 状态，勿重新全量生成校园。','']
(OUT/'START-HERE.md').write_text('\n'.join(lines),encoding='utf-8')
cards=[]
for f in features:
 imgs=''.join(f'<a href="../../references/guanghua_lawn/img/img/IMG_{n}.jpeg" target="_blank" rel="noopener"><img src="thumbs/IMG_{n}.jpeg" alt="IMG_{n}" loading="lazy"><span>IMG_{n}'+(' · 主参考' if n==f['primary_photo'] else '')+'</span></a>' for n in sorted(set(f['photos']),key=lambda n:(n!=f['primary_photo'],n)))
 cards.append(f'<article id="{f["id"]}" data-search="{f["id"]} {f["name"]}"><div class="number">{f["map_number"]}</div><div><h2>{f["name"]} <code>{f["id"]}</code></h2><p>{f["next_refinement"]}</p><div class="links"><a href="index.html#{f["id"]}">在地图定位 ↗</a><span>路线：{" / ".join(f["context_zones"])}</span><span>位置、尺度：推定</span></div><div class="photos">{imgs}</div></div></article>')
page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>光华楼草坪 · 地点目录</title><style>*{box-sizing:border-box}body{margin:0;background:#f4f2e9;color:#244237;font:15px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1180px;margin:auto;padding:28px 24px}h1{margin:0;font-size:25px}p{color:#586e60;margin:7px 0}a{color:#156357}header{padding-bottom:20px;border-bottom:1px solid #cad4c4}nav{display:flex;gap:18px;flex-wrap:wrap;margin:12px 0}input{font:inherit;padding:10px 12px;border:1px solid #adc1ab;background:#fffdf6;border-radius:4px;width:min(100%,400px)}article{display:grid;grid-template-columns:48px 1fr;gap:14px;padding:23px 0;border-bottom:1px solid #d2d9cd}article[hidden]{display:none}.number{color:#927047;font-size:24px}h2{font-size:18px;margin:0;font-weight:500}code{font-size:12px;color:#798775;padding-left:10px}.links{display:flex;gap:18px;flex-wrap:wrap;font-size:12px;color:#6a7865;margin:8px 0 13px}.photos{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:9px}.photos a{text-decoration:none;font-size:11px;background:#e4e9dc;padding-bottom:3px}.photos img{width:100%;height:145px;object-fit:cover;display:block}.photos span{padding-left:5px}.note{font-size:13px}@media(max-width:600px){main{padding:20px 14px}article{grid-template-columns:30px 1fr;gap:8px}.number{font-size:20px}.photos{grid-template-columns:1fr 1fr}.photos img{height:110px}}</style></head><body><main><header><h1>光华楼草坪 · 地点目录</h1><p>21 个固定地点编号，作为以后分部位精修的入口。</p><p class="note">__COUNTS__<br>下方照片是该地点的证据；同路线的其他照片可在地图中继续查看。现有模型仍是比例推定。</p><nav><a href="index.html">照片地图</a><a href="viewer.html">当前三维模型</a><a href="START-HERE.md">精修说明</a></nav><input id="search" placeholder="输入地点，如 高台 / 采光 / WTERR" aria-label="筛选地点"></header>__CARDS__<p id="empty" hidden>没有匹配的地点，请换一个名称。</p></main><script>document.querySelector('#search').addEventListener('input',e=>{const q=e.target.value.trim().toLowerCase();let count=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!a.dataset.search.toLowerCase().includes(q);if(!a.hidden)count++;});document.querySelector('#empty').hidden=count>0;});</script></body></html>'''
page=page.replace('__COUNTS__',f'305 张已归入 15 段路线；{linked} 张已关联具体地点，其余 {305-linked} 张保留为路线背景。').replace('__CARDS__',''.join(cards))
(OUT/'locations.html').write_text(page,encoding='utf-8')

# Verify references and preserve a final state manifest without altering model checkpoints.
assert len(photos)==305 and len(set(p['number'] for p in photos))==305
assert all(f['primary_photo'] in f['photos'] for f in features)
source_ok=all(hashlib.sha256((ROOT/'references/guanghua_lawn/img/img'/p['file']).read_bytes()).hexdigest()==p['sha256'] for p in photos)
assert source_ok,'Original image contents changed'
baseline=json.loads((MODEL/'baseline-sha256.json').read_text(encoding='utf-8'))
baseline_ok=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in baseline.items())
assert baseline_ok,'Existing asset changed'
state={'status':'Preparation complete; model work stopped at current checkpoint by user instruction','photo_count':305,'location_count':21,'route_count':15,'direct_evidence_photos':linked,'route_context_only_photos':305-linked,'original_photo_hashes_match':source_ok,'baseline_hashes_match':baseline_ok,'baseline_files_checked':len(baseline),'model_files':{p.name:{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in MODEL.iterdir() if p.suffix in ['.blend','.glb']},'next_entry':'START-HERE.md'}
(OUT/'preparation-status.json').write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in state.items() if k!='model_files'},ensure_ascii=False))
