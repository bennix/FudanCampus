import bpy,json
from pathlib import Path
from mathutils import Vector
R=Path.cwd();O=R/'field-review/guanghua-refinement-v4/vegetation-v1'
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'west-exit-shape-v1/view-03/west-exit-shape.blend'))
a=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@Vector(v) for v in o.bound_box]
  if o.get('feature_id') in ['VEGETATION','ESKY','EOPEN_S','ETERR','EPATH']:
   a.append(dict(name=o.name,id=o.get('feature_id'),hidden=o.hide_render,bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],loc=list(o.location)))
(O/'inventory.json').write_text(json.dumps(a,indent=2))
print('INVENTORY_DONE')
