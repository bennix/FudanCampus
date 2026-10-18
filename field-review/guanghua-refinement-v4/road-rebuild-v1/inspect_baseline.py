import bpy,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent; R=O.parents[2]
base=O.parent/'stage01-east.blend'
bpy.ops.wm.open_mainfile(filepath=str(base))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
for o in bpy.data.objects:
 if o.type!='MESH':continue
 vs=[tuple(o.matrix_world@v.co) for v in o.data.vertices]
 item={'name':o.name,'id':o.get('feature_id'),'bounds':[[min(p[i] for p in vs),max(p[i] for p in vs)] for i in range(3)]}
 if o.get('feature_id') in {'EPATH','ESKY','EOPEN_S','ETERR'}:
  item.update(vertices=[list(v.co) for v in o.data.vertices],faces=[list(f.vertices) for f in o.data.polygons],transform=[list(row) for row in o.matrix_world],materials=[m.name for m in o.data.materials])
 records.append(item)
(O/'baseline-geometry.json').write_text(json.dumps(records),encoding='utf-8')
files=[base,O.parent.parent/'guanghua-complete-v3/guanghua-complete-v3.blend']
files+=list((R/'references/guanghua_lawn').rglob('*.jpeg'))
files+=list((R/'web/public/models').rglob('*.glb'))
(O/'protected-files.json').write_text(json.dumps({str(p.relative_to(R)):sha(p) for p in files},indent=2),encoding='utf-8')
print('BASELINE_READY',len(records),len(files))
