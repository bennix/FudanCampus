"""Local closeout migration with current-manifest protection and explicit sources."""
import json,hashlib,shutil,struct,math,argparse
from pathlib import Path
import numpy as np
O=Path(__file__).resolve().parent;ROOT=O.parents[2];P=ROOT/'web/public'
parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path,default=O/'guanghua-closeout-final.blend');parser.add_argument('--report-dir',type=Path,default=O)
args=parser.parse_args();source=args.source.resolve();out=args.report_dir.resolve();out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
metrics=json.loads((O/'glb-metrics.json').read_text(encoding='utf-8'));conversion=json.loads((O/'export-conversion.json').read_text(encoding='utf-8'))
assert sha(source)==conversion['source_sha256'];assert metrics['bytes']<=150*1024*1024
path=P/'campus-manifest.json';manifest=json.loads(path.read_text(encoding='utf-8-sig'));before=json.loads(json.dumps(manifest))
baseline={a['url']:sha(P/a['url']) for a in manifest['shared']+manifest['buildings']}
baseline.update({b['overview']['url']:sha(P/b['overview']['url']) for b in manifest['buildings']})
if not (out/'campus-manifest-before.json').exists():(out/'campus-manifest-before.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
if (out/'integration.json').exists():baseline=json.loads((out/'integration.json').read_text(encoding='utf-8'))['baselines']
def asset(src,relative):
 dst=P/relative;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
 return dict(url=relative,revision=sha(dst)[:12],bytes=dst.stat().st_size)
landscape=asset(O/'guanghua-closeout-optimized.glb','models/landscape/guanghua-closeout.glb')
house=asset(O/'guanghua-building-27.glb','models/buildings/27-closeout.glb')
forest=asset(O/'05-guanghua-closeout.glb','models/shared/05-guanghua-closeout.glb')
assert landscape['bytes']+house['bytes']+forest['bytes']<=150*1024*1024
# Bounds are computed from the actual exported accessor boxes and node transforms.
def bounds(p):
 raw=Path(p).read_bytes();length=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+length]);pts=[]
 def visit(i,parent):
  n=j['nodes'][i]
  if 'matrix' in n:local=np.array(n['matrix']).reshape(4,4).T
  else:
   x,y,z,w=n.get('rotation',[0,0,0,1]);rot=np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])
   local=np.eye(4);local[:3,:3]=rot@np.diag(n.get('scale',[1,1,1]));local[:3,3]=n.get('translation',[0,0,0])
  world=parent@local
  if 'mesh' in n:
   for p in j['meshes'][n['mesh']]['primitives']:
    a=j['accessors'][p['attributes']['POSITION']]
    for x in [a['min'][0],a['max'][0]]:
     for y in [a['min'][1],a['max'][1]]:
      for z in [a['min'][2],a['max'][2]]:pts.append((world@np.array([x,y,z,1]))[:3])
  for c in n.get('children',[]):visit(c,world)
 for i in j['scenes'][j.get('scene',0)]['nodes']:visit(i,np.eye(4))
 a=np.asarray(pts);return dict(min=a.min(axis=0).tolist(),max=a.max(axis=0).tolist())
for a in manifest['shared']:
 if a['id']=='guanghua-landscape':a.update(landscape);a['name']='Guanghua unified closeout';a['closeoutReport']='field-review/guanghua-refinement-v4/closeout-final/integration.json'
 if a['id']=='05':a.update(forest)
building=next(b for b in manifest['buildings'] if b['id']=='27');building.update(house);building['overview']=house.copy();building['overviewMode']='full';building['bounds']=bounds(P/house['url'])
for p,h in baseline.items():assert sha(P/p)==h,('Baseline asset changed',p)
assert all(b==next(a for a in before['buildings'] if a['id']==b['id']) for b in manifest['buildings'] if b['id']!='27')
report=dict(source=str(source),source_sha256=sha(source),scale=conversion['scale'],translation_blender=conversion['translation_blender'],baselines=baseline,
 feature_ids=conversion['feature_ids'],landscape=landscape,building=house,building_bounds=building['bounds'],
 terrain_reused=next(a for a in manifest['shared'] if a['id']=='00'),vegetation_reused=next(a for a in manifest['shared'] if a['id']=='05'),
 inherited_footprint=[-90,112.3021175619119,-9,124],registration='Inherited provisional 2/3 scale; native landscape envelope preserved',
 replacement='Building 27 and Guanghua landscape switch to new local assets; old shared forest triangles protruding into the replacement envelope are removed in a new derivative; retained outside vegetation triangles remain exact',
 validation_status='Local candidate switched for actual browser validation; final acceptance pending')
(out/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('LOCAL_CLOSEOUT_INTEGRATED',landscape,house,flush=True)
