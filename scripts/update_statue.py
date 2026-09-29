"""Rebuild only landmark 58 and migrate the old placeholder out of shared 00."""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from statue_geometry import build_statue
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=build_statue()
bpy.context.view_layer.update()
out=ROOT/'assets/landmarks';out.mkdir(exist_ok=True,parents=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'58.blend'))
public=ROOT/'web/public'
manifest=json.loads((public/'campus-manifest.json').read_text())
for obj in objects:obj.location+=Vector((-40,66.4,0))
bpy.context.view_layer.update()
target=public/'models/shared/58.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_extras=True)
def entry(path):
    data=path.read_bytes()
    return dict(url=str(path.relative_to(public)),bytes=len(data),revision=hashlib.sha256(data).hexdigest()[:12])
manifest['shared']=[a for a in manifest['shared'] if a['id']!='58']
manifest['shared'].append(dict(id='58',name='毛主席像',**entry(target)))
for obj in objects:obj.location-=Vector((-40,66.4,0))
# One-time migration. Keep all other shared geometry unchanged in world space.
temporary=bpy.data.scenes.new('Remove old statue placeholder');original=bpy.context.scene;bpy.context.window.scene=temporary
bpy.ops.import_scene.gltf(filepath=str(public/'models/shared/00.glb'))
old=[o for o in temporary.objects if o.name.startswith(('Statue plinth','Statue abstract body','Statue head'))]
if old:
    for obj in old:bpy.data.objects.remove(obj,do_unlink=True)
    bpy.ops.export_scene.gltf(filepath=str(public/'models/shared/00.glb'),export_format='GLB',use_active_scene=True,export_extras=True)
    for item in manifest['shared']:
        if item['id']=='00':item.update(entry(public/'models/shared/00.glb'))
bpy.context.window.scene=original
(public/'campus-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
labels=json.loads((public/'buildings.json').read_text())
for item in labels['buildings']:
    if item['id']=='58':item['position']=[-40,9,-66.4]
(public/'buildings.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2)+'\n')
# Neutral studio preview; independent of the campus file.
scene=bpy.context.scene;scene.world.color=(.24,.24,.24)
world=scene.world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.33,.37,.42,1)
world.node_tree.nodes['Background'].inputs[1].default_value=.7
for name,pos,power,size in [('Key',(-5,-8,12),1900,7),('Fill',(5,-2,8),900,5),('Rim',(1,5,10),1500,5)]:
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,4))-ob.location).to_track_quat('-Z','Y').to_euler()
data=bpy.data.cameras.new('Statue front three quarter');camera=bpy.data.objects.new('Statue front three quarter',data);scene.collection.objects.link(camera)
camera.location=(9,-23,10);camera.rotation_euler=(Vector((0,0,4.25))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=10.1;scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.render.filepath=str(ROOT/'output/statue_detail.png');bpy.ops.render.render(write_still=True)
camera.location=(0,-8,7.98);camera.rotation_euler=(Vector((0,0,7.94))-camera.location).to_track_quat('-Z','Y').to_euler()
data.ortho_scale=1.3;scene.render.resolution_x=900;scene.render.resolution_y=1000
scene.render.filepath=str(ROOT/'output/statue_face.png');bpy.ops.render.render(write_still=True)
triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects)
print('STATUE_COMPLETE',len(objects),'objects',triangles,'triangles',target.stat().st_size,'bytes')
