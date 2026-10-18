"""Read-only v7 inventory for the authorized closeout cycle."""
import bpy, json, sys, collections
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
R=O.parent
sys.path.insert(0,str(R/'scene-unified-v5'))
from scene_fingerprints import snapshot, sha, plain, write
source=R/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'
assert sha(source)=='641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2'
bpy.ops.wm.open_mainfile(filepath=str(source))
write(O/'baseline-snapshot.json',snapshot())
rows=[]
for o in bpy.context.scene.objects:
    row=dict(name=o.name,type=o.type,feature=o.get('feature_id'),visible=not o.hide_render,
             matrix=plain(o.matrix_world),properties={k:plain(v) for k,v in o.items()})
    if o.type in {'MESH','FONT','CURVE'}:
        p=[o.matrix_world@Vector(v) for v in o.bound_box]
        row['bounds']=[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]
        row['materials']=[m.name if m else None for m in o.data.materials]
    if o.type=='MESH':row.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),triangles=sum(len(p.vertices)-2 for p in o.data.polygons))
    if o.type=='FONT':row.update(body=o.data.body,extrude=o.data.extrude,size=o.data.size,spacing=o.data.space_character)
    if o.type=='CAMERA':row.update(lens=o.data.lens,scale=o.data.ortho_scale,camera_type=o.data.type)
    rows.append(row)
write(O/'baseline-inventory.json',rows)
print('FEATURES',dict(collections.Counter(o.get('feature_id') for o in bpy.context.scene.objects if o.type=='MESH' and not o.hide_render)),flush=True)
for row in rows:
    if row['type']=='CAMERA' or row['type']=='FONT' or row['feature'] in {'BUILDING_ENTRY','EPATH','EOPEN_S','ESKY','ESKY_N','POET_DONKEY','WB1','WB2'} and (row['type']=='MESH' and not any(k in row['name'].lower() for k in ['leaf','branch','stem','canopy'])):
        print(json.dumps({k:v for k,v in row.items() if k not in {'properties','matrix'}},ensure_ascii=False),flush=True)
print('BASELINE_INVENTORY_COMPLETE',flush=True)
