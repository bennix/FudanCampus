import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(O/'stage02-east-urn.blend'))
out=[]
def cross(a,b,c):return (b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x)
def intersect(a,b,c,d):return cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or ob.get('feature_id') not in ['EPATH','E_ENTRY']:continue
 if not ('path' in ob.name.lower() or ob.get('feature_id')=='EPATH') or any(t in ob.name for t in ['ground','terrain']):continue
 ob.data.calc_loop_triangles();bad=[];levels={};down=[]
 for p in ob.data.polygons:
  vs=[ob.matrix_world@ob.data.vertices[i].co for i in p.vertices]
  if max(q.z for q in vs)-min(q.z for q in vs)<1e-4:
   levels.setdefault(round(vs[0].z,4),[0,0]);levels[round(vs[0].z,4)][p.normal.z<0]+=1
  if len(vs)==4 and (intersect(vs[0],vs[1],vs[2],vs[3]) or intersect(vs[1],vs[2],vs[3],vs[0])):
   bad.append(dict(face=p.index,center=[sum(q[k] for q in vs)/4 for k in range(3)],vertices=[list(q) for q in vs]))
 for t in ob.data.loop_triangles:
  vs=[ob.matrix_world@ob.data.vertices[i].co for i in t.vertices]
  if abs(vs[0].z-vs[1].z)<1e-5 and abs(vs[0].z-vs[2].z)<1e-5 and vs[0].z>.08 and t.normal.z<-.1:down.append(t.polygon_index)
 out.append(dict(name=ob.name,bow_tie_quads=bad,flat_levels=levels,downward_upper_triangles=sorted(set(down))))
(O/'path-diagnosis.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in a.items() if k!='bow_tie_quads'}|dict(bow_ties=len(a['bow_tie_quads'])) for a in out]),flush=True)
