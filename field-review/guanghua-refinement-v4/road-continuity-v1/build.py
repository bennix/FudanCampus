import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;D=json.loads((O/'shape.json').read_text())
base=O.parent/'west-exit-shape-v1/view-03/west-exit-shape.blend'
before=hashlib.sha256(base.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(base));s=bpy.context.scene
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
lawn=next(o for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')=='LAWN');ls=sig(lawn);lname=lawn.name
root=next(o for o in bpy.data.objects if o.type=='EMPTY' and o.get('feature_id')=='EPATH')
for o in list(bpy.data.objects):
 if o.get('feature_id')=='EPATH' and o.type in {'MESH','CURVE'}:bpy.data.objects.remove(o,do_unlink=True)
for name,material in [('road','pink-path'),('ground','FIN_garden_grass')]:
 data=D[name];m=bpy.data.meshes.new('Continuous east '+name);m.from_pydata(data['vertices'],[],data['faces']);m.update()
 ob=bpy.data.objects.new('EPATH__continuous_'+name,m);root.users_collection[0].objects.link(ob);ob.parent=root
 m.materials.append(bpy.data.materials[material]);ob['feature_id']='EPATH';ob['geometry_confidence']='inferred';ob['note']=D['uncertainty'];ob['source_photos']=[4568,4572,4574,4565,4582]
 uv=m.uv_layers.new(name='MetreUV')
 for loop in m.loops:
  co=m.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x*.3,co.y*.3)
 for p in m.polygons:p.use_smooth=(name=='ground' and p.normal.z>.01)
dx=D['registration_x']
def camera(name,loc,target,scale):
 d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);s.collection.objects.link(c);c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;return c
views={'exit':bpy.data.objects['SHAPE exit approximate'],'side':bpy.data.objects['SHAPE side'],'top':camera('Continuous east top',(88+dx,50,100),(88+dx,50,0),105)}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=825;s.render.resolution_percentage=100
s.camera=views['exit'];assert sig(lawn)==ls
target=O/'east-road-continuous.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
for name,c in views.items():
 s.camera=c;s.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.open_mainfile(filepath=str(target));assert sig(bpy.data.objects[lname])==ls;assert hashlib.sha256(base.read_bytes()).hexdigest()==before
(O/'check.json').write_text(json.dumps({'baseline_unchanged':True,'lawn_unchanged':True,'reopens':True,'road_domain_components':1}))
print('CONTINUITY_SAVED')
