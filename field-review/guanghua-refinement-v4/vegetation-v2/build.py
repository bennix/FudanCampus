import bpy,math,random,json,hashlib,ast,time,numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from export_visible_glb import export_visible_glb
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path.cwd();O=R/'field-review/guanghua-refinement-v4/vegetation-v2';BASE=O.parent/'vegetation-v1/vegetation-v1.blend'
bpy.ops.wm.open_mainfile(filepath=str(BASE));S=bpy.context.scene
basehash=hashlib.sha256(BASE.read_bytes()).hexdigest()
def sig(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(row) for row in o.matrix_world])).encode()).hexdigest()
protected={o.name:sig(o) for o in S.objects if o.type=='MESH'}
C=bpy.data.collections.new('07_Full_garden_vegetation');S.collection.children.link(C)
# Reuse the accepted leaf and branch vocabulary without running its build script.
code=ast.parse((O.parent/'vegetation-v1/build.py').read_text(encoding='utf-8'))
ns={n.name:n for n in code.body if isinstance(n,ast.FunctionDef)}
exec(compile(ast.Module(body=[ns[n] for n in ['add','leaf','branch','tree']],type_ignores=[]),'<accepted-vegetation-functions>','exec'))
rng=random.Random(92928);B={};leaf_count=0;stems=[];materials=[bpy.data.materials['VEG1 '+n] for n in ['olive','grey-green','deep-green','young-green','autumn','bark']]
def ground(x,y):return 0

def flush_meshes(fid):
 result=[]
 for name,(v,f,mi) in B.items():
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],f);mesh.update()
  for m in materials:mesh.materials.append(m)
  for p,idx in zip(mesh.polygons,mi):p.material_index=idx;p.use_smooth='branches' in name
  ob=bpy.data.objects.new(name,mesh);C.objects.link(ob);ob['feature_id']=fid;ob['source_photos']=[4338,4377,4474,4539];ob['geometry_confidence']='inferred';result.append(ob)
 B.clear();return result
# Four reusable prototypes: same leaf detail, fuller background crowns.
prototypes=[]
for i in range(4):
 tree('V2 prototype '+str(i),0,0,8,3.7+i*.18,95+i*8)
 objects=flush_meshes('VEGETATION_V2');prototypes.append([o.data for o in objects])
 for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
# Ground/obstacle ray casts constrain planting, with open lawn excluded.
def is_grass(m):return bool(m and any(k in m.name.lower() for k in ['grass','lawn','turf']))
verts=[];faces=[];gv=[];gf=[]
for ob in list(S.objects):
 if ob.type!='MESH' or ob.get('feature_id') in ['VEGETATION','VEGETATION_PILOT','VEGETATION_V2','CONTEXT_GUANGHUA']:continue
 ob.data.calc_loop_triangles()
 for tri in ob.data.loop_triangles:
  mat=ob.data.materials[tri.material_index] if ob.data.materials else None
  isg=is_grass(mat);vlist,flist=(gv,gf) if isg else (verts,faces)
  pts=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices]
  if (pts[1]-pts[0]).cross(pts[2]-pts[0]).z<=1e-5:continue
  n=len(vlist);vlist.extend(pts);flist.append((n,n+1,n+2))
obstacles=BVHTree.FromPolygons(verts,faces,all_triangles=True);terrain=BVHTree.FromPolygons(gv,gf,all_triangles=True)
def site(x,y):
 hit=terrain.ray_cast(Vector((x,y,30)),Vector((0,0,-1)))
 if hit[0] is None:return None
 z=hit[0].z
 for dx,dy in [(0,0),(.55,0),(-.55,0),(0,.55),(0,-.55)]:
  h=obstacles.ray_cast(Vector((x+dx,y+dy,30)),Vector((0,0,-1)))
  if h[0] is not None and h[0].z>=z-.03:return None
 return z
