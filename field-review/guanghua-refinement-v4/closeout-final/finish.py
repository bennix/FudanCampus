"""Bounded native appearance edits after the first structural diagnostic."""
import bpy,bmesh,sys,json,math,random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O))
from assemble import read,make,solid,camera,metric_uv,collection
sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import snapshot,sha,write,plain
SOURCE=O/'guanghua-closeout-structure.blend';TARGET=O/'guanghua-closeout-final.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
before=snapshot();changed=set();added=[];edits=[];rng=random.Random(10010608)
def touch(o,task,note):
 changed.add(o.name);o['closeout_task']=task;o['closeout_note']=note
def derived_material(o,index,color=None,roughness=None,metallic=None):
 old=o.data.materials[index];m=old.copy();m.name='CLOSEOUT '+old.name;o.data.materials[index]=m
 if color is not None:
  m.diffuse_color=(*color,1)
  if m.use_nodes:
   p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if p:
    for link in list(p.inputs['Base Color'].links):m.node_tree.links.remove(link)
    p.inputs['Base Color'].default_value=(*color,1)
 if m.use_nodes:
  p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if p:
   if roughness is not None:p.inputs['Roughness'].default_value=roughness
   if metallic is not None:p.inputs['Metallic'].default_value=metallic
 return m
def coords(o):
 a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a);return a.reshape(-1,3)
def setcoords(o,a):o.data.vertices.foreach_set('co',a.astype(np.float32).ravel());o.data.update()
def bvh(objects):
 v=[];f=[]
 for o in objects:
  o.data.calc_loop_triangles()
  for t in o.data.loop_triangles:
   q=[o.matrix_world@o.data.vertices[i].co for i in t.vertices]
   if (q[1]-q[0]).cross(q[2]-q[0]).z<1e-8:continue
   k=len(v);v.extend(q);f.append((k,k+1,k+2))
 return BVHTree.FromPolygons(v,f,all_triangles=True)
ground=bvh([o for o in s.objects if o.type=='MESH' and not o.hide_render and (o.get('feature_id')=='GROUND' or o.name=='C04 continuous ground')])
road=bvh([bpy.data.objects['C04 continuous road']])
tree_moves=[];tree_groups={}
for o in s.objects:
 if o.type=='MESH' and o.get('feature_id')=='TREE_CANOPY_V6':tree_groups.setdefault(o.get('tree_group'),[]).append(o)
for group,objects in tree_groups.items():
 loc=objects[0].location.copy();x,y=loc.x,loc.y
 if 67.1<x<91.3 and 35<y<73.3:
  root=ground.ray_cast(Vector((x,y,30)),Vector((0,0,-1)))[0];hit=road.ray_cast(Vector((x,y,30)),Vector((0,0,-1)))[0]
  if hit is not None:
   found=None
   for dist in [.8,1.3,1.8,2.4,3.0]:
    for k in range(16):
     xx=x+dist*math.cos(k*math.tau/16);yy=y+dist*math.sin(k*math.tau/16)
     g=ground.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0]
     h=road.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0]
     if g and h is None and 67.8<xx<90 and 35<yy<73:found=(xx,yy,g.z);break
    if found:break
   assert found,('No planting ground for tree',group)
   root=Vector(found)
  if root:
   for o in objects:o.location=(root.x,root.y,root.z+.002);touch(o,'C06','Root reprojected to repaired terrain; original XY retained unless intersecting the road')
   tree_moves.append(dict(group=group,before=list(loc),after=list(objects[0].location),confidence='inferred position/level'))
 for o in objects:
  a=coords(o);h=max(1,a[:,2].max());z=np.maximum(a[:,2],0)/h
  # A continuous spatial warp applies to both limbs and foliage, preserving joins.
  a[:,0]+=.15*z*z*np.sin(a[:,2]*.61+y*.17);a[:,1]+=.12*z*z*np.sin(a[:,2]*.47+x*.09)
  if 'leaves' in o.name or 'needles' in o.name:
   if len(a)%4==0:
    q=a.reshape(-1,4,3);c=q.mean(axis=1,keepdims=True)
    q[:]=c+(q-c)*(1.12 if 'leaves' in o.name else 1.07)
  setcoords(o,a);touch(o,'C06' if 'south' not in o.name else 'C07','Continuous unequal limb warp and slightly fuller twig blades; v6 root provenance and crown gaps retained')
