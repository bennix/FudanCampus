"""Photo-guided vegetation pilot; preserve every baseline mesh and transform."""
import bpy, math, random, json, hashlib, time
from pathlib import Path
from mathutils import Vector
R=Path.cwd(); O=R/'field-review/guanghua-refinement-v4/vegetation-v1'; O.mkdir(exist_ok=True)
BASE=O.parent/'west-exit-shape-v1/view-03/west-exit-shape.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE)); S=bpy.context.scene
rng=random.Random(92917)
def signature(o):
 return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(r) for r in o.matrix_world])).encode()).hexdigest()
before={o.name:signature(o) for o in S.objects if o.type=='MESH'}
basehash=hashlib.sha256(BASE.read_bytes()).hexdigest()
C=bpy.data.collections.new('06_Vegetation_photo_pilot');S.collection.children.link(C)
materials=[]
for name,color in [('olive',(.12,.19,.065)),('grey-green',(.19,.245,.12)),('deep-green',(.065,.13,.04)),('young-green',(.23,.30,.105)),('autumn',(.32,.24,.075)),('bark',(.105,.085,.065))]:
 m=bpy.data.materials.new('VEG1 '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.72
 materials.append(m)
B={}; leaf_count=0; stems=[]
def add(name,v,f,mi):
 vs,fs,ms=B.setdefault(name,([],[],[]));n=len(vs);vs.extend([tuple(x) for x in v]);fs.extend([tuple(n+i for i in p) for p in f]);ms.extend([mi]*len(f))
def leaf(name,p,size=.12,mi=None):
 global leaf_count
 p=Vector(p);a=rng.uniform(0,math.tau);tilt=rng.uniform(-.65,.8)
 u=Vector((math.cos(a),math.sin(a),tilt)).normalized()*size
 w=u.cross(Vector((0,0,1))).normalized()*size*.40
 # Folded pointed leaf; true opaque geometry, no alpha-card halos.
 add(name,[p-u*.52,p-w,p+u*.65,p+w,p+Vector((0,0,size*.12))],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],mi if mi is not None else rng.choices([0,1,2,3,4],[34,28,25,10,3])[0]);leaf_count+=1

def branch(name,a,b,r0,r1):
 a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
 if u.length<.01:u=d.cross(Vector((0,1,0)))
 u.normalize();v=d.cross(u);n=7
 verts=[p+r*(math.cos(i*math.tau/n)*u+math.sin(i*math.tau/n)*v) for p,r in [(a,r0),(b,r1)] for i in range(n)]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 add(name,verts,faces,5)

def ground(x,y):
 ob=bpy.data.objects['EPATH__photo_shape_ground'];inv=ob.matrix_world.inverted();hit,loc,normal,index=ob.ray_cast(inv@Vector((x,y,20)),Vector((0,0,-1)))
 return (ob.matrix_world@loc).z if hit else 0

def tree(name,x,y,h,spread,density):
 z=ground(x,y);p=Vector((x,y,z));fork=p+Vector((.30,-.18,h*.30));branch(name+' branches',p,p+Vector((-.12,.09,h*.16)),.23,.18);branch(name+' branches',p+Vector((-.12,.09,h*.16)),fork,.18,.125)
 stems.append(dict(name=name,x=x,y=y,z=z,height=h,spread=spread,confidence='inferred',sources=[4568,4574]))
 for j in range(7):
  angle=j*2.399+rng.uniform(-.25,.25);radius=spread*rng.uniform(.55,1)
  end=p+Vector((math.cos(angle)*radius,math.sin(angle)*radius,h*rng.uniform(.58,.88)))
  mid=fork.lerp(end,.55)+Vector((rng.uniform(-.35,.35),rng.uniform(-.35,.35),-.42));branch(name+' branches',fork,mid,.10,.055);branch(name+' branches',mid,end,.055,.017)
  for k in range(12):
   t=.12+k*.075;origin=mid.lerp(end,t)
   angle2=angle+rng.uniform(-1.8,1.8)
   tip=origin+Vector((math.cos(angle2)*rng.uniform(.4,1.1),math.sin(angle2)*rng.uniform(.4,1.1),rng.uniform(.25,.85)))
   branch(name+' branches',origin,tip,.017,.004)
   for q in range(density):
    t=rng.random();c=origin.lerp(tip,t)
    c+=Vector((rng.gauss(0,.30),rng.gauss(0,.30),rng.gauss(0,.22)))
    leaf(name+' leaves',c,rng.uniform(.10,.19))

def shrub(name,x,y,rx,ry,h,count):
 z=ground(x,y)
 for j in range(9):
  a=j*2.399;branch(name+' twigs',(x,y,z),(x+rx*.65*math.cos(a),y+ry*.65*math.sin(a),z+h*.75),.015,.003)
 for i in range(count):
  u=rng.uniform(-1,1);a=rng.uniform(0,math.tau);rad=rng.uniform(.65,1)**.5
  p=(x+rx*math.sqrt(1-u*u)*math.cos(a)*rad,y+ry*math.sqrt(1-u*u)*math.sin(a)*rad,z+h*.52+h*.48*u)
  leaf(name+' leaves',p,rng.uniform(.10,.21),rng.choice([0,1,2,2,3]))

