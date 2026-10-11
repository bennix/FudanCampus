import bpy,bmesh,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent
BASE=O.parent/'west-entry-v3/west-entry-aligned-v3.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(ob):
 a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
 return hashlib.sha256(a.tobytes()+str(list(ob.matrix_world)).encode()+str([tuple(p.vertices) for p in ob.data.polygons]).encode()).hexdigest()
def all_digests():return {o.name:digest(o) for o in bpy.context.scene.objects if o.type=='MESH'}
def verify_unchanged(before,changed=()):
 after=all_digests();fixed={n:h for n,h in before.items() if n not in changed}
 assert all(after.get(n)==h for n,h in fixed.items()),[n for n,h in fixed.items() if after.get(n)!=h]
 return len(fixed)
def collection(name):
 c=bpy.data.collections.get(name)
 if not c:c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
 return c
def uv(ob,scale=1):
 layer=ob.data.uv_layers.active or ob.data.uv_layers.new(name='V4 metric UV')
 for p in ob.data.polygons:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=(1,2) if axis==0 else (0,2) if axis==1 else (0,1)
  for li in p.loop_indices:
   q=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co
   layer.data[li].uv=(q[axes[0]]/scale,q[axes[1]]/scale)
def mesh(name,vs,fs,mat,fid,refs,smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);collection('09_V4 photo refinement').objects.link(ob);me.materials.append(mat)
 ob['feature_id']=fid;ob['source_photos']=refs;ob['geometry_confidence']='inferred';ob['dimension_status']='推定 / photo proportion estimate; not measured'
 ob['evidence_status']='Visible component relationship confirmed; dimensions inferred'
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 for p in me.polygons:p.use_smooth=smooth
 uv(ob);return ob
