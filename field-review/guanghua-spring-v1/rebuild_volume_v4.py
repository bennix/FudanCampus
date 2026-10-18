"""Rebuild only the identified cherry tree from the user's flowering reference.
Root registration is inherited. Visible habit is photo-supported; depth inferred.
"""
import bpy,sys,json,random,math,bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;R=O.parents[1]
sys.path.insert(0,str(R/'field-review/guanghua-refinement-v4/scene-unified-v5'))
from scene_fingerprints import sha,snapshot,write
BASE=O/'guanghua-spring-photo-v3.blend'
OUT=O/'guanghua-spring-volume-v4.blend';base_sha=sha(BASE)
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene;before=snapshot()
target='V6 East spreading 01';wood=bpy.data.objects[target+' wood'];flowers=bpy.data.objects[target+' leaves'];heart=bpy.data.objects['SIGN__continuous-heart__FIN_red']
root=list(wood.location);changed={wood.name,flowers.name};rng=random.Random(4312)
def bounds(ob):
 pts=[ob.matrix_world@Vector(p) for p in ob.bound_box]
 return [[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]]
bpy.context.view_layer.update()
clearance=bounds(heart)[0][1]-max(bounds(bpy.data.objects[n])[1][1] for n in ['SIGN__seat-back__FIN_blue','SIGN__back-slats__FIN_blue','SIGN__seat-slats__FIN_blue']);assert clearance>.11
# Reuse accepted native materials exactly.
barks=list(wood.data.materials)[:3];white=wood.data.materials[3]
wv=[];wf=[];wm=[];coarse_faces=[];branch_paths=[];flower_paths=[]
def photo_shape(p):
 return Vector((p[0]*1.30,p[1]*1.20,p[2] if p[2]<1.55 else 1.55+(p[2]-1.55)*.91))
def tube(points,radii,kind=0,sides=8,record=True,coarse=False):
 control=[Vector(p) for p in points];pts=[];rs=[]
 for i in range(len(control)-1):
  a=control[max(i-1,0)];b=control[i];c=control[i+1];d=control[min(i+2,len(control)-1)]
  for j in range(4):
   t=j/4;pts.append((b*2+(c-a)*t+(a*2-b*5+c*4-d)*t*t+(-a+b*3-c*3+d)*t*t*t)*.5);rs.append(radii[i]*(1-t)+radii[i+1]*t)
 pts.append(control[-1]);rs.append(radii[-1]);pts=[photo_shape(p) for p in pts];start=len(wv);face_start=len(wf)
 for i,(p,r) in enumerate(zip(pts,rs)):
  direction=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();axis=direction.cross(Vector((0,0,1)))
  if axis.length<.01:axis=direction.cross(Vector((0,1,0)))
  axis.normalize();other=direction.cross(axis).normalized()
  for j in range(sides):
   ang=2*math.pi*j/sides;uneven=1+.05*math.sin(j*3+i*.7)
   wv.append(tuple(p+(axis*math.cos(ang)+other*math.sin(ang))*r*uneven))
 for i in range(len(pts)-1):
  mat=3 if (pts[i].z+pts[i+1].z)/2<1.4 else kind
  for j in range(sides):wf.append((start+i*sides+j,start+i*sides+(j+1)%sides,start+(i+1)*sides+(j+1)%sides,start+(i+1)*sides+j));wm.append(mat)
 wf.extend([tuple(start+j for j in reversed(range(sides))),tuple(start+(len(pts)-1)*sides+j for j in range(sides))]);wm.extend([3 if pts[0].z<1.4 else kind,kind])
 if coarse:coarse_faces.extend(range(face_start,len(wf)))
 if record:branch_paths.append([list(p) for p in pts])
 return control
