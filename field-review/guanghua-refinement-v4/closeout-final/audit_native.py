"""Read-only final-source audit, including actual ray intersections at interfaces."""
import bpy,sys,math,json,re
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read,solid
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,snapshot,write,plain
T=O/'guanghua-closeout-final.blend';BASE=O.parent/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'
source_hash=sha(T);bpy.ops.wm.open_mainfile(filepath=str(T));s=bpy.context.scene
assert snapshot()==read(O/'final-snapshot.json')
assert sha(BASE)=='641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2'
def tree(objects):
 v=[];f=[]
 for o in objects:
  k=len(v);v.extend(o.matrix_world@q.co for q in o.data.vertices);f.extend(tuple(k+i for i in p.vertices) for p in o.data.polygons)
 return BVHTree.FromPolygons(v,f)
def z(t,x,y):
 q=t.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),80)[0]
 return q.z if q else None
walk=[o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='E_WALK'];assert len(walk)==200
walk_solids=[solid(o) for o in walk];assert not [a for a in walk_solids if a['nonmanifold'] or a['zero_area'] or a['volume']<=0]
plaza=bpy.data.objects['FORECOURT photo grid plaza'];w=tree(walk);p=tree([plaza]);junction=[]
for i in range(241):
 x=63.50211715698242+.00005+(3.6-.0001)*i/240;a=z(w,x,77.85448455810547-.0001);b=z(p,x,77.85448455810547+.0001)
 assert a is not None and b is not None,(i,a,b)
 assert b-.00261<=a<=b+.00011,(i,a,b)
 junction.append(dict(x=x,path_z=a,plaza_z=b))
road=tree([bpy.data.objects['C04 continuous road']]);ground=tree([bpy.data.objects['C04 continuous ground']]);edges=[]
for row in read(O/'road-pack.json')['shared_edge_samples']:
 x,y=row['x'],row['y'];a=[];b=[]
 for k in range(32):
  xx=x+.00025*math.cos(k*math.tau/32);yy=y+.00025*math.sin(k*math.tau/32)
  aa=z(road,xx,yy);bb=z(ground,xx,yy)
  if aa is not None:a.append(aa)
  if bb is not None:b.append(bb)
 boundary_type='road / planting ground'
 if a and not b and abs(x-67.10211756)<.001:
  bb=z(w,x-.0003,y)
  if bb is not None:b=[bb];boundary_type='west exterior / protected straight corridor'
 assert a and b,('Uncovered actual boundary',row)
 delta=min(abs(aa-bb) for aa in a for bb in b)
 edges.append(dict(x=x,y=y,boundary_type=boundary_type,minimum_actual_height_difference=delta,road_height_range=[min(a),max(a)],ground_height_range=[min(b),max(b)]))
checks=[solid(o) for o in s.objects if o.type=='MESH' and o.get('closeout_task') in {'C02','C03','C04','C15'} and o.get('closeout_role') not in {'vegetation'} and o.name not in {'POET_DONKEY 驢背詩思','POET_DONKEY inset nameplate'} and o.name.startswith(('C02 ','C03 ','C04 ','C15 '))]
assert max(a['minimum_actual_height_difference'] for a in edges)<1e-4
assert not [a for a in checks if a['nonmanifold'] or a['zero_area'] or a['volume']<=0 or not a['finite']]
fonts=[]
for o in s.objects:
 if o.type!='FONT':continue
 q=[o.matrix_world@Vector(p) for p in o.bound_box];bounds=[[min(p[i] for p in q) for i in range(3)],[max(p[i] for p in q) for i in range(3)]]
 assert o.data.body and o.data.font
 if o.get('feature_id') in {'WB1','WB2'}:assert abs(bounds[1][1]-bounds[0][1]-5.12)<1e-4
 fonts.append(dict(name=o.name,body=o.data.body,bounds=bounds,font=o.data.font.name,packed=bool(o.data.font.packed_file)))
assert sorted(r['body'] for r in fonts)==sorted(['FUDAN','光华楼广场自行车库','光华楼广场自行车库'])
components={}
for fid in ['WB1','WB2','WOPEN','WOPEN_S','EOPEN','EOPEN_S','ESKY','ESKY_N','WSKY1','WSKY2','WTERR','ETERR','ERAMP','E_FURNITURE','SIGN','POET_DONKEY']:
 components[fid]=[o.name for o in s.objects if o.get('feature_id')==fid and o.type in {'MESH','FONT'} and not o.hide_render]
 if fid!='ESKY_N':assert components[fid],fid
groups={}
for o in s.objects:
 if o.type=='MESH' and o.name.startswith('GV3 shrub '):groups.setdefault(o.name.split(' GV3')[0],[]).append(o)
shrubs=[]
for key,obs in groups.items():
 loc=obs[0].location;hit=z(road,loc.x,loc.y);g=z(ground,loc.x,loc.y)
 shrubs.append(dict(group=key,location=list(loc),road_z=hit,ground_z=g,objects=[o.name for o in obs]))
tri=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in s.objects if o.type=='MESH' and not o.hide_render)
current=snapshot();before=read(O/'baseline-snapshot.json');diff=dict(removed=sorted(set(before)-set(current)),added=sorted(set(current)-set(before)),changed=sorted(n for n in set(before)&set(current) if before[n]!=current[n]),unchanged=sorted(n for n in set(before)&set(current) if before[n]==current[n]))
report=dict(source_sha256=source_hash,baseline_unchanged=True,reopened_snapshot_equal=True,meshes=sum(o.type=='MESH' for o in s.objects),visible_native_triangles=tri,closed_repaired_solids=checks,straight_path_entities=200,plaza_interface_samples=241,max_plaza_recess=max(abs(a['path_z']-a['plaza_z']) for a in junction),road_boundary_samples=241,max_actual_road_ground_difference=max(a['minimum_actual_height_difference'] for a in edges),fonts=fonts,component_inventory=components,shrubs=shrubs,diff=diff,limits=['Absolute scale and levels inferred','ESKY_N geographic placement remains unknown','No certification of hidden structures or global solid collision freedom'])
write(O/'native-validation.json',report);write(O/'native-junction-probes.json',junction);write(O/'native-road-edge-probes.json',edges)
assert sha(T)==source_hash
print('NATIVE_AUDIT',report['meshes'],tri,report['max_actual_road_ground_difference'],len(groups),flush=True)
