import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
from mathutils.geometry import delaunay_2d_cdt
bpy.ops.wm.open_mainfile(filepath=str(O/'stage03-straight-path.blend'));s=bpy.context.scene;before=all_digests()
names=['EPATH__main-curve__pink-path','EPATH__lawn-connection__pink-path','EPATH__north-exit-path__pink-path','E_ENTRY northern curve within garden']
paths=[bpy.data.objects[n] for n in names];changed=names
cams={'top':bpy.data.objects['V4 straight path overhead'],
 '4496':camera('V4 approximate photo4496',(65.8,78.2,1.8),(78.9,66,1.0),lens=27),
 'junction':camera('V4 flat path crossing diagnostic',(74.5,31,20),(74.5,31,0),9)}
render('stage04-before-junction.png',cams['junction'],True,width=1000,samples=12)
render('stage04-before-4496.png',cams['4496'],width=1000,samples=12)
vs=[];faces=[];samples=[];bins={};source_area=0
for ob in paths:
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
 for tri in me.loop_triangles:
  if tri.normal.z<.01:continue
  pts=[ob.matrix_world@me.vertices[i].co for i in tri.vertices]
  area=abs((pts[1].x-pts[0].x)*(pts[2].y-pts[0].y)-(pts[1].y-pts[0].y)*(pts[2].x-pts[0].x))/2
  if area<1e-9:continue
  source_area+=area;k=len(samples);samples.append(pts)
  for x in range(math.floor(min(p.x for p in pts)),math.floor(max(p.x for p in pts))+1):
   for y in range(math.floor(min(p.y for p in pts)),math.floor(max(p.y for p in pts))+1):bins.setdefault((x,y),[]).append(k)
  start=len(vs);vs.extend([Vector((p.x,p.y)) for p in pts]);faces.append(tuple(range(start,start+3)))
 ev.to_mesh_clear()
def heights(q):
 out=[]
 for idx in bins.get((math.floor(q.x),math.floor(q.y)),[]):
  a,b,c=samples[idx];den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
  u=((b.y-c.y)*(q.x-c.x)+(c.x-b.x)*(q.y-c.y))/den
  v=((c.y-a.y)*(q.x-c.x)+(a.x-c.x)*(q.y-c.y))/den;w=1-u-v
  if min(u,v,w)>-1e-5:out.append(u*a.z+v*b.z+w*c.z)
 return out
v2,e2,f2,*_=delaunay_2d_cdt(vs,[],faces,1,1e-5)
valid=[];area=0
for face in f2:
 center=sum((v2[i] for i in face),Vector((0,0)))/len(face)
 if not heights(center):continue
 p=[v2[i] for i in face]
 facearea=abs(sum(p[j].x*p[(j+1)%len(p)].y-p[(j+1)%len(p)].x*p[j].y for j in range(len(p))))/2
 if facearea<1e-8:continue
 valid.append(tuple(face));area+=facearea
used=sorted({i for face in valid for i in face});idx={q:i for i,q in enumerate(used)}
top=[(v2[i].x,v2[i].y,max(heights(v2[i]) or [.095])) for i in used]
topfaces=[tuple(idx[i] for i in face) for face in valid]
# Cap only the union boundary. No duplicated coplanar triangles remain.
edgecount={};directed={}
for face in topfaces:
 for a,b in zip(face,face[1:]+face[:1]):key=tuple(sorted((a,b)));edgecount[key]=edgecount.get(key,0)+1;directed[key]=(a,b)
boundary=[directed[k] for k,n in edgecount.items() if n==1];assert all(n<=2 for n in edgecount.values())
n=len(top);vs3=top+[(x,y,-.035) for x,y,z in top]
fs3=topfaces+[tuple(n+i for i in reversed(f)) for f in topfaces]+[(b,a,a+n,b+n) for a,b in boundary]
ob=mesh('EPATH continuous union surface',vs3,fs3,paths[0].data.materials[0],'EPATH',[4496,4585,4492])
bm=bmesh.new();bm.from_mesh(ob.data)
tiny_before=[dict(area=f.calc_area(),vertices=[list(v.co) for v in f.verts]) for f in bm.faces if f.calc_area()<1e-9]
print('CDT_FLOAT_PRECISION_FACES',json.dumps(tiny_before),flush=True)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5)
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-5)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();ob.data.update()
ob['repair_note']='Constrained 2D union and original upper envelope; removed overlapping coplanar surfaces and folded junction quads; route footprint inherited'
ob.data.materials.clear();ob.data.materials.append(clean_path_material());uv(ob,4)
ob['finish_repair']='Inherited pink-path texture had visible repeated black wedges; replaced with even-seed constant-width stone joints'
for old in paths:bpy.data.objects.remove(old,do_unlink=True)
solid=solid_check(ob);unchanged=verify_unchanged(before,changed)
assert source_area-area>0,'No duplicate-area removal found'
probe=[];tree=BVHTree.FromPolygons([v.co for v in ob.data.vertices],[list(p.vertices) for p in ob.data.polygons])
for q in [(74.5,31),(76.8,65.5),(82.6,70.05)]:
 hit,norm,_,_=tree.ray_cast(Vector((*q,10)),Vector((0,0,-1)),15)
 probe.append(dict(xy=q,hit=list(hit) if hit else None,normal=list(norm) if norm else None))
s.camera=cams['4496'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage04-curve-repair.blend'))
save_report('stage04',dict(protected_meshes_unchanged=unchanged,source_road_meshes=names,source_projected_area=source_area,union_projected_area=area,removed_overlap_area=source_area-area,upper_envelope='source road heights, no extra clearance lift',northern_folded_quads_removed=True,precision_degenerate_faces_removed=len(tiny_before),solid=solid,ray_probes=probe,views=['top','4496','junction'],limits=['Old independent elevated road/terrain at east terrace retained','Site route, heights and camera remain inferred']))
for k,cam in cams.items():render('stage04-after-'+k+'.png',cam,k in ['top','junction'],width=1400,samples=24)
print('STAGE04_COMPLETE',flush=True)