edits.append(dict(task='C06/C07',trees=len(tree_groups),root_reprojections=tree_moves,seed=10010608))
# Round and shorten existing 9-vertex, 8-triangle leaf fans without changing the
# base endpoint. Twig geometry, seeds, envelopes and all opening clearances remain.
leaf_fans=0;processed_leaf_meshes=set()
for o in list(s.objects):
 if o.type!='MESH' or o.hide_render or o.get('feature_id')!='GARDEN_VEGETATION_V3':continue
 me=o.data
 if me.as_pointer() in processed_leaf_meshes:
  touch(o,'C08','Shared leaf prototype edited once; leaf bases and twig geometry retained');continue
 processed_leaf_meshes.add(me.as_pointer())
 starts=np.empty(len(me.polygons),np.int32);totals=starts.copy();me.polygons.foreach_get('loop_start',starts);me.polygons.foreach_get('loop_total',totals)
 ix=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',ix)
 rows=np.zeros((len(me.polygons),3),np.int32);valid=totals==3;rows[valid]=ix[starts[valid,None]+np.arange(3)]
 cand=np.where(valid&(rows[:,1]==rows[:,0]+1)&(rows[:,2]==rows[:,0]+8))[0];cand=cand[cand+7<len(rows)]
 bases=[]
 for j in cand:
  b=int(rows[j,0]);r=rows[j:j+8]
  if np.array_equal(r[:,0],np.arange(b,b+8)) and np.all(r[:,2]==b+8):bases.append(b)
 if not bases:continue
 a=coords(o);inds=np.asarray(bases)[:,None]+np.arange(9);q=a[inds].copy();base=q[:,0].copy();u=(q[:,4]-q[:,0])*.5;w=(q[:,6]-q[:,2])*.5
 p=base+u*.81
 q[:,0]=base;q[:,4]=base+u*1.62
 for j,t,sign,width in [(1,.26,-1,.73),(2,.81,-1,1.05),(3,1.36,-1,.73),(5,1.36,1,.73),(6,.81,1,1.05),(7,.26,1,.73)]:q[:,j]=base+u*t+w*sign*width
 q[:,8]=p+np.array([0,0,.008]);a[inds]=q;setcoords(o,a);leaf_fans+=len(bases)
 touch(o,'C08','Existing leaf bases retained; blades shortened to 81% and oval shoulders widened; no new isolated leaf clouds')
edits.append(dict(task='C08',rounded_leaf_fans=leaf_fans,leaf_base_preserved=True))
# Add connected fine sprigs on the rebuilt foreground beds, keeping stone visible.
plan=read(O/'planter-pack.json');leaf_v=[];leaf_f=[];stem_v=[];stem_f=[]
def tube(points,r0=.015,r1=.005,vs=stem_v,fs=stem_f):
 pts=[Vector(p) for p in points];start=len(vs);n=6
 for j,p in enumerate(pts):
  d=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();u=d.cross(Vector((0,1,0))).normalized();w=d.cross(u);r=r0+(r1-r0)*j/(len(pts)-1)
  for k in range(n):vs.append(tuple(p+r*(u*math.cos(k*math.tau/n)+w*math.sin(k*math.tau/n))))
 fs.extend([tuple(start+i for i in reversed(range(n))),tuple(start+(len(pts)-1)*n+i for i in range(n))])
 for j in range(len(pts)-1):
  for k in range(n):a=start+j*n+k;b=start+j*n+(k+1)%n;fs.append((a,b,b+n,a+n))
def blade(p,length=.085,width=.038,angle=0,vs=leaf_v,fs=leaf_f):
 p=Vector(p);u=Vector((math.cos(angle),math.sin(angle),.22))*length;w=Vector((-math.sin(angle),math.cos(angle),0))*width;b=len(vs)
 # Six-vertex curved oval, attached at its base.
 vs.extend([tuple(p),tuple(p+u*.35-w),tuple(p+u*.8-w*.76),tuple(p+u*1.12),tuple(p+u*.8+w*.76),tuple(p+u*.35+w)])
 fs.extend([(b,b+1,b+2),(b,b+2,b+3),(b,b+3,b+4),(b,b+4,b+5)])
