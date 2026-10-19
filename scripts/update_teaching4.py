"""Build only teaching building 17, export, and render photo-comparison views."""
import bpy, sys, json, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from teaching4_geometry import build_teaching4
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
objects=build_teaching4();bpy.context.view_layer.update()
public=ROOT/'web/public'
blend=ROOT/'assets/buildings/17.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
target=public/'models/buildings/17.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',export_extras=True)
data=target.read_bytes();asset=dict(url='models/buildings/17.glb',bytes=len(data),revision=hashlib.sha256(data).hexdigest()[:12])
corners=[o.matrix_world@Vector(c) for o in objects for c in o.bound_box]
lo=[min(v[i] for v in corners) for i in range(3)];hi=[max(v[i] for v in corners) for i in range(3)]
manifest=json.loads((public/'campus-manifest.json').read_text())
manifest['buildings']=[a for a in manifest['buildings'] if a['id']!='17']
manifest['buildings'].append(dict(id='17',name='第四教学楼',**asset,overview=asset,overviewMode='full',position=[-154.4,0,-204],rotation=[0,0,0],orientationBaked=True,bounds=dict(min=[lo[0],lo[2],-hi[1]],max=[hi[0],hi[2],-lo[1]]),labelPosition=[-154.4,22,-204],loadDistance=240,source='Eight user photographs; map footprint; dimensions inferred'))
manifest['buildings'].sort(key=lambda a:int(a['id']))
(public/'campus-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
labels=json.loads((public/'buildings.json').read_text())
for a in labels['buildings']:
    if a['id']=='17':a['position']=[-154.4,22,-204];a['source']='user photographs; approximate dimensions'
(public/'buildings.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2)+'\n')
scene=bpy.context.scene;scene.world.use_nodes=True
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(.55,.61,.68,1);bg.inputs[1].default_value=.6
light=bpy.data.lights.new('soft sun','SUN');light.energy=2.4;light.angle=.3
o=bpy.data.objects.new('soft sun',light);scene.collection.objects.link(o);o.rotation_euler=(.5,-.4,-.6)
camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(camera);scene.camera=camera
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
for name,pos,look,lens in [('front',(-42,-57,27),(0,-2,8),43),('rear',(38,56,24),(0,1,10),43),('sculpture',(20,-24,10),(10,-10.8,3.4),52)]:
    camera.location=pos;camera.rotation_euler=(Vector(look)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens
    scene.render.filepath=str(ROOT/f'output/teaching4-{name}.png');bpy.ops.render.render(write_still=True)
print('TEACHING4_COMPLETE',len(objects),len(data))
