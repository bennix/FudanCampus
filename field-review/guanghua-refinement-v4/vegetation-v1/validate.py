import bpy,json,math,struct
from pathlib import Path
from mathutils import Vector
O=Path.cwd()/'field-review/guanghua-refinement-v4/vegetation-v1';bpy.ops.wm.open_mainfile(filepath=str(O/'vegetation-v1.blend'))
r=json.loads((O/'validation.json').read_text());road=bpy.data.objects['EPATH__photo_shape_road'];clear=[]
for t in r['trees']:
 hit,_,_,_=road.ray_cast(Vector((t['x'],t['y'],20)),Vector((0,0,-1)))
 assert not hit,t['name'];clear.append(t['name'])
for ob in bpy.context.scene.objects:
 if ob.get('feature_id')=='VEGETATION_PILOT':assert all(math.isfinite(c) for v in ob.data.vertices for c in v.co)
raw=(O/'vegetation-v1.glb').read_bytes();magic,version,length=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and length==len(raw)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(O/'vegetation-v1.glb'))
new=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id')=='VEGETATION_PILOT'];assert len(new)==21
r.update(glb_reimport=True,finite_added_vertices=True,tree_centres_clear_of_local_walk=clear)
(O/'validation.json').write_text(json.dumps(r,indent=2));print('VALIDATION_OK')