for ob in [o for o in s.objects if o.get('closeout_role')=='vegetation' and o.get('closeout_task')=='C03']:
 tree=bvh([ob]);vs=[];fs=[];sv=[];sf=[]
 lo=np.min(coords(ob),axis=0);hi=np.max(coords(ob),axis=0)
 for _ in range(2500):
  x=rng.uniform(lo[0],hi[0]);y=rng.uniform(lo[1],hi[1]);hit=tree.ray_cast(Vector((x,y,10)),Vector((0,0,-1)))[0]
  if hit is None:continue
  end=hit+Vector((rng.uniform(-.07,.07),rng.uniform(-.07,.07),rng.uniform(.09,.18)));tube([hit-Vector((0,0,.05)),end],.009,.002,sv,sf)
  for j in range(4):blade(hit.lerp(end,.25+j*.2),.075,.035,rng.uniform(0,math.tau),vs,fs)
 m=ob.data.materials[0];fol=make(ob.name+' attached sprigs',vs,fs,m,'BUILDING_ENTRY','C08','vegetation');fol['p5_role']='vegetation';added.append(fol.name)
 st=make(ob.name+' attached twigs',sv,sf,bpy.data.materials['V6 grey fissured bark'],'BUILDING_ENTRY','C08','vegetation');st['p5_role']='vegetation';added.append(st.name)
# Garage typography and neutral, nonmetallic blue/yellow paint.
font_records=[]
for o in s.objects:
 if o.type=='FONT' and o.get('feature_id') in {'WB1','WB2'}:
  o.data.space_character=1.035;o.data.extrude=.004;o.data.bevel_depth=.0007;bpy.context.view_layer.update()
  points=[o.matrix_world@Vector(p) for p in o.bound_box];width=max(p.y for p in points)-min(p.y for p in points)
  o.scale.x*=5.12/width;bpy.context.view_layer.update()
  derived_material(o,0,(.69,.47,.028),.63,0);o['text_export_required']=True
  font_records.append(dict(name=o.name,body=o.data.body,target_width=5.12,extrude=o.data.extrude))
 forsign=o.type=='MESH' and o.get('feature_id') in {'WB1','WB2'} and 'sign-board' in o.name
 if forsign:derived_material(o,0,(.020,.065,.205),.60,0);touch(o,'C09','Blue painted fascia matched to IMG_4424; full yellow text with side margins')
