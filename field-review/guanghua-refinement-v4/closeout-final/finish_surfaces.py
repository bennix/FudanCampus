import bpy,bmesh,sys,json,math,random
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read,make,metric_uv,solid
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,snapshot,write
T=O/'guanghua-closeout-final.blend';bpy.ops.wm.open_mainfile(filepath=str(T));s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
before=snapshot();changed=set();added=[];report={};rng=random.Random(10010212)
# Replace only the identified square front-column components, retaining every
# surrounding cornice, window axis and stone edge in its original world position.
o=bpy.data.objects['光华楼 · Guanghua light stone edges'];bm=bmesh.new();bm.from_mesh(o.data);unseen=set(bm.verts);remove=set();columns=[]
while unseen:
 todo=[unseen.pop()];comp=set(todo)
 while todo:
  v=todo.pop()
  for e in v.link_edges:
   q=e.other_vert(v)
   if q in unseen:unseen.remove(q);comp.add(q);todo.append(q)
 ps=[o.matrix_world@v.co for v in comp];lo=np.min(np.asarray(ps),axis=0);hi=np.max(np.asarray(ps),axis=0);c=(lo+hi)/2;dim=hi-lo
 front=(abs(c[1]-125.4)<.003 and abs(c[2]-6)<.003 and abs(dim[2]-8.7)<.003)
 upper=(abs(c[1]-134.325)<.003 and abs(c[2]-16.8)<.003 and abs(dim[2]-10.95)<.003)
 if front or upper:columns.append((list(c),list(dim),front));remove.update(comp)
assert len(columns)==45,('Unexpected identified front columns',len(columns))
keep=sorted(tuple(v.co) for v in bm.verts if v not in remove)
bmesh.ops.delete(bm,geom=list(remove),context='VERTS');bm.to_mesh(o.data);bm.free();assert sorted(tuple(v.co) for v in o.data.vertices)==keep
changed.add(o.name);o['closeout_task']='C02';v=[];f=[]
for c,dim,front in columns:
 radius=dim[0]*.47;bottom=c[2]-dim[2]/2;top=c[2]+dim[2]/2
 levels=[(bottom,radius*1.2),(bottom+.18,radius*1.2),(bottom+.25,radius),(top-.38,radius*.94),(top-.28,radius*1.05),(top-.12,radius*1.22),(top,radius*1.22)]
 start=len(v);n=48
 for z,r in levels:
  for k in range(n):
   a=k*math.tau/n;rr=r*(1-.05*(.5+.5*math.cos(k*math.pi))) if bottom+.24<z<top-.3 else r
   v.append((c[0]+rr*math.cos(a),c[1]+rr*math.sin(a),z))
 f.extend([tuple(start+k for k in reversed(range(n))),tuple(start+(len(levels)-1)*n+k for k in range(n))])
 for j in range(len(levels)-1):
  for k in range(n):a=start+j*n+k;b=start+j*n+(k+1)%n;f.append((a,b,b+n,a+n))
col=make('C02 visible fluted facade columns',v,f,o.data.materials[0],'CONTEXT_GUANGHUA','C02','front facade columns');col['source_photos']=[4464,4485];col['capitals_detail']='Visible ring/capital mass confirmed; ornamental carving generalized';added.append(col.name)
assert solid(col)['nonmanifold']==0
report['C02']=dict(replaced_square_columns=len(columns),retained_noncolumn_vertices=len(keep),axes_and_openings_preserved=True,dimension_status='Inherited relative scale; no surveyed claim')
# Add restrained fine mineral relief to the newly rebuilt stone and road, while
# preserving existing calibrated picture textures and the 200-piece corridor.
for o in s.objects:
 if o.type!='MESH' or o.get('closeout_task') not in {'C03','C04'} or o.get('closeout_role')=='vegetation':continue
 if o.get('closeout_role') in {'soil','ground'}:continue
 for i,old in enumerate(list(o.data.materials)):
  if old is None:continue
  mat=old.copy();mat.name='C11 '+old.name;o.data.materials[i]=mat
  if mat.use_nodes:
   nt=mat.node_tree;p=next((n for n in nt.nodes if n.type=='BSDF_PRINCIPLED'),None)
   if p and not p.inputs['Normal'].is_linked:
    tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=70;tex.inputs['Detail'].default_value=2
    coord=nt.nodes.new('ShaderNodeTexCoord');nt.links.new(coord.outputs['Object'],tex.inputs['Vector'])
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.16;bump.inputs['Distance'].default_value=.009
    nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal']);p.inputs['Roughness'].default_value=.78
  changed.add(o.name);o['closeout_surface_task']='C11';metric_uv(o)
