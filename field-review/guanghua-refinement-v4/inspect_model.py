import bpy,json
from pathlib import Path
p=Path('field-review/guanghua-refinement-v4')
bpy.ops.wm.open_mainfile(filepath=str(Path('field-review/guanghua-complete-v3/guanghua-complete-v3.blend').resolve()))
a=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  a.append(dict(name=o.name,id=o.get('feature_id'),location=list(o.location),bounds=[[min((o.matrix_world@v.co)[k] for v in o.data.vertices),max((o.matrix_world@v.co)[k] for v in o.data.vertices)] for k in range(3)],materials=[m.name for m in o.data.materials]))
(p/'baseline-objects.json').write_text(json.dumps(a,indent=2))
print('OBJECTS',len(a))
