"""Independent read-only visible-scene audit; does not save or modify native assets."""
import bpy,json,sys,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent
T=O/'guanghua-closeout-final.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
initial=sha(T);bpy.ops.wm.open_mainfile(filepath=str(T));s=bpy.context.scene
def bounds(o):
 p=[o.matrix_world@Vector(q) for q in o.bound_box]
 return [[min(q[k] for q in p) for k in range(3)],[max(q[k] for q in p) for k in range(3)]]
def material(m):
 r=dict(name=m.name,diffuse=list(getattr(m,'diffuse_color',getattr(m,'color',[]))),use_nodes=m.use_nodes)
 if m.use_nodes:
  r['nodes']=[dict(type=n.bl_idname,name=n.name,inputs={p.name:list(p.default_value) if hasattr(p.default_value,'__len__') else p.default_value for p in n.inputs if hasattr(p,'default_value') and not p.is_linked and isinstance(p.default_value,(int,float,tuple,list,Vector))}) for n in m.node_tree.nodes if n.type in {'BSDF_PRINCIPLED','BACKGROUND','BSDF_TRANSLUCENT','MIX_SHADER'}]
 return r
hidden=[]
for o in s.objects:
 if o.type!='MESH' or o.hide_render:continue
 n=o.name.lower()
 if o.get('feature_id') in {'GARDEN_VEGETATION_V3','TREE_CANOPY_V6','VEGETATION','VEGETATION_V2'} or o.get('closeout_role')=='vegetation' or any(w in n for w in ['planting','leaves','red flowers','planted-shrubs','hedge']):
  hidden.append(o.name);o.hide_render=True
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def cast(origin,direction,dist=2500):
 pos=Vector(origin);direction=Vector(direction).normalized();travel=0
 for i in range(400):
  ok,loc,normal,face,obj,matrix=s.ray_cast(dg,pos,direction,distance=dist-travel)
  if not ok:return None
  step=(loc-pos).length
  if not obj.hide_render:
   mats=obj.data.materials if obj.type=='MESH' else []
   mi=obj.data.polygons[face].material_index if obj.type=='MESH' and 0<=face<len(obj.data.polygons) else 0
   return dict(object=obj.name,feature_id=obj.get('feature_id'),location=list(loc),normal=list(normal),face=face,material=mats[mi].name if mats and mi<len(mats) and mats[mi] else None,distance=travel+step)
  travel+=step+.00001;pos=loc+direction*.00001
 return dict(error='ray iteration limit')
lights=[o for o in s.objects if o.type=='LIGHT' and not o.hide_render]
report=dict(source_sha256=initial,read_only=True,lights=[dict(name=o.name,type=o.data.type,energy=o.data.energy,color=list(o.data.color),position=list(o.location),toward_light=list((o.matrix_world.to_3x3()@Vector((0,0,1))).normalized())) for o in lights],world=dict(name=s.world.name,color=list(s.world.color),materials=material(s.world) if s.world else None),opening_image_probes={},components={})
for fid,pixels in [('EOPEN',[(.85,.40),(.9,.65),(.65,.15),(.22,.83),(.5,.49)]),('EOPEN_S',[(.86,.43),(.94,.69),(.70,.69),(.23,.8),(.51,.53)])]:
 ob=bpy.data.objects[fid+'__tread__FIN_granite'];bb=bounds(ob);center=Vector(tuple((bb[0][k]+bb[1][k])/2 for k in range(3)))
 loc=center+Vector((-4.4,6.7,4.6));target=center+Vector((0,0,.5));rot=(target-loc).to_track_quat('-Z','Y').to_matrix()
 rows=[]
 for u,v in pixels:
  direction=rot@Vector(((u-.5)*36/36,(.5-v)*27/36,-1));hit=cast(loc,direction);shadow=[]
  if hit and 'location' in hit:
   point=Vector(hit['location']);normal=Vector(hit['normal'])
   for light in lights:
    if light.data.type=='SUN':to_light=light.matrix_world.to_3x3()@Vector((0,0,1));distance=2500
    else:to_light=light.location-point;distance=to_light.length
    obstruction=cast(point+normal*.00005,to_light,distance-.0001)
    shadow.append(dict(light=light.name,obstruction=obstruction))
  rows.append(dict(pixel_normalized=[u,v],first_visible_surface=hit,shadow_rays=shadow))
 report['opening_image_probes'][fid]=dict(camera_location=list(loc),target=list(target),lens=36,aspect=4/3,hidden_render_objects=len(hidden),probes=rows)
for fid in ['WB1','WB2','WOPEN','WOPEN_S','EOPEN','EOPEN_S','ESKY','WSKY1','WSKY2','ERAMP','E_FURNITURE','POET_DONKEY','SIGN']:
 report['components'][fid]=[dict(name=o.name,type=o.type,bounds=bounds(o),hidden_render=o.hide_render,materials=[m.name for m in o.data.materials if m],body=o.data.body if o.type=='FONT' else None,properties={k:o[k] for k in o.keys() if k in {'closeout_task','source_photos','geometry_confidence','feature_id'}}) for o in s.objects if o.type in {'MESH','FONT'} and o.get('feature_id')==fid]
report['component_materials']={m.name:material(m) for fid in ['WB1','WB2','WOPEN','WOPEN_S','EOPEN','EOPEN_S','ESKY','WSKY1','WSKY2','ERAMP','E_FURNITURE','POET_DONKEY','SIGN'] for o in s.objects if o.type in {'MESH','FONT'} and o.get('feature_id')==fid for m in o.data.materials if m}
terrain_names=['GROUND__terrain__FIN_garden_grass','C04 continuous ground','C04 continuous road']
trees={n:BVHTree.FromPolygons([bpy.data.objects[n].matrix_world@v.co for v in bpy.data.objects[n].data.vertices],[tuple(p.vertices) for p in bpy.data.objects[n].data.polygons]) for n in terrain_names}
report['duplicate_ground_probes']=[]
for x,y in [(70.060989,69.007263),(68.789238,72.228401),(75.452064,62.393818),(69.046074,45.937206),(67.650955,48.023235),(69.043930,50.209206),(74,67),(82,65),(85,38),(88,48)]:
 row=dict(x=x,y=y,surfaces={})
 for n,t in trees.items():
  p,norm,f,d=t.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),80)
  row['surfaces'][n]=dict(z=p.z,normal=list(norm),face=f) if p else None
 original=row['surfaces'][terrain_names[0]];new=row['surfaces'][terrain_names[1]]
 row['ground_surface_difference']=abs(original['z']-new['z']) if original and new else None
 report['duplicate_ground_probes'].append(row)
assert sha(T)==initial
(O/'independent-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=lambda v:list(v) if hasattr(v,'__len__') else str(v)),encoding='utf-8')
print('INDEPENDENT_READ_ONLY_COMPLETE',initial,flush=True)
