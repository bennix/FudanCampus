"""Repair diagnosed crown density and shrub-road contact on the unified candidate."""
import bpy,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import snapshot,sha,write
T=O/'guanghua-closeout-final.blend';bpy.ops.wm.open_mainfile(filepath=str(T));bpy.context.preferences.filepaths.save_version=0;s=bpy.context.scene
assert not s.get('closeout_canopy_contact_refined'),'Run the preceding native stages before rebuilding this stage'
before=snapshot();changed=set();cache={}
def coords(me):
 a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
for o in s.objects:
 if o.type!='MESH':continue
 if o.get('feature_id')=='TREE_CANOPY_V6' and ('leaves' in o.name or 'needles' in o.name):
  a=coords(o.data);q=a.reshape(-1,4,3);center=q.mean(axis=1,keepdims=True);q[:]=center+(q-center)*(1.18 if 'leaves' in o.name else 1.08)
  o.data.vertices.foreach_set('co',a.ravel());o.data.update();changed.add(o.name);o['closeout_leaf_density_adjustment']='Crown blade area increased without adding isolated leaf clouds; crown outline and v6 twig centers retained'
 if o.name.startswith('GV3 shrub '):
  key=o.data.as_pointer()
  if key not in cache:
   me=o.data.copy();cache[key]=me;a=coords(me);z=np.maximum(a[:,2],0)
   a[:,0]+=.035*z*np.sin(a[:,1]*2.5+a[:,2]*1.8);a[:,1]+=.025*z*np.sin(a[:,0]*2.1);a[:,2]*=.92
   me.vertices.foreach_set('co',a.ravel());me.update()
  o.data=cache[key]
  changed.add(o.name);o['closeout_shrub_shape']='Shared asymmetric flattened clump warp applied once to both foliage and twigs; inferred distribution retained'
def bvh(obs):
 v=[];f=[]
 for o in obs:
  k=len(v);v.extend(o.matrix_world@q.co for q in o.data.vertices);f.extend(tuple(k+i for i in p.vertices) for p in o.data.polygons)
 return BVHTree.FromPolygons(v,f)
ground=bvh([o for o in s.objects if o.type=='MESH' and not o.hide_render and (o.get('feature_id')=='GROUND' or o.name=='C04 continuous ground')])
road=bvh([bpy.data.objects['C04 continuous road']])
def hit(t,x,y):return t.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),80)[0]
groups={}
for o in s.objects:
 if o.type=='MESH' and o.name.startswith('GV3 shrub '):groups.setdefault(o.name.split(' GV3')[0],[]).append(o)
moves=[]
for key,obs in groups.items():
 loc=obs[0].location.copy();x,y=loc.x,loc.y
 if not (67.1<x<91.3 and 35<y<77.3):continue
 g=hit(ground,x,y);r=hit(road,x,y);new=loc.copy();factor=1.
 if r:
  # Seek a planting disk rather than merely an unoccupied center point.
  candidate=None
  for radius in [.45,.65,.9]:
   for dist in [.8,1.3,1.8,2.4,3.,3.8,4.6]:
    for k in range(24):
     xx=x+dist*math.cos(k*math.tau/24);yy=y+dist*math.sin(k*math.tau/24)
     if not (67.6<xx<90.8 and 35.5<yy<73.1):continue
     gg=hit(ground,xx,yy)
     if not gg:continue
     if any(hit(road,xx+radius*math.cos(j*math.tau/12),yy+radius*math.sin(j*math.tau/12)) for j in range(12)):continue
     candidate=(xx,yy,gg.z+.003);break
    if candidate:break
   if candidate:break
  assert candidate,('No bounded shrub planting disk',key)
  new=Vector(candidate);factor=.60
 elif g:new.z=g.z+.003
 for o in obs:
  o.location=new
  if factor!=1:o.scale.x*=factor;o.scale.y*=factor
  changed.add(o.name);o['closeout_planting_contact']='Projected onto actual new terrain; root collision moved within the inferred east planting mask'
 moves.append(dict(group=key,before=list(loc),after=list(new),road_collision_repaired=bool(r),horizontal_scale=factor))
assert all(hit(road,o.location.x,o.location.y) is None for o in s.objects if o.name.startswith('GV3 shrub ') and o.type=='MESH' and 67.1<o.location.x<91.3 and 35<o.location.y<77.3)
flowers=[]
for o in s.objects:
 if o.type=='MESH' and o.name.startswith('BENTRY ') and o.name.endswith('red flowers'):
  o.data=o.data.copy()
  for i,m in enumerate(o.data.materials):
   mm=m.copy();mm.name='C14 visible red blossom';mm.diffuse_color=(.31,.025,.04,1)
   if mm.use_nodes:
    p=next((n for n in mm.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if p:
     for link in list(p.inputs['Base Color'].links):mm.node_tree.links.remove(link)
     p.inputs['Base Color'].default_value=mm.diffuse_color;p.inputs['Roughness'].default_value=.7
   o.data.materials[i]=mm
  changed.add(o.name);flowers.append(o.name)
s['closeout_canopy_contact_refined']=True;bpy.context.view_layer.update();after=snapshot();drift=[n for n,v in before.items() if n not in changed and after.get(n)!=v];assert not drift,drift
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'canopy-contact-validation.json',dict(source_sha256=sha(T),changed=sorted(changed),shared_shrub_meshes_edited_once=len(cache),root_reprojections=moves,blossom_color_changes=flowers,confidence='Photo-supported crown fullness and asymmetric clumps; precise tree/shrub positions and terrain levels inferred'))
write(O/'final-snapshot.json',after);bpy.ops.wm.open_mainfile(filepath=str(T));assert snapshot()==after
print('CANOPY_CONTACT_REOPENED',len(changed),sum(m['road_collision_repaired'] for m in moves),flush=True)