report['C11']=dict(metric_uv='Scene-unit mapping on repaired solids; original calibrated surfaces retained',relief_distance=.009,material_graph='Native procedural microrelief; export conversion recorded separately')
# Soil and a small amount of litter are bounded to visible trunk bases and must
# hit planting ground while avoiding every road/paving surface.
def bvh(objects):
 vv=[];ff=[]
 for o in objects:
  o.data.calc_loop_triangles()
  for t in o.data.loop_triangles:
   q=[o.matrix_world@o.data.vertices[i].co for i in t.vertices]
   if (q[1]-q[0]).cross(q[2]-q[0]).z<1e-7:continue
   k=len(vv);vv.extend(q);ff.append((k,k+1,k+2))
 return BVHTree.FromPolygons(vv,ff,all_triangles=True)
ground=bvh([o for o in s.objects if o.type=='MESH' and not o.hide_render and (o.get('feature_id')=='GROUND' or o.name=='C04 continuous ground')])
hard=bvh([o for o in s.objects if o.type=='MESH' and not o.hide_render and o.get('feature_id') in {'EPATH','E_WALK','WPATH','EDGE_PATHS','FORECOURT','WTERR','ETERR'} and not any(k in o.name.lower() for k in ['hedge','leaf','ground'])])
v=[];f=[];lv=[];lf=[];roots=[]
for o in [o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='TREE_CANOPY_V6' and 'wood' in o.name]:
 x,y=o.location.x,o.location.y
 # The central lawn stays clear; root transitions are restricted to planting strips.
 if not (-83<x<-29 or 67<x<105 or -2<y<4):continue
 points=[]
 for k in range(14):
  a=k*math.tau/14;r=.36+rng.uniform(-.05,.07);xx=x+r*math.cos(a);yy=y+r*math.sin(a)
  q=ground.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0];h=hard.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0]
  if q is None or h is not None and h.z>=q.z-.025:points=[];break
  points.append((xx,yy,q.z+.001))
 if not points:continue
 c=ground.ray_cast(Vector((x,y,30)),Vector((0,0,-1)))[0]
 if c is None:continue
 start=len(v);v.append((x,y,c.z+.001));v.extend(points)
 for k in range(14):f.append((start,start+1+k,start+1+(k+1)%14))
 roots.append(dict(tree=o.get('tree_group'),position=[x,y,c.z],soil_radius=.36))
 for _ in range(7):
  a=rng.uniform(0,math.tau);r=rng.uniform(.25,.8);xx=x+r*math.cos(a);yy=y+r*math.sin(a)
  q=ground.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0];h=hard.ray_cast(Vector((xx,yy,30)),Vector((0,0,-1)))[0]
  if q is None or h is not None and h.z>=q.z-.025:continue
  k=len(lv);length=rng.uniform(.045,.07);width=length*.4;zz=q.z+.0016
  lv.extend([(xx-length,yy,zz),(xx,yy-width,zz),(xx+length,yy,zz+.003),(xx,yy+width,zz)]);lf.extend([(k,k+1,k+2),(k,k+2,k+3)])
for name,vs,fs,color in [('C12 bounded bare trunk soil',v,f,(.12,.095,.052)),('C12 sparse ground litter',lv,lf,(.21,.15,.065))]:
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True;p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.93
 ob=make(name,vs,fs,mat,'GROUND','C12','ground detail');ob['evidence_status']='Sparse visible-ground appearance confirmed; exact distribution inferred';added.append(ob.name)
report['C12']=dict(root_patches=roots,litter_blades=len(lf)//2,roads_excluded=True,underground_roots='unknown; not modeled')
after=snapshot();assert all(after.get(n)==h for n,h in before.items() if n not in changed)
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'surface-validation.json',dict(changed=sorted(changed),added=added,tasks=report,source_sha256=sha(T),visual_status='pending diagnostic2'))
write(O/'final-snapshot.json',after);bpy.ops.wm.open_mainfile(filepath=str(T));assert snapshot()==after
print('SURFACE_AND_FACADE_REOPENED',len(columns),len(roots),flush=True)
