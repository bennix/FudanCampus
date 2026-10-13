"""Read only geometry extraction for bounded audit repairs."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;T=O/'guanghua-closeout-final.blend'
bpy.ops.wm.open_mainfile(filepath=str(T))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def extract(o):
 uv=o.data.uv_layers.active
 return dict(name=o.name,matrix=[list(r) for r in o.matrix_world],vertices=[list(o.matrix_world@v.co) for v in o.data.vertices],faces=[dict(vertices=list(p.vertices),normal=list(o.matrix_world.to_3x3()@p.normal),material=p.material_index,uv=[list(uv.data[l].uv) for l in p.loop_indices] if uv else []) for p in o.data.polygons],materials=[m.name if m else None for m in o.data.materials])
grounds=[extract(bpy.data.objects[n]) for n in ['GROUND__terrain__FIN_garden_grass','C04 continuous ground']]
trees=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o.get('feature_id')=='TREE_CANOPY_V6':
  points=[o.matrix_world@Vector(q) for q in o.bound_box];low=[min(q[i] for q in points) for i in range(3)];high=[max(q[i] for q in points) for i in range(3)]
  trees.append(dict(name=o.name,location=list(o.location),bounds=[low,high],props={k:o[k] for k in o.keys()}))
(O/'native-audit-geometry.json').write_text(json.dumps(dict(source_sha256=sha(T),ground=grounds,trees=trees),ensure_ascii=False,default=lambda x:list(x) if hasattr(x,'__len__') else str(x)),encoding='utf-8')
for o in grounds:print('GROUND',o['name'],len(o['vertices']),len(o['faces']), sorted(set(round(v[2],6) for v in o['vertices']))[:15],flush=True)
print('RING_TREE_CANDIDATES',[(o['name'],o['location'],o['props']) for o in trees if 94<o['location'][0]<99 and 34<o['location'][1]<40],flush=True)