edits.append(dict(task='C09',editable_fonts=font_records))
# Glass response is reduced at the material, independent of camera angle.
glass_mats={}
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 for i,m in enumerate(o.data.materials):
  if m and 'glass' in m.name.lower() and o.get('feature_id')!='CONTEXT_GUANGHUA':
   if m.name not in glass_mats:
    g=m.copy();g.name='CLOSEOUT neutral '+m.name;g.diffuse_color=(.16,.23,.23,.40)
    if g.use_nodes:
     p=next((n for n in g.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
     if p:
      p.inputs['Base Color'].default_value=(.16,.23,.23,1);p.inputs['Roughness'].default_value=.20;p.inputs['Transmission Weight'].default_value=.30;p.inputs['Alpha'].default_value=.40
    g.surface_render_method='DITHERED';glass_mats[m.name]=g
   o.data.materials[i]=glass_mats[m.name];touch(o,'C13','Neutral blue-green glass; frames and photographed bases retained')
# Continuous twining stems and attached oval leaves replace spherical vine blobs.
vines=[o for o in list(s.objects) if o.type=='MESH' and o.get('feature_id')=='ERAMP' and any(k in o.name for k in ['pergola-vines','hanging-vines','extra-vines'])]
for o in vines:touch(o,'C14','Superseded by connected twining vines');bpy.data.objects.remove(o,do_unlink=True)
beam=bpy.data.objects['ERAMP__pergola-long-beam__dark-wood'];a=coords(beam);sv=[];sf=[];lv=[];lf=[]
for j in range(0,len(a),8):
 if j+8>len(a):break
 q=[beam.matrix_world@Vector(p) for p in a[j:j+8]];low=min(q,key=lambda p:p.y);high=max(q,key=lambda p:p.y)
 if (high-low).length<.3:continue
 ps=[]
 for t in np.linspace(0,1,12):
  p=low.lerp(high,float(t));p.z=3.2+.04*math.sin(t*math.tau*2+j);ps.append(p)
 tube(ps,.019,.01,sv,sf)
 for i in range(32):
  t=i/31;p=ps[0].lerp(ps[-1],t);p.z=3.2+.04*math.sin(t*math.tau*2+j)
  for k in range(3):blade(p,.17,.075,rng.uniform(0,math.tau),lv,lf)
 if j%24==0:
  p=ps[4];pts=[p,p+Vector((.05,.04,-.24)),p+Vector((-.05,.02,-.52))];tube(pts,.014,.004,sv,sf)
  for i in range(9):blade(pts[0].lerp(pts[-1],i/8),.14,.065,rng.uniform(0,math.tau),lv,lf)
for name,v,f,mat in [('C14 connected vine stems',sv,sf,bpy.data.materials['V6 grey fissured bark']),('C14 attached vine leaves',lv,lf,bpy.data.materials['GV3 olive'])]:
 ob=make(name,v,f,mat,'ERAMP','C14','vegetation');added.append(ob.name)
# The ring-seat's real inherited location, rather than the unrelated garden tree.
camera('Closeout pergola seat',(101.0,30.5,2.2),(96.5,36.8,.8),lens=32)
# Bring plaque mounting support to within 6 mm of the back, with an inferred
# stone return. It does not touch the text or front face.
root=bpy.data.objects['POET_DONKEY photo placed landmark'];plate=bpy.data.objects['POET_DONKEY inset nameplate'];text=bpy.data.objects['POET_DONKEY 驢背詩思']
inv=root.matrix_world.inverted();pp=[inv@plate.matrix_world@v.co for v in plate.data.vertices];lo=[min(p[i] for p in pp) for i in range(3)];hi=[max(p[i] for p in pp) for i in range(3)]
v=[tuple(root.matrix_world@Vector((x,y,z))) for x in [lo[0]-.035,hi[0]+.035] for y in [hi[1]+.006,hi[1]+.26] for z in [lo[2]-.025,hi[2]+.025]]
f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
back=make('C15 plaque stone mounting return',v,f,bpy.data.materials['FC_warm_granite'],'POET_DONKEY','C15','stone mounting return');added.append(back.name);assert solid(back)['nonmanifold']==0
derived_material(plate,0,(.075,.095,.09),.58,.5);touch(plate,'C15','Thin supported mounting relationship; exact historical inset depth remains unknown')
derived_material(text,0,(.38,.39,.32),.60,.35);touch(text,'C15','Four correct traditional characters with readable neutral metal face')
for o in s.objects:
 if o.type=='MESH' and o.get('feature_id')=='POET_DONKEY' and any(k in o.name for k in ['cloak','robe','donkey','body','head','arm','leg']) and o.data.materials:
  derived_material(o,0,(.105,.145,.12),.57,.55);touch(o,'C15','Moderate patinated metal response; unphotographed anatomy remains generalized')
# Roof glass, leaf transmission and original packed texture resources are retained.
s.view_settings.view_transform='AgX';s.view_settings.exposure=.65
s['active_checkpoint']='Closeout native candidate: structure, foliage and details; final acceptance pending'
s['uncertainty_register']='Absolute scale, terrain levels, hidden construction, species/count/position of inferred trees and ESKY_N site position remain inferred or unknown'
bpy.context.view_layer.update();after=snapshot()
drift=[n for n,h in before.items() if n not in changed and after.get(n)!=h];assert not drift,drift
fonts=[o for o in s.objects if o.type=='FONT'];assert len(fonts)==3
assert sorted(o.data.body for o in fonts)==sorted(['FUDAN','光华楼广场自行车库','光华楼广场自行车库'])
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
write(O/'finish-validation.json',dict(source_sha256=sha(SOURCE),checkpoint_sha256=sha(TARGET),changed=sorted(changed),added=added,
 protected_unchanged=len(before)-len(changed),edits=edits,fonts_editable=True,visual_status='pending diagnostic2',seed=10010608))
write(O/'final-snapshot.json',after)
bpy.ops.wm.open_mainfile(filepath=str(TARGET));assert snapshot()==after
print('NATIVE_FINISH_REOPENED',len(changed),len(added),leaf_fans,flush=True)
