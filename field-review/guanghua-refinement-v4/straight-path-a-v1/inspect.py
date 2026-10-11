import bpy, json, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O = Path(__file__).resolve().parent
BASE = O.parent / 'forecourt-refinement-v4/forecourt-refined-v4.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rows = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    pts = [ob.matrix_world @ Vector(p) for p in ob.bound_box]
    lo = [min(p[k] for p in pts) for k in range(3)]
    hi = [max(p[k] for p in pts) for k in range(3)]
    if not (lo[0] < 69 and hi[0] > 61 and lo[1] < 82 and hi[1] > 13):
        continue
    row = dict(name=ob.name, fid=ob.get('feature_id'), bounds=[lo,hi],
        materials=[m.name if m else None for m in ob.data.materials],
        hidden=ob.hide_render, vertices=len(ob.data.vertices), polygons=len(ob.data.polygons))
    if ob.name.startswith('E_WALK recessed') and not ob.name.endswith(('000','098')):
        continue
    if any(t in ob.name for t in ['FORECOURT','EDGE_PATHS','E_WALK','E_ENTRY']):
        row['boundary_xy'] = sorted(set((round(p.x,6),round(p.y,6)) for p in [ob.matrix_world@v.co for v in ob.data.vertices])) if len(ob.data.vertices)<200 else []
    rows.append(row)
(O/'inspection.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps([r for r in rows if any(t in r['name'] for t in ['FORECOURT','EDGE_PATHS','E_WALK','E_ENTRY','LAWN'])],ensure_ascii=False),flush=True)

hits=[]
for x,y in [(65.3,13.99),(65.3,14.01),(65.3,77.7),(65.3,77.85),(65.3,77.86),(65.3,78),(63.55,77.8),(67.05,77.8),(63.8,76),(66.8,76)]:
    h=[]
    for ob in bpy.context.scene.objects:
        if ob.type!='MESH' or ob.hide_render: continue
        inv=ob.matrix_world.inverted()
        ok,loc,norm,face=ob.ray_cast(inv@Vector((x,y,10)),(inv.to_3x3()@Vector((0,0,-1))).normalized(),distance=12)
        if ok:
            z=(ob.matrix_world@loc).z
            if z<2:h.append((ob.name,round(z,7),face))
    hits.append(dict(xy=[x,y],hits=sorted(h,key=lambda q:-q[1])))
(O/'surface-probes.json').write_text(json.dumps(hits,indent=2),encoding='utf-8')
print('SURFACE_PROBES',json.dumps(hits),flush=True)
print('INSPECT_OK',flush=True)
