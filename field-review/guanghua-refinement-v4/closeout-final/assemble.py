"""Sequential closeout assembly. Accepted source files are read only."""
import bpy,bmesh,json,sys,math
from pathlib import Path
from mathutils import Vector
import numpy as np
O=Path(__file__).resolve().parent;R=O.parent
sys.path.insert(0,str(R/'scene-unified-v5'))
from scene_fingerprints import sha,snapshot,write,plain
BASE=R/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'
BASE_SHA='641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2'
STRUCT=O/'guanghua-closeout-structure.blend'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def collection(name):
 c=bpy.data.collections.get(name)
 if not c:c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
 return c
def metric_uv(o):
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='Closeout metre UV')
 for p in o.data.polygons:
  k=max(range(3),key=lambda k:abs(p.normal[k]));axes=(1,2) if k==0 else (0,2) if k==1 else (0,1)
  for li in p.loop_indices:
   q=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(q[axes[0]],q[axes[1]])
def make(name,vertices,faces,mat,fid,task,role):
 me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
 bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-6)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 ob=bpy.data.objects.new(name,me);collection('14_Closeout '+task).objects.link(ob);me.materials.append(mat)
 ob['feature_id']=fid;ob['closeout_task']=task;ob['closeout_role']=role
 ob['geometry_confidence']='Visible relationship confirmed; dimension and local elevation inferred'
 ob['source_photos']=[4464,4480,4485] if task=='C03' else [4568,4567,4572,4574]
 metric_uv(ob);return ob
def solid(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 r=dict(name=o.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),zero_area=sum(f.calc_area()<1e-9 for f in bm.faces),
        volume=bm.calc_volume(signed=True),finite=all(math.isfinite(v) for q in bm.verts for v in q.co),faces=len(bm.faces))
 bm.free();return r
def camera(name,loc,target,lens=32,scale=None):
 c=bpy.data.objects.get(name)
 if not c:
  d=bpy.data.cameras.new(name);c=bpy.data.objects.new(name,d);collection('14_Closeout cameras').objects.link(c)
 c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
 c.data.lens=lens;c.data.clip_end=2500
 if scale:c.data.type='ORTHO';c.data.ortho_scale=scale
 c['camera_confidence']='Manual evidence view; absolute pose inferred'
 return c