trunk=tube([(0,0,-.05),(.04,.015,.35),(.10,.02,.9),(.05,0,1.35),(.08,.03,1.78)],[.58,.47,.41,.38,.31],0,14,coarse=True)
# Unequal heavy limbs leave a clear low fork. Their centerlines remain visible.
primary_specs=[
 [(0,0,1.48),(-.9,.10,2.03),(-2.2,.15,2.47),(-3.6,.40,2.93),(-4.65,.65,3.95)],
 [(.07,.0,1.55),(.85,-.25,2.15),(2.05,-.55,2.70),(3.35,-.60,3.36),(4.5,-.4,4.60)],
 [(.03,.05,1.62),(.3,.70,2.35),(.75,1.55,3.32),(.45,2.45,4.70),(.75,3.3,5.9)],
 [(.0,.02,1.58),(-.6,.25,2.4),(-1.25,.75,3.8),(-1.80,1.25,5.15),(-2.25,1.5,6.45)],
 [(.06,.03,1.64),(.55,.30,2.5),(1.35,.65,3.8),(1.8,1.00,5.25),(2.25,1.3,6.60)],
 [(.04,-.06,1.67),(.08,-.65,2.8),(-.25,-1.35,4.0),(-.50,-1.9,5.5),(-.70,-2.10,7.0)],
 [(.08,-.03,1.55),(.60,-.6,2.3),(1.40,-1.6,3.35),(2.65,-2.5,4.55),(3.3,-2.8,5.8)],
]
for pi,points in enumerate(primary_specs):
 heavy=[1.0,.98,.52,.68,.60,.50,.55][pi]
 main=tube(points,[r*heavy for r in [.32,.265,.18,.105,.045]],pi%2,12,coarse=True)
 for ai in [1,2,3,4]:
  start=main[ai];radial=Vector((start.x,start.y,0));radial.normalize()
  side=Vector((-radial.y,radial.x,0));sign=-1 if (pi+ai)%2 else 1
  lateral=side*sign*rng.uniform(.6,1.3)+radial*rng.uniform(.25,.65)
  length=rng.uniform(1.25,2.05)
  end=start+lateral*length+Vector((0,0,rng.uniform(1.0,1.65)))
  mid=start.lerp(end,.5)+Vector((rng.uniform(-.18,.18),rng.uniform(-.18,.18),-.10))
  branch=tube([start,mid,end],[.065,.035,.010],1,7)
  flower_paths.append(branch[1:])
  for ti in range(9):
   attach=mid.lerp(end,.04+ti*.105+rng.uniform(-.03,.03))
   azimuth=rng.uniform(0,2*math.pi)
   d=side*(math.cos(azimuth)*rng.uniform(.35,.95))+radial*rng.uniform(-.40,.65)+Vector((0,0,rng.uniform(.15,.95)))
   tip=attach+d*rng.uniform(.65,1.12)
   twig=tube([attach,attach.lerp(tip,.52)+Vector((.03,-.035,-.06)),tip],[.020,.012,.003],2,5)
   flower_paths.append(twig)
   # Two delicate fans at the end of each twig carry blossoms rather than clouds.
   for fi in range(4):
    fork=twig[1].lerp(twig[2],.55)
    angle=rng.uniform(0,2*math.pi)
    fan=d.normalized()*rng.uniform(.20,.48)+Vector((math.cos(angle)*rng.uniform(.15,.40),math.sin(angle)*rng.uniform(.15,.40),rng.uniform(-.12,.37)))
    small=tube([fork,fork+fan*.5,fork+fan],[.008,.005,.0018],2,5)
    flower_paths.append(small)
    for qi in range(2):
     stem=small[0].lerp(small[-1],.45+qi*.28)
     angle=rng.uniform(0,2*math.pi)
     spray=fan.normalized()*rng.uniform(.16,.30)+Vector((math.cos(angle)*rng.uniform(.12,.25),math.sin(angle)*rng.uniform(.12,.25),rng.uniform(-.12,.25)))
     fine_tip=tube([stem,stem+spray*.48,stem+spray],[.0045,.0025,.0009],2,4)
     flower_paths.append(fine_tip)