def box(name,loc,size,mat,fid,refs,bevel=0):
 x,y,z=loc;w,d,h=size
 vs=[(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 ob=mesh(name,vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,fid,refs)
 if bevel:m=ob.modifiers.new('Small stone bevel','BEVEL');m.width=bevel;m.segments=2
 return ob
def prism(name,pts,z0,z1,mat,fid,refs):
 pts=list(pts)
 if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0:pts.reverse()
 n=len(pts);ob=mesh(name,[(x,y,z0(x,y) if callable(z0) else z0) for x,y in pts]+[(x,y,z1(x,y) if callable(z1) else z1) for x,y in pts],
  [tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,fid,refs)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(ob.data);bm.free();ob.data.update();uv(ob);return ob
def lathe(name,cx,cy,profile,mat,fid,refs,flute=0,N=96):
 # Zero-radius profile entries use one pole vertex, preventing degenerate cap fans.
 vs=[];rings=[]
 for j,(r,z) in enumerate(profile):
  if r<1e-6:rings.append([len(vs)]);vs.append((cx,cy,z));continue
  rings.append(list(range(len(vs),len(vs)+N)))
  for i in range(N):
   a=i*math.tau/N;rr=r*(1+flute*math.cos(a*32));vs.append((cx+rr*math.cos(a),cy+rr*math.sin(a),z))
 fs=[]
 for a,b in zip(rings,rings[1:]):
  for i in range(N):
   k=(i+1)%N
   fs.append((a[0],b[k],b[i]) if len(a)==1 else (a[i],a[k],b[0]) if len(b)==1 else (a[i],a[k],b[k],b[i]))
 if len(rings[0])>1:fs.append(tuple(reversed(rings[0])))
 if len(rings[-1])>1:fs.append(tuple(rings[-1]))
 return mesh(name,vs,fs,mat,fid,refs,True)
def ribbon(name,points,width,zbottom,ztop,mat,fid,refs):
 qs=[Vector(p[:2]) for p in points];vs=[]
 closed=(qs[0]-qs[-1]).length<1e-6
 if closed:qs=qs[:-1]
 for i,q in enumerate(qs):
  if closed:
   a=(q-qs[(i-1)%len(qs)]).normalized();b=(qs[(i+1)%len(qs)]-q).normalized()
   na=Vector((-a.y,a.x));nb=Vector((-b.y,b.x));m=(na+nb).normalized();u=m*width/2/max(.2,m.dot(nb))
  else:
   tangent=(qs[min(i+1,len(qs)-1)]-qs[max(0,i-1)]).normalized();u=Vector((-tangent.y,tangent.x))*width/2
  a,b=q+u,q-u;lo=zbottom(q.x,q.y) if callable(zbottom) else zbottom;hi=ztop(q.x,q.y) if callable(ztop) else ztop
  vs.extend([(a.x,a.y,lo),(b.x,b.y,lo),(b.x,b.y,hi),(a.x,a.y,hi)])
 fs=[] if closed else [(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]
 for i in range(len(qs) if closed else len(qs)-1):
  nexti=(i+1)%len(qs)
  for j in range(4):a=4*i+j;b=4*i+(j+1)%4;fs.append((a,b,nexti*4+(j+1)%4,nexti*4+j))
 return mesh(name,vs,fs,mat,fid,refs)
def bezier(a,b,c,d,N=40):
 a,b,c,d=[Vector(p) for p in (a,b,c,d)]
 return [tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in [i/N for i in range(N+1)]]
def union(target,other):
 bpy.context.view_layer.objects.active=target
 mod=target.modifiers.new('Continuous stone junction','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=other
 bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(other,do_unlink=True);uv(target)
def solid_check(ob):
 bm=bmesh.new();bm.from_mesh(ob.data)
 report=dict(name=ob.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),zero_area=sum(f.calc_area()<1e-9 for f in bm.faces),volume=bm.calc_volume(signed=True),finite=all(math.isfinite(c) for v in bm.verts for c in v.co))
 bm.free();assert report['nonmanifold']==0 and report['zero_area']==0 and report['volume']>0 and report['finite'],report
 return report
def camera(name,loc,target,scale=None,lens=27):
 ob=bpy.data.objects.get(name)
 if not ob:d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);collection('10_V4 review cameras').objects.link(ob)
 ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
 ob.data.type='ORTHO' if scale else 'PERSP';ob.data.lens=lens;ob.data.clip_end=2000
 if scale:ob.data.ortho_scale=scale
 ob['camera_confidence']='Manual photo-like view; extrinsics and focal length inferred, not solved'
 return ob
def render(path,cam,top=False,width=1200,samples=20,ratio=.75):
 s=bpy.context.scene;hidden=[]
 if top:
  hidden=[ob for ob in s.objects if ob.type=='MESH' and not ob.hide_render and (ob.get('feature_id')=='CONTEXT_GUANGHUA' or any(t in ob.name.lower() for t in ['leaves','canopy','mound','tree-crown']))]
  for ob in hidden:ob.hide_render=True
 s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True
 s.render.resolution_x=width;s.render.resolution_y=round(width*ratio);s.render.resolution_percentage=100
 s.render.image_settings.file_format='PNG';s.render.filepath=str(O/path)
 bpy.ops.render.render(write_still=True)
 for ob in hidden:ob.hide_render=False
def save_report(stage,report):
 report['baseline_unchanged']=sha(BASE)==json.loads((O/'baseline-lock.json').read_text())['source_sha256']
 assert report['baseline_unchanged']
 report['dimensions']='推定：照片比例，未实测';(O/(stage+'-validation.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print('STAGE_VALIDATED',stage,flush=True)
def texture_material(name,color,period,pattern,N=768):
 rng=np.random.default_rng(930104);yy,xx=np.mgrid[:N,:N]/N;xx*=period[0];yy*=period[1]
 tone=rng.normal(0,.008,(N,N))+pattern(xx,yy,rng)
 rgba=np.ones((N,N,4),np.float32)
 for k,b in enumerate(color):rgba[:,:,k]=np.clip(b+tone,.02,.9)
 im=bpy.data.images.new(name+' albedo',width=N,height=N);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(O/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True;nt=mat.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.84
 tx=nt.nodes.new('ShaderNodeTexImage');tx.image=im;nt.links.new(tx.outputs['Color'],p.inputs['Base Color'])
 return mat
def clean_path_material():
 def pattern(x,y,rng):
  # Evenly distributed periodic seeds avoid nearly coincident seeds producing
  # the broad black triangular wedges in the inherited pink-path image.
  seeds=np.array([((i+.5+rng.uniform(-.29,.29))*4/7,(j+.5+rng.uniform(-.29,.29))*4/7) for j in range(7) for i in range(7)])
  first=np.full(x.shape,np.inf);second=first.copy();ia=np.zeros(x.shape,int);ib=ia.copy()
  for k,(sx,sy) in enumerate(seeds):
   dx=(x-sx+2)%4-2;dy=(y-sy+2)%4-2;d=dx*dx+dy*dy;near=d<first;runner=(~near)&(d<second)
   ib=np.where(near,ia,np.where(runner,k,ib));second=np.where(near,first,np.where(runner,d,second))
   ia=np.where(near,k,ia);first=np.minimum(first,d)
  delta=(seeds[:,None,:]-seeds[None,:,:]+2)%4-2;dist=np.sqrt((delta*delta).sum(axis=2))
  edge=(second-first)/np.maximum(1e-5,2*dist[ia,ib])
  seam=-.082*np.exp(-(edge/.012)**2)
  return seam+.012*np.sin(ia*17.31)
 mat=texture_material('V4 clean irregular garden stone',(.53,.455,.407),(4,4),pattern)
 mat['reference']='IMG_4496, 4585';mat['estimated_joint_width']=.024;mat['dimension_status']='推定 / not measured'
 return mat