def structures():
 assert sha(BASE)==BASE_SHA
 bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
 before=read(O/'baseline-snapshot.json');pack=read(O/'planter-pack.json');road=read(O/'road-pack.json')
 stems=['curved planter wall','curved coping','curved planter soil','burgundy planting','clipped green planting','outer retaining wall','outer coping']
 removed=[o.name for o in s.objects if o.name.startswith('BENTRY ') and any(k in o.name for k in stems)]
 removed += [o.name for o in s.objects if o.type in {'MESH','CURVE'} and o.get('feature_id')=='EPATH']
 relocated=[o.name for o in s.objects if o.name.startswith('BENTRY ') and any(' '+k+' ' in o.name for k in ['inner','outer']) and any(o.name.endswith(k) for k in ['urn','broad leaves','red flowers','soil'])]
 whitelist=set(removed+relocated)
 write(O/'edit-contract.json',dict(source_sha256=BASE_SHA,removed=removed,changed=relocated,
  tasks={'C03':dict(primary={'west':4464,'east':4485},target='Independent low front curves, stepped stair returns, smooth ramp returns and separable bases',invariants='Stair axes, ramp surfaces, lawn and plaza extents',confidence='Confirmed visible relationship; dimensions inferred'),
  'C04':dict(primary=4568,target='Forward travel before turning; connected road surface with shared terrain edge height',invariants='Flat road outside declared patch, terrace, skylights and openings',confidence=road['confidence'])}))
 for n in removed:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
 mats={'stone':bpy.data.materials['FC_warm_granite'],'cap':bpy.data.materials['FC_warm_granite'],'soil':bpy.data.materials['FIN_garden_grass'],
 'red':bpy.data.materials['P5 layered red shrub foliage'],'green':bpy.data.materials['P5 layered green shrub foliage']}
 mats['yellow']=mats['green']
 new=[]
 for row in pack['objects']:
  ob=make(row['name'].replace('P5 ','C03 '),row['vertices'],row['faces'],mats[row['material']],'BUILDING_ENTRY','C03',row['role'])
  ob['closeout_side']=row['side'];ob['p5_role']=row['role'];new.append(ob)
 oldcenter={'west':{'inner':(-47.25,100),'outer':(-52.75,100)},'east':{'inner':(87.25,100),'outer':(92.75,100)}}
 moves=[]
 for side in ['west','east']:
  for kind in ['inner','outer']:
   target=pack['plans'][side]['spec'][kind];src=oldcenter[side][kind];delta=Vector((target[0]-src[0],target[1]-src[1],0))
   for suffix in ['urn','broad leaves','red flowers','soil']:
    o=bpy.data.objects['BENTRY '+side+' '+kind+' '+suffix];o.data=o.data.copy()
    for v in o.data.vertices:v.co+=o.matrix_world.inverted().to_3x3()@delta
    o.data.update();o['closeout_task']='C03';moves.append(dict(object=o.name,delta=list(delta)))
 for name,mat in [('road','V4 clean irregular garden stone'),('ground','FIN_garden_grass')]:
  row=road[name];ob=make('C04 continuous '+name,row['vertices'],row['faces'],bpy.data.materials[mat],'EPATH','C04',name);new.append(ob)
  ob['terrain_boundary']='Road and ground share height function and complementary polygon domains'
 checks=[solid(o) for o in new]
 write(O/'structure-mesh-checks.json',checks)
 bad=[r for r in checks if r['nonmanifold'] or r['zero_area'] or r['volume']<=0 or not r['finite']]
 assert not bad,bad
 after=snapshot();protected={n:h for n,h in before.items() if n not in whitelist}
 drift=[n for n,h in protected.items() if after.get(n)!=h];assert not drift,drift
 assert sum(o.type=='FONT' for o in s.objects)==3
 camera('Closeout overhead',(10,58,280),(10,58,0),scale=280)
 camera('Closeout east road overhead',(82,54,100),(82,54,0),scale=82)
 camera('Closeout east road side',(103,29,13),(79,48,1.2),scale=44)
 camera('Closeout west garage',(-85.0,48,2.3),(-74.5,48,.7),lens=32)
 camera('Closeout east garage',(-85.0,70,2.3),(-74.5,70,.7),lens=32)
 s['active_checkpoint']='Closeout structure C03/C04; visual diagnosis pending'
 bpy.ops.wm.save_as_mainfile(filepath=str(STRUCT))
 report=dict(source_sha256=BASE_SHA,checkpoint=str(STRUCT),checkpoint_sha256=sha(STRUCT),
 protected_unchanged=len(protected),whitelist=sorted(whitelist),added=[o.name for o in new],relocations=moves,
 planter_clearance=pack['checks'],road_components=road['road_components'],road_ground_overlap=road['overlap_area'],
 shared_edge_samples=road['shared_edge_samples'],shared_edge_max_height_difference=road['shared_edge_max_height_difference'],
 solids=checks,visual_status='pending diagnostic inspection',absolute_scale='inferred')
 write(O/'structure-validation.json',report);write(O/'structure-snapshot.json',after)
 # A real reopen checks packed resources, mesh state, and text persistence.
 bpy.ops.wm.open_mainfile(filepath=str(STRUCT));assert snapshot()==after
 report['checkpoint_reopens']=True;assert sha(BASE)==BASE_SHA
 report['baseline_unchanged']=True;write(O/'structure-validation.json',report)
 print('STRUCTURE_REOPENED',len(new),len(protected),flush=True)
if __name__=='__main__':structures()