# Connected interior shoots bridge the sparse centre at several heights.
# Each is anchored to an existing main limb; no detached flower clouds.
interior_paths=[]
for ci in range(16):
 main=[Vector(p) for p in primary_specs[ci%len(primary_specs)]]
 start=main[1].lerp(main[2],rng.uniform(.35,.85))
 angle=ci*2.399963+ rng.uniform(-.22,.22)
 radius=rng.uniform(.35,2.1)
 end=Vector((math.cos(angle)*radius,math.sin(angle)*radius,rng.uniform(4.65,6.65)))
 mid=start.lerp(end,.52)+Vector((rng.uniform(-.22,.22),rng.uniform(-.22,.22),.14))
 stem=tube([start,mid,end],[.042,.021,.004],1,6)
 interior_paths.append(stem[1:])
 for ti in range(10):
  attach=mid.lerp(end,rng.uniform(.10,.95));az=rng.uniform(0,2*math.pi)
  delta=Vector((math.cos(az)*rng.uniform(.35,1.15),math.sin(az)*rng.uniform(.35,1.15),rng.uniform(-.2,.75)))
  tip=attach+delta
  twig=tube([attach,attach.lerp(tip,.48)+Vector((0,0,.06)),tip],[.015,.008,.0016],2,5)
  interior_paths.append(twig)
  for fi in range(4):
   at=twig[1].lerp(twig[2],rng.uniform(.10,.85));az=rng.uniform(0,2*math.pi)
   delta=Vector((math.cos(az)*rng.uniform(.16,.40),math.sin(az)*rng.uniform(.16,.40),rng.uniform(-.16,.40)))
   interior_paths.append(tube([at,at+delta*.47,at+delta],[.005,.0025,.0008],2,4))
flower_paths.extend(interior_paths)
# Low buttress roots are retained at the original root location.
for i in range(5):
 ang=i*2*math.pi/5+.2;end=Vector((math.cos(ang)*.77,math.sin(ang)*.65,-.02))
 tube([Vector((0,0,.3)),end*.6+Vector((0,0,.04)),end],[.16,.105,.035],0,7,False,True)
def subset_mesh(name,indices):
 used=sorted({v for i in indices for v in wf[i]});remap={v:i for i,v in enumerate(used)};me=bpy.data.meshes.new(name);me.from_pydata([wv[v] for v in used],[],[tuple(remap[v] for v in wf[i]) for i in indices])
 for m in barks+[white]:me.materials.append(m)
 for p,i in zip(me.polygons,indices):p.material_index=wm[i];p.use_smooth=True
 me.update();return me
coarse=set(coarse_faces);wood.data=subset_mesh('Cherry connected trunk and heavy limbs',coarse_faces)
bpy.context.view_layer.objects.active=wood;wood.select_set(True)
mod=wood.modifiers.new('Union heavy low forks','REMESH');mod.mode='VOXEL';mod.voxel_size=.038;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=wood.modifiers.new('Soften aged branch junctions','SMOOTH');mod.factor=.32;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name)
for p in wood.data.polygons:p.material_index=3 if p.center.z<1.35 else (1 if math.sin(p.center.x*12+p.center.z*4)*math.sin(p.center.y*9)> .55 else 0)
fine=subset_mesh('Cherry connected secondary twigs',[i for i in range(len(wf)) if i not in coarse]);bm=bmesh.new();bm.from_mesh(wood.data);bm.from_mesh(fine);bm.to_mesh(wood.data);bm.free();bpy.data.meshes.remove(fine);wood.data.update()
wood['geometry_confidence']='Photo-supported low fork, heavy spreading limbs; depth and exact proportions inferred';wood['reference']='reference-spring-cherry.jpg';wood['fork_height_native']=1.55
flower_mats=list(flowers.data.materials)
fv=[];ff=[];fm=[];anchors=[]
for path in flower_paths:
 for segment in range(len(path)-1):
  a,b=path[segment:segment+2];dist=(b-a).length;count=max(1,int(dist/.075))
  for i in range(count):
   if rng.random()<.055:continue
   center=a.lerp(b,(i+.3+rng.random()*.4)/count);anchors.append(list(center))
   tangent=(b-a).normalized();u=tangent.cross(Vector((0,0,1)))
   if u.length<.01:u=tangent.cross(Vector((0,1,0)))
   u.normalize();w=tangent.cross(u).normalized()
   for j in range(rng.choice([4,4,5])):
    angle=rng.random()*2*math.pi;radial=u*math.cos(angle)+w*math.sin(angle)
    c=center+radial*rng.uniform(.045,.20)+tangent*rng.uniform(-.045,.045)
    normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1))).normalized()
    x=normal.cross(Vector((0,0,1)))
    if x.length<.01:x=normal.cross(Vector((0,1,0)))
    x.normalize();y=normal.cross(x).normalized();size=rng.uniform(.105,.175)
    x*=size*.5;y*=size*rng.uniform(.45,.60)
    # Six-vertex shallow curved spray: two differently facing halves.
    bulge=normal*size*rng.uniform(.16,.30)
    start=len(fv);fv.extend([tuple(c-x-y),tuple(c-y+bulge),tuple(c+x-y),tuple(c-x+y),tuple(c+y+bulge),tuple(c+x+y)])
    mi=rng.choices([0,1,2],[.78,.20,.02])[0]
    ff.extend([(start,start+1,start+4,start+3),(start+1,start+2,start+5,start+4)]);fm.extend([mi,mi])