# First render the actual inherited state. Then show visibility-only separately.
S.render.engine='CYCLES';S.cycles.samples=16;S.cycles.use_denoising=True
S.render.threads_mode='FIXED';S.render.threads=8
S.render.resolution_x=1100;S.render.resolution_y=825;S.render.resolution_percentage=100
S.camera=bpy.data.objects['SHAPE exit approximate']
def render(name,cam):
 S.camera=bpy.data.objects[cam];S.render.filepath=str(O/(name+'.png'));t=time.time();bpy.ops.render.render(write_still=True);return round(time.time()-t,2)
timings={};timings['before']=None # retained identical baseline render
restored=[]
for o in S.objects:
 if o.get('feature_id') in {'VEGETATION','E_TREES'}:
  if o.hide_render:restored.append(o.name)
  o.hide_render=False;o.hide_set(False)
timings['visibility']=None # retained visibility-only comparison
# Tree positions lie outside skylight, stair opening and walk; metres inferred.
tree('V01 southern small tree',68.6,41.5,4.8,2.4,42)
tree('V02 behind skylight',67.9,46.5,7.1,4.2,52)
tree('V03 northern spreading tree',76.0,50.9,7.2,4.3,52)
tree('V04 east garden backdrop',80.8,59.5,7.3,3.2,64)
tree('V05 south garden backdrop',78.4,35.8,6.5,3.0,58)
shrub('S01 broadleaf at south exit',77.6,44.9,.70,.85,1.15,2200)
shrub('S02 south approach',76.2,42.3,.75,.80,1.05,1900)
shrub('S03 north exit bush',78.0,50.4,.80,.80,1.10,2100)
shrub('S04 clipped foreground',68.6,42.7,.70,.65,.95,1800)
# Surface foliage follows existing hedge meshes exactly, retaining hardscape.
hedge_sources=[]
for ob in list(S.objects):
 if ob.type!='MESH':continue
 fid=ob.get('feature_id'); selected=(fid=='ESKY' and 'planted-shrubs' in ob.name) or (fid=='EOPEN_S' and 'hedge' in ob.name) or (fid=='ETERR' and '__hedge__' in ob.name)
 if not selected:continue
 hedge_sources.append(ob.name);ob.data.calc_loop_triangles()
 for tri in ob.data.loop_triangles:
  a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices];normal=(b-a).cross(c-a)
  area=normal.length*.5
  if area<1e-8:continue
  normal.normalize()
  if normal.z<-.3:continue
  count=int(area*420+rng.random())
  for i in range(count):
   u=math.sqrt(rng.random());v=rng.random();p=(1-u)*a+u*(1-v)*b+u*v*c+normal*rng.uniform(.015,.08)
   leaf('H '+fid+' textured leaves',p,rng.uniform(.055,.095),rng.choices([0,1,2,3],[38,22,32,8])[0])
for name,(v,f,mi) in B.items():
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update();ob=bpy.data.objects.new(name,mesh);C.objects.link(ob)
 for m in materials:mesh.materials.append(m)
 for p,idx in zip(mesh.polygons,mi):p.material_index=idx;p.use_smooth='branches' in name or 'twigs' in name
 ob['feature_id']='VEGETATION_PILOT';ob['source_photos']=[4568,4574];ob['geometry_confidence']='inferred';ob['random_seed']=92917
assert all(signature(bpy.data.objects[n])==h for n,h in before.items())
S.camera=bpy.data.objects['SHAPE exit approximate'];S['vegetation_revision']='v1 photo pilot; tree visibility restored; local trees/shrubs/hedge foliage added'
checkpoint=O/'vegetation-v1.blend';bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
timings['after']=render('after-exit','SHAPE exit approximate')
timings['side']=render('after-side','SHAPE side')
timings['top']=render('after-top','SHAPE top')
# Export independent review, not production campus replacement.
bpy.ops.object.select_all(action='DESELECT')
for ob in S.objects:
 if ob.type=='MESH' and not ob.hide_render:ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'vegetation-v1.glb'),export_format='GLB',use_selection=True,export_extras=True)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
assert all(signature(bpy.data.objects[n])==h for n,h in before.items())
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==basehash
report=dict(baseline_unchanged=True,all_original_meshes_and_transforms_unchanged=True,protected_mesh_count=len(before),reopened=True,restored_visibility=restored,trees=stems,leaf_count=leaf_count,added_meshes=len(B),hedge_sources=hedge_sources,render_seconds=timings,glb_bytes=(O/'vegetation-v1.glb').stat().st_size,limitations=['Manual approximate camera, not calibrated','Tree locations and sizes inferred','Existing road issues retained','Pilot only; full garden refinement pending','Browser performance not measured'])
(O/'validation.json').write_text(json.dumps(report,indent=2))
print('VEGETATION_PILOT_COMPLETE',flush=True)

# Keep web export compatible with procedural baseline materials.
import runpy
runpy.run_path(str(O/'export_web.py'),run_name='__main__')
