import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
BASE=O.parent/'west-entry-v3/west-entry-aligned-v3.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rows=[]
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    if ob.get('feature_id') not in ['CONTEXT_GUANGHUA','EPATH','WPATH','E_ENTRY','W_ENTRY','EDGE_PATHS','FORECOURT','GROUND']:continue
    ps=[ob.matrix_world@Vector(c) for c in ob.bound_box]
    bm=bmesh.new();bm.from_mesh(ob.data)
    rows.append(dict(name=ob.name,fid=ob.get('feature_id'),bounds=[[min(p[k] for p in ps) for k in range(3)],[max(p[k] for p in ps) for k in range(3)]],vertices=len(ob.data.vertices),faces=len(ob.data.polygons),boundary=sum(e.is_boundary for e in bm.edges),nonmanifold=sum(not e.is_manifold for e in bm.edges),negative_top=sum(f.normal.z<-.8 and f.calc_center_median().z>0 for f in bm.faces),materials=[m.name for m in ob.data.materials if m],modifiers=[(m.name,m.type) for m in ob.modifiers],parent=ob.parent.name if ob.parent else None))
    bm.free()
(O/'inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
summary=[r for r in rows if r['fid'] in ['EPATH','WPATH','EDGE_PATHS','FORECOURT'] or r['fid']=='CONTEXT_GUANGHUA' and any(t in r['name'].lower() for t in ['stair','step','base','plinth','podium','floor','column','porch'])]
print(json.dumps(summary),flush=True)
print('CONTEXT_NAMES',json.dumps([r['name'] for r in rows if r['fid']=='CONTEXT_GUANGHUA']),flush=True)
print('CAMERAS',json.dumps([dict(name=o.name,loc=list(o.location),rot=list(o.rotation_euler),type=o.data.type,scale=o.data.ortho_scale,lens=o.data.lens) for o in bpy.context.scene.objects if o.type=='CAMERA']),flush=True)