fv=[tuple(photo_shape(p)) for p in fv];anchors=[list(photo_shape(p)) for p in anchors]
me=bpy.data.meshes.new(target+' blossom sprays attached to twigs');me.from_pydata(fv,[],ff)
for m in flower_mats:me.materials.append(m)
for p,mi in zip(me.polygons,fm):p.material_index=mi
uv=me.uv_layers.new(name='Blossom UV')
for pi,p in enumerate(me.polygons):
 coords=[(0,0),(.5,0),(.5,1),(0,1)] if pi%2==0 else [(.5,0),(1,0),(1,1),(.5,1)]
 for li,coord in zip(p.loop_indices,coords):uv.data[li].uv=coord
me.update();flowers.data=me;flowers['season']='spring branch-led bloom';flowers['source_object']=target+' leaves';flowers['geometry_confidence']='Blossom anchors generated directly on fine branch centerlines; inferred individual flowers';flowers['reference']='reference-spring-cherry.jpg'
s['spring_target']=target;s['spring_reference_confidence']='Single view: habit, trunk and color supported; unseen depth and absolute size inferred'
def camera(name,loc,aim,lens):
 d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);s.collection.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(aim)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
camera('Spring cherry review',(52,27,7.5),(67.9,46.5,4.1),43)
camera('Spring cherry photo angle',(65.5,24.8,5.6),(67.9,46.5,4.2),42)
after=snapshot();drift=[n for n,v in before.items() if n not in changed and after.get(n)!=v];assert not drift,drift;assert list(wood.location)==root
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT));source_sha=sha(OUT)
# Export the two editable source meshes without a whole-campus re-export.
export_scene=bpy.data.scenes.new('Cherry replacement only');copies=[]
for ob in [wood,flowers]:
 cp=ob.copy();export_scene.collection.objects.link(cp);cp.matrix_world=ob.matrix_world.copy();cp['source_object']=ob.name;cp['campusVegetation']=True;copies.append(cp)
bpy.context.window.scene=export_scene
bpy.ops.export_scene.gltf(filepath=str(O/'cherry-volume-v4-native.glb'),export_format='GLB',export_extras=True,export_yup=True,export_texcoords=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_animations=False,use_selection=False,use_active_scene=True)
bpy.context.window.scene=s
for cp in copies:bpy.data.objects.remove(cp,do_unlink=True)
bpy.data.scenes.remove(export_scene)
bpy.ops.wm.open_mainfile(filepath=str(OUT));assert snapshot()==after;assert sha(BASE)==base_sha
report=dict(source=str(OUT),source_sha256=source_sha,baseline=str(BASE),baseline_sha256=base_sha,target_tree=target,root_native=root,changed=sorted(changed),non_target_meshes_preserved=len(before)-2,drift=[],blossom_cards=len(ff)//2,twig_anchor_sites=len(anchors),branch_paths=len(branch_paths),fork_height_native=1.55,trunk_base_diameter_native=1.16,canopy_horizontal_scale=[1.30,1.20],heart_clearance_native=clearance,heart_clearance_web=clearance*2/3,confidence='Visible low fork, heavy lateral limbs, pale varying blossoms and whitewash photo-supported; depth and absolute scale inferred')
wood=bpy.data.objects[target+' wood'];flowers=bpy.data.objects[target+' leaves']
report['central_shoots']=16;report['generation']='Non-coplanar connected twigs; volumetric anchors; small curved two-half blossom sprays';report['materials_reused']=True
report['wood_bounds_native']=bounds(wood);report['flower_bounds_native']=bounds(flowers)
write(O/'volume-v4-native-validation.json',report);write(O/'volume-v4-branch-centerlines.json',dict(root=root,paths=branch_paths,blossom_anchors=anchors))
print('BRANCH_LED_CHERRY_VALIDATED '+json.dumps(report),flush=True)
