import bpy,json,hashlib
from pathlib import Path
O=Path.cwd()/'field-review/guanghua-refinement-v4/vegetation-v2'
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(r) for r in o.matrix_world])).encode()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'vegetation-v1/vegetation-v1.blend'));old={o.name:sig(o) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(O/'vegetation-v2.blend'));assert all(sig(bpy.data.objects[n])==s for n,s in old.items())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'vegetation-v2.glb'));assert any(o.get('feature_id')=='VEGETATION_V2' for o in bpy.context.scene.objects)
r=json.loads((O/'validation.json').read_text());r.update(reopened=True,glb_reimport=True,original_geometry_verified_after_final=True);(O/'validation.json').write_text(json.dumps(r,indent=2));print('CHECK_OK')
