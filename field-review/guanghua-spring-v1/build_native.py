import bpy,sys,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;R=O.parents[1]
sys.path.insert(0,str(R/'field-review/guanghua-refinement-v4/scene-unified-v5'))
from scene_fingerprints import sha,snapshot,write
BASE=R/'field-review/guanghua-refinement-v4/closeout-final/guanghua-closeout-final.blend'
OUT=O/'guanghua-spring-full-bloom.blend';baseline_sha=sha(BASE)
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene;before=snapshot()
target='V6 East spreading 01';wood=bpy.data.objects[target+' wood'];leaves=bpy.data.objects[target+' leaves'];heart=bpy.data.objects['SIGN__continuous-heart__FIN_red']
root=list(wood.location);changed={wood.name,leaves.name,heart.name}
heart.location.y+=.32;heart['spring_repair']='Heart moved behind chair; geometry and base preserved'
def bounds(ob):
    ps=[ob.matrix_world@Vector(p) for p in ob.bound_box]
    return [[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]]
bpy.context.view_layer.update()
seat=[bpy.data.objects[n] for n in ['SIGN__seat-back__FIN_blue','SIGN__back-slats__FIN_blue','SIGN__seat-slats__FIN_blue']]
clearance=bounds(heart)[0][1]-max(bounds(o)[1][1] for o in seat);assert clearance>.11
im=bpy.data.images.load(str(O/'spring-blossom-atlas.png'),check_existing=False);im.pack()
m=bpy.data.materials.new('Spring cherry pale pink-white blossom clusters');m.use_nodes=True;m.diffuse_color=(.88,.74,.79,1)
p=m.node_tree.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.8;p.inputs['Specular IOR Level'].default_value=.2
t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(t.outputs['Alpha'],p.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
leaves.data=leaves.data.copy();me=leaves.data;a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);q=a.reshape(-1,4,3);c=q.mean(axis=1);u=(q[:,2]-q[:,0])*.5;w=(q[:,1]-q[:,3])*.5
u*=1.38;w*=1.38
q[:]=np.stack([c-u-w,c+u-w,c+u+w,c-u+w],axis=1);me.vertices.foreach_set('co',q.ravel());me.materials.clear();me.materials.append(m);me.polygons.foreach_set('material_index',np.zeros(len(me.polygons),np.int32));me.update()
uv=me.uv_layers.new(name='Spring blossom UV');coords=np.tile([[0,0],[1,0],[1,1],[0,1]],(len(c),1));ix=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',ix);uv.data.foreach_set('uv',coords[ix].astype(np.float32).ravel())
leaves['season']='spring full bloom';leaves['blossom_spray_scale']=1.38;leaves['reference']='reference-spring-cherry.jpg; user target screenshot';leaves['season_confidence']='Photo-confirmed pale pink-white bloom; existing branch structure and placement inferred'
wood.data=wood.data.copy();wm=bpy.data.materials.new('Spring cherry whitewashed lower trunk');wm.use_nodes=True;wm.diffuse_color=(.72,.72,.67,1);wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=wm.diffuse_color;wm.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.96
wood.data.materials.append(wm);white=0
for poly in wood.data.polygons:
    if poly.center.z<1.4:poly.material_index=len(wood.data.materials)-1;white+=1
wood['season_reference']='Whitewashed base observed in user spring photo; upper woody geometry retained'
s['spring_target']=target;s['heart_behind_chair_clearance_native']=clearance
def camera(name,loc,target,lens):
    d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;return ob
camera('Spring cherry review',(48,27,7.5),(68,46.5,4.4),43)
camera('Heart chair front',(29.25,5.2,2.0),(29.25,10.5,1.55),48)
camera('Heart chair side',(32.5,7.0,2.2),(29.25,10.45,1.4),48)
after=snapshot();drift=[n for n,v in before.items() if n not in changed and after.get(n)!=v];assert not drift,drift
assert list(wood.location)==root
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT));after_sha=sha(OUT)
bpy.ops.wm.open_mainfile(filepath=str(OUT));assert snapshot()==after;assert sha(BASE)==baseline_sha
report=dict(source=str(OUT),source_sha256=after_sha,baseline=str(BASE),baseline_sha256=baseline_sha,target_tree=target,root_native=root,changed=sorted(changed),non_target_meshes_preserved=len(before)-3,drift=[],blossom_cards=len(c),blossom_spray_scale=1.38,blossom_area_multiplier=1.38**2,whitewash_faces=white,heart_translation_native=[0,.32,0],heart_clearance_native=clearance,heart_clearance_web=clearance*2/3,confidence='Flower color, flowering habit, and whitewashed trunk photo-supported; placement and absolute size inherited and inferred')
write(O/'native-validation.json',report)
print('SPRING_NATIVE_VALIDATED '+json.dumps(report,ensure_ascii=False),flush=True)
