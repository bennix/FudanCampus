import bpy,json,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
BASE=O.parent/'scene-unified-v5/guanghua-unified-v5.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
items=[]
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and (any(t in ob.name for t in ['tree','Tree','mature','spreading','backdrop']) or ob.type=='FONT'):
        pts=[ob.matrix_world@Vector(v) for v in ob.bound_box]
        items.append(dict(name=ob.name,visible=not ob.hide_render,feature=ob.get('feature_id'),location=list(ob.location),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],vertices=len(ob.data.vertices),faces=len(ob.data.polygons),materials=[m.name if m else None for m in ob.data.materials]))
terrain=[]
for ob in bpy.context.scene.objects:
    if ob.type=='MESH' and not ob.hide_render and any(m and any(k in m.name.lower() for k in ['grass','soil','lawn']) for m in ob.data.materials):
        if len(ob.data.vertices)<40000:terrain.append(dict(name=ob.name,feature=ob.get('feature_id'),materials=[m.name for m in ob.data.materials if m]))
cameras=[dict(name=ob.name,location=list(ob.location),rotation=list(ob.rotation_euler),lens=ob.data.lens,type=ob.data.type,ortho=ob.data.ortho_scale) for ob in bpy.context.scene.objects if ob.type=='CAMERA']
(O/'baseline-inventory.json').write_text(json.dumps(dict(trees=items,terrain=terrain,cameras=cameras),ensure_ascii=False,indent=2),encoding='utf-8')
for r in items:
    if r['visible']:print(r['name'],r['location'],r['bounds'],r['vertices'],flush=True)
print('TERRAIN',terrain,flush=True)
