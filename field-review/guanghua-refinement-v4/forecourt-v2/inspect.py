import bpy,json
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'forecourt-v1/forecourt-entry-v1.blend'))
rows=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 bb=[o.matrix_world@Vector(p) for p in o.bound_box]
 lo=[min(p[k] for p in bb) for k in range(3)];hi=[max(p[k] for p in bb) for k in range(3)]
 if o.get('feature_id') in ['EPATH','EOPEN','PLAZA','EDGE_PATHS'] or (lo[1]>100 and o.get('feature_id')!='CONTEXT_GUANGHUA'):
  rows.append(dict(name=o.name,fid=o.get('feature_id'),bounds=[lo,hi],materials=[m.name for m in o.data.materials],hidden=o.hide_render))
(O/'inventory.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows))
