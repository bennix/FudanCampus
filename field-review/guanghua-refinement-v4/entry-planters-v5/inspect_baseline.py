import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np

O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rows=[]
for ob in bpy.context.scene.objects:
    if ob.type!='MESH': continue
    pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
    if ob.get('feature_id')!='BUILDING_ENTRY' and not (min(p.y for p in pts)<122 and max(p.y for p in pts)>99): continue
    rows.append(dict(name=ob.name,feature_id=ob.get('feature_id'),bounds=[[min(p[k] for p in pts) for k in range(3)],[max(p[k] for p in pts) for k in range(3)]],materials=[m.name for m in ob.data.materials if m],vertices=len(ob.data.vertices),polygons=len(ob.data.polygons),modifiers=[(m.name,m.type) for m in ob.modifiers],matrix=[list(r) for r in ob.matrix_world]))
(O/'baseline-inventory.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps([r for r in rows if r['feature_id']=='BUILDING_ENTRY'],ensure_ascii=False),flush=True)
print('CAMERAS',json.dumps([dict(name=o.name,loc=list(o.location),rotation=list(o.rotation_euler),type=o.data.type,scale=o.data.ortho_scale,lens=o.data.lens) for o in bpy.context.scene.objects if o.type=='CAMERA']),flush=True)
print('INSPECTION_COMPLETE',flush=True)