positions=json.loads((R/'field-review/guanghua-complete-v3/assembly.json').read_text())['tree_positions']
pilot=json.loads((O.parent/'vegetation-v1/validation.json').read_text())['trees']
placed=[];skipped=[]
candidates=[(*p,'existing') for p in positions]
candidates += [(x,y,8.5+((i+j)%3),'infill') for i,x in enumerate([-73,-62,-51,-40]) for j,y in enumerate([18,43,69,88])]
candidates += [(x,8,10+(i%3),'south') for i,x in enumerate(range(-67,96,10))]
candidates += [(x,y,8+(j%3),'east') for x in [86,97] for j,y in enumerate([24,46,77,87])]
for x,y,h,kind in candidates:
 if any(math.hypot(x-t['x'],y-t['y'])<4.0 for t in pilot) or any(math.hypot(x-t['x'],y-t['y'])<5 for t in placed):continue
 z=site(x,y)
 if z is None:
  skipped.append([x,y,kind]);continue
 k=len(placed);angle=rng.uniform(0,math.tau);scale=h/8
 for mesh in prototypes[k%4]:
  ob=bpy.data.objects.new('V2 tree %02d '%k+mesh.name,mesh);C.objects.link(ob);ob.location=(x,y,z);ob.rotation_euler.z=angle;ob.scale=(scale*rng.uniform(.94,1.08),scale,scale)
  ob['feature_id']='VEGETATION_V2';ob['source_photos']=[4338,4474];ob['geometry_confidence']='inferred'
 placed.append(dict(x=x,y=y,z=z,height=h,origin=kind))
# Retain source objects for editing but replace their visible trunks and ball crowns.
hidden=[]
for ob in S.objects:
 if ob.get('feature_id')=='VEGETATION' and any(p in ob.name for p in ['tree-trunks','tree-branches','tree-canopies']):ob.hide_render=True;ob.hide_set(True);hidden.append(ob.name)
# Add leaves to remaining planted masses. Sample existing surfaces, not empty land.
plant_sources=[]
for ob in list(S.objects):
 if ob.type!='MESH' or ob.hide_render or ob.get('feature_id') in ['VEGETATION_PILOT','VEGETATION_V2']:continue
 fid=ob.get('feature_id');name=ob.name.lower()
 if fid in ['ESKY','EOPEN_S','ETERR']:continue # accepted sample untouched
 if not any(k in name for k in ['hedge','shrub','vines','leaf-clusters']):continue
 if 'core' in name:continue
 plant_sources.append(ob.name);ob.data.calc_loop_triangles();total=sum(t.area for t in ob.data.loop_triangles);density=min(190,14000/max(total,1))
 for tri in ob.data.loop_triangles:
  a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices];normal=(b-a).cross(c-a);area=normal.length*.5
  if area<1e-8:continue
  normal.normalize()
  if normal.z<-.35:continue
  for i in range(int(area*density+rng.random())):
   u=math.sqrt(rng.random());v=rng.random();p=(1-u)*a+u*(1-v)*b+u*v*c+normal*rng.uniform(.015,.065)
   leaf('V2 leaves '+str(fid),p,rng.uniform(.065,.12),rng.choice([0,1,2,2,3]))
