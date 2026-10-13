import bpy,sys
import numpy as np
from pathlib import Path
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import snapshot,sha,write
T=O/'guanghua-closeout-final.blend';BASE=O.parent/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'
bpy.ops.wm.open_mainfile(filepath=str(T));bpy.context.preferences.filepaths.save_version=0
targets={o.name:o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id')=='GARDEN_VEGETATION_V3' and o.get('closeout_task')=='C08'}
names=list(targets)
with bpy.data.libraries.load(str(BASE),link=False) as (available,loaded):loaded.objects=names[:]
cache={};counts=[]
for name,original in zip(names,loaded.objects):
 key=original.data.as_pointer()
 if key not in cache:
  me=original.data.copy();me.name='C08 once '+original.data.name
  a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
  bases=[]
  for p in me.polygons:
   if len(p.vertices)!=3:continue
   b,j,c=p.vertices
   if j!=b+1 or c!=b+8 or p.index+7>=len(me.polygons):continue
   rows=list(me.polygons[p.index:p.index+8])
   if all(len(r.vertices)==3 and r.vertices[0]==b+i and r.vertices[2]==c for i,r in enumerate(rows)):bases.append(b)
  ix=np.asarray(bases)[:,None]+np.arange(9);q=a[ix].copy();base=q[:,0].copy();u=(q[:,4]-q[:,0])*.5;w=(q[:,6]-q[:,2])*.5
  q[:,4]=base+u*1.62
  for j,t,sign,width in [(1,.26,-1,.73),(2,.81,-1,1.05),(3,1.36,-1,.73),(5,1.36,1,.73),(6,.81,1,1.05),(7,.26,1,.73)]:q[:,j]=base+u*t+w*sign*width
  q[:,8]=base+u*.81+np.array([0,0,.007]);a[ix]=q;me.vertices.foreach_set('co',a.ravel());me.update()
  cache[key]=me;counts.append(dict(mesh=me.name,leaf_fans=len(bases),instances=0))
 targets[name].data=cache[key];targets[name]['closeout_note']='Recovered v7 shared prototype; rounded/shortened exactly once; all inherited per-instance transforms retained'
for original in loaded.objects:bpy.data.objects.remove(original,do_unlink=True)
for row in counts:row['instances']=sum(o.data.name==row['mesh'] for o in targets.values())
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'shared-foliage-repair.json',dict(source_sha256=sha(T),v7_sha256=sha(BASE),affected_instances=len(targets),unique_meshes=len(cache),prototypes=counts))
write(O/'final-snapshot.json',snapshot());print('SHARED_FOLIAGE_REPAIRED',len(targets),len(cache),flush=True)
