import bpy,bmesh,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent
base=O/'stage01-east.blend'
baseline_hash=hashlib.sha256(base.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(base))
def signature(o):
 return hashlib.sha256(repr((list(o.matrix_world),[tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
protected={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')!='EPATH'}
paths=[o for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')=='EPATH' and 'terrain' not in o.name]
terrain=[o for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')=='EPATH' and 'terrain' in o.name]
# Resolve the overlapping 2.5D surfaces with a constrained planar triangulation.
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt
verts=[];faces=[];samples=[];bins={}
for o in paths+terrain:
 o.data.calc_loop_triangles()
 for tri in o.data.loop_triangles:
  if tri.normal.z<.01:continue
  pts=[o.data.vertices[i].co.copy() for i in tri.vertices]
  idx=len(samples);samples.append((pts,o in paths))
  for x in range(int(min(p.x for p in pts))-1,int(max(p.x for p in pts))+2):
   for y in range(int(min(p.y for p in pts))-1,int(max(p.y for p in pts))+2):bins.setdefault((x,y),[]).append(idx)
  start=len(verts);verts.extend([Vector((p.x,p.y)) for p in pts]);faces.append(tuple(range(start,start+3)))
def heights(p):
 road=[];earth=[]
 for idx in bins.get((int(p.x),int(p.y)),[]):
  (a,b,c),isroad=samples[idx]
  den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
  if abs(den)<1e-10:continue
  u=((b.y-c.y)*(p.x-c.x)+(c.x-b.x)*(p.y-c.y))/den
  v=((c.y-a.y)*(p.x-c.x)+(a.x-c.x)*(p.y-c.y))/den;w=1-u-v
  if min(u,v,w)>=-1e-5:(road if isroad else earth).append(u*a.z+v*b.z+w*c.z)
 return road,earth
vv,ee,ff,*_=delaunay_2d_cdt(verts,[],faces,1,0.00001)
coords=[]
for p in vv:
 r,t=heights(p);coords.append((p.x,p.y,max(r+t+[.008])+.003))
mesh=bpy.data.meshes.new('EPATH_continuous_surface');mesh.from_pydata(coords,[],ff);mesh.update()
main=next(o for o in paths if '__main-curve__' in o.name)
roadmat=main.data.materials[0];earthmat=terrain[0].data.materials[0]
mesh.materials.append(roadmat);mesh.materials.append(earthmat)
for poly in mesh.polygons:
 center=sum((vv[i] for i in poly.vertices),Vector((0,0)))/len(poly.vertices)
 r,t=heights(center);poly.material_index=0 if r else 1
uv=mesh.uv_layers.new(name='V4_surface')
for loop in mesh.loops:
 co=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x*.3,co.y*.3)
main.data=mesh
for o in paths+terrain:
 if o!=main:bpy.data.objects.remove(o,do_unlink=True)
main['repair_note']='Continuous constrained triangulation; overlapping pavement and shoulder surfaces replaced by a single upper envelope. Grades inferred.'
main['source_photos']=[4496,4507,4513,4565,4568,4574,4581,4585]
main['revision']='v4-stage02-path-repair'
assert protected=={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')!='EPATH'}
target=O/'stage02-east-path-repair.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.wm.open_mainfile(filepath=str(target))
assert protected=={o.name:signature(o) for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')!='EPATH'}
assert hashlib.sha256(base.read_bytes()).hexdigest()==baseline_hash
report={'baseline_sha256':baseline_hash,'baseline_unchanged':True,'non_EPATH_geometry_unchanged':True,'reopen_passed':True,'scope':'Mesh repair only; route, terrain grade and exit heights remain inferred.'}
(O/'stage02-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s=bpy.context.scene;s.cycles.samples=12
for name in ['east-top','east-exit']:
 s.camera=bpy.data.objects['V4 '+name];s.render.filepath=str(O/('stage02-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('STAGE02_DONE')