foliage_objects=flush_meshes('VEGETATION_V2')
# Portable image textures: gentle multi-scale variation, plus fine blade-like grain.
texrng=np.random.default_rng(929)
def make_texture(name,base,grass=False,n=512):
 y,x=np.mgrid[0:n,0:n].astype(np.float32);x/=n;y/=n
 coarse=np.zeros((n,n),np.float32)
 for kx,ky,amp in [(1,2,.035),(3,1,.024),(5,4,.012),(13,9,.006)]:coarse+=amp*np.sin(math.tau*(x*kx+y*ky)+texrng.uniform(0,6.28))
 grain=texrng.normal(0,.018 if grass else .008,(n,n)).astype(np.float32)
 fine=.012*np.sin(math.tau*(x*167+y*23))*np.sin(math.tau*y*97) if grass else 0
 color=np.empty((n,n,4),np.float32)
 for i,b in enumerate(base):color[:,:,i]=np.clip(b+coarse+grain+fine,.015,.85)
 if grass:
  dry=np.maximum(0,np.sin(math.tau*(x*2-y*3)+1.2)*np.sin(math.tau*(x*3+y))+-.25)*.045
  color[:,:,0]+=dry;color[:,:,1]+=dry*.35;color[:,:,2]+=dry*.28
 color[:,:,3]=1
 im=bpy.data.images.new(name,width=n,height=n);im.pixels.foreach_set(color.ravel());im.filepath_raw=str(O/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
fixed=[];grass_mats=[]
for mat in list(bpy.data.materials):
 if not mat.users or not mat.use_nodes or mat.name.startswith('VEG1 '):continue
 p=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p:continue
 grass=is_grass(mat);linked=p.inputs['Base Color'].is_linked
 if not grass and (not linked or any(n.type=='TEX_IMAGE' and n.image for n in mat.node_tree.nodes)):continue
 base=list(mat.diffuse_color[:3]);base=[.27,.33,.12] if grass else base
 for link in list(p.inputs['Base Color'].links):mat.node_tree.links.remove(link)
 p.inputs['Base Color'].default_value=(*base,1)
 # Grass and broad surfaces receive embedded RGB textures. Leaf/bark keep colour.
 if grass or any(k in mat.name.lower() for k in ['paver','stone','concrete','granite','ramp']):
  im=make_texture('V2_'+mat.name.replace(' ','_'),base,grass,n=2048 if grass else 512)
  node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;node.interpolation='Linear'
  uv=mat.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map='V2_surface_UV';mat.node_tree.links.new(uv.outputs[0],node.inputs['Vector']);mat.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color'])
 if grass:
  p.inputs['Roughness'].default_value=.96;grass_mats.append(mat.name)
  for link in list(p.inputs['Normal'].links):mat.node_tree.links.remove(link)
 fixed.append(mat.name)
# Add world-scale UVs only; geometry stays intact.
for ob in S.objects:
 if ob.type!='MESH' or not any(m and m.name in fixed for m in ob.data.materials):continue
 uv=ob.data.uv_layers.get('V2_surface_UV') or ob.data.uv_layers.new(name='V2_surface_UV')
 grass=any(is_grass(m) for m in ob.data.materials)
 for loop in ob.data.loops:
  co=ob.matrix_world@ob.data.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x/(24 if grass else 4),co.y/(24 if grass else 4))
assert all(sig(bpy.data.objects[n])==h for n,h in protected.items())
S.camera=bpy.data.objects['FINAL landscape'];S.render.engine='CYCLES';S.cycles.samples=20;S.cycles.use_denoising=True;S.render.threads_mode='FIXED';S.render.threads=8
S.render.resolution_x=1400;S.render.resolution_y=980;S.render.resolution_percentage=100
# Keep this study independent from the production campus model.
S['vegetation_revision']='v2 full garden; accepted pilot preserved; compatible materials and grass texture'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'vegetation-v2.blend'))
for name,cam in [('overall','FINAL landscape'),('east','SHAPE exit approximate'),('west','03-west-garden'),('lawn','05-north-photo-4474')]:
 S.camera=bpy.data.objects[cam];S.render.filepath=str(O/('after-'+name+'.png'));bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in S.objects:
 if ob.type=='MESH' and not ob.hide_render:ob.hide_set(False);ob.select_set(True)
export_visible_glb(filepath=str(O/'vegetation-v2.glb'))
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==basehash
report=dict(baseline_unchanged=True,original_geometry_and_transforms_unchanged=True,preserved_meshes=len(protected),trees=placed,skipped_blocked_positions=skipped,hidden_old_tree_objects=hidden,planted_surface_sources=plant_sources,portable_materials=fixed,grass_materials=grass_mats,prototype_count=4,glb_bytes=(O/'vegetation-v2.glb').stat().st_size,scope='All garden vegetation at accepted pilot detail; not measured reconstruction')
(O/'validation.json').write_text(json.dumps(report,indent=2));print('FULL_GARDEN_COMPLETE',flush=True)
