import bpy,json
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE))
rows=[]
for ob in bpy.context.scene.objects:
    if ob.type=='CAMERA':
        rows.append(dict(name=ob.name,type='CAMERA',location=list(ob.location),rotation=list(ob.rotation_euler),lens=ob.data.lens,ortho=ob.data.ortho_scale))
    elif ob.type=='MESH' and (ob.get('feature_id') in ['VEGETATION','VEGETATION_PILOT','VEGETATION_V2','E_TREES'] or any(k in ob.name.lower() for k in ['hedge','shrub','planting','leaf-clusters'])):
        pts=[ob.matrix_world@Vector(p) for p in ob.bound_box]
        rows.append(dict(name=ob.name,type='MESH',fid=ob.get('feature_id'),location=list(ob.location),scale=list(ob.scale),rotation=list(ob.rotation_euler),bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)] for i in range(3)],vertices=len(ob.data.vertices),materials=[m.name for m in ob.data.materials],hidden=ob.hide_render))
(O/'inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('INVENTORY_COMPLETE',len(rows),flush=True)
