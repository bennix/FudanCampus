"""Reopen the garden checkpoint, check protected content and render delivery views."""
import bpy, json, hashlib, time, ast
import numpy as np
from pathlib import Path
O=Path(__file__).resolve().parent
report=json.loads((O/'validation.json').read_text(encoding='utf-8'))
BASE=Path(report['source']);OUT=O/'garden-vegetation-v3.blend'
tree=ast.parse((O/'build.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['fingerprint','render']],type_ignores=[]),'<garden helpers>','exec'))
bpy.ops.wm.open_mainfile(filepath=str(BASE))
protected={ob.name:fingerprint(ob) for ob in bpy.context.scene.objects if ob.type=='MESH' and ob.name not in report['modified_foliage_materials']}
original_visibility={ob.name:ob.hide_render for ob in bpy.context.scene.objects if ob.type=='MESH' and ob.name not in report['hidden_old_garden_plants']}
def geometry(ob):
    h=hashlib.sha256()
    for group,key,n,dtype in [(ob.data.vertices,'co',3,np.float32),(ob.data.loops,'vertex_index',1,np.int32)]:
        a=np.empty(len(group)*n,dtype);group.foreach_get(key,a);h.update(a.tobytes())
    h.update(str([list(r) for r in ob.matrix_world]).encode());return h.hexdigest()
original_geometry={ob.name:geometry(ob) for ob in bpy.context.scene.objects if ob.type=='MESH'}
# The before views use exactly the final exposure and existing saved cameras.
S=bpy.context.scene
for key,name in [('east-exit','SHAPE exit approximate'),('west-garden','03-west-garden'),('east-garden','04-east-garden')]:
    render('before-'+key,bpy.data.objects[name],1000,16)
bpy.ops.wm.open_mainfile(filepath=str(OUT));S=bpy.context.scene
assert all(fingerprint(bpy.data.objects[n])==v for n,v in protected.items())
assert all(geometry(bpy.data.objects[n])==v for n,v in original_geometry.items())
assert all(bpy.data.objects[n].hide_render==v for n,v in original_visibility.items())
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==report['source_sha256']
newmeshes=[ob for ob in S.objects if ob.type=='MESH' and ob.get('feature_id')=='GARDEN_VEGETATION_V3']
for ob in newmeshes:
    a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a);assert np.isfinite(a).all(),ob.name
report['checkpoint_reopened']=True;report['protected_meshes_verified_after_reopen']=len(protected);report['new_mesh_coordinates_finite']=True;report['all_original_mesh_geometry_and_transforms_retained']=True
views={'east-exit':'SHAPE exit approximate','east-garden':'04-east-garden','west-garden':'03-west-garden','west-platform':'GV3 west platform photo 4390','east-understory':'GV3 east understory photo 4582','overall':'FINAL landscape'}
report['final_render_views']=[]
print('REOPEN_VALIDATED',len(protected),flush=True)
for key,name in views.items():
    render('final-'+key,bpy.data.objects[name],1800,40)
    report['final_render_views'].append(key)
    (O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
report['renders_complete']=True
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('FINAL_RENDER_COMPLETE',flush=True)
