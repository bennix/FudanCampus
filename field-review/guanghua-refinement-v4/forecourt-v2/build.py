import bpy,bmesh,math,json,hashlib,random,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;R=O.parents[2]
BASE=O.parent/'forecourt-v1/forecourt-entry-v1.blend'
basehash=hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
rng=random.Random(93041); nr=np.random.default_rng(93041)
C=bpy.data.collections.new('08_Forecourt_refinement');s.collection.children.link(C)
outline=json.loads((R/'field-review/guanghua-lawn-shape-v2/outline.json').read_text())
poly=[(x-25,y+16) for x,y in outline['polygon_xy']]
north=list(reversed(poly[2:])); tip=poly[2]; AX=(tip[0]+67.10211756)/2; Y=tip[1]; PY=Y+1.21
def digest(o):
 a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a)
 return hashlib.sha256(a.tobytes()+str(list(o.matrix_world)).encode()).hexdigest()
fixed={o.name:digest(o) for o in s.objects if o.type=='MESH' and o.get('feature_id') in ['LAWN','WTERR','ETERR','CONTEXT_GUANGHUA']}
def mesh(name,vs,fs,mat,fid='FORECOURT',smooth=False):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
 ob=bpy.data.objects.new(name,me);C.objects.link(ob);me.materials.append(mat)
 ob['feature_id']=fid;ob['geometry_confidence']='inferred photo proportions';ob['source_photos']=[4491,4492] if fid=='E_ENTRY' else [4474,4485] if fid=='FORECOURT' else [4467,4468]
 for p in me.polygons:p.use_smooth=smooth
 return ob
def box(name,loc,size,mat,fid='FORECOURT',bevel=0):
 x,y,z=loc;w,d,h=size
 vs=[(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 ob=mesh(name,vs,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,fid)
 if bevel:
  mod=ob.modifiers.new('stone edge','BEVEL');mod.width=bevel;mod.segments=2
 return ob
def prism(name,pts,z0,z1,mat,fid='FORECOURT'):
 if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0:pts=list(reversed(pts))
 n=len(pts);ob=mesh(name,[(x,y,z) for z in [z0,z1] for x,y in pts],[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,fid)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();return ob
def uv(ob,scale=1):
 layer=ob.data.uv_layers.get('FORECOURT_metric') or ob.data.uv_layers.new(name='FORECOURT_metric');ob.data.uv_layers.active=layer;layer.active_render=True
 for p in ob.data.polygons:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=(1,2) if axis==0 else (0,2) if axis==1 else (0,1)
  for li in p.loop_indices:
   co=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co;layer.data[li].uv=(co[axes[0]]/scale,co[axes[1]]/scale)
def material(name,color,rough=.8,metal=0,kind='stone'):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1);nt=m.node_tree;p=nt.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 n=2048 if kind=='plaza' else 512
 yy,xx=np.mgrid[:n,:n]/n
 tone=nr.normal(0,.012,(n,n))
 if kind=='plaza':
  x=xx*9.6;y=yy*9.6
  # Four 1.2m slabs per 4.8m bay; broad light bands and thin joints.
  tx=(x//1.2).astype(int);ty=(y//1.2).astype(int);tile=nr.normal(0,.013,(8,8))[ty,tx]
  band=(np.mod(x,4.8)<.16)|(np.mod(y,4.8)<.16)
  seam=(np.mod(x,1.2)<.012)|(np.mod(y,1.2)<.012)
  tone+=tile+band*.105-seam*.095
 elif kind=='bronze':tone+=.035*np.sin(xx*22+np.sin(yy*36))*np.sin(yy*16)+.014*np.sin(xx*100)*np.sin(yy*81)
 elif kind=='urn':tone+=-.035*np.maximum(0,np.sin(xx*110+.3*np.sin(yy*15)))*(.4+.6*yy)
 rgba=np.ones((n,n,4),np.float32)
 for i,b in enumerate(color):rgba[:,:,i]=np.clip(b+tone,.015,.94)
 im=bpy.data.images.new(name+' albedo',width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(O/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 t=nt.nodes.new('ShaderNodeTexImage');t.image=im;nt.links.new(t.outputs['Color'],p.inputs['Base Color'])
 tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=85 if kind!='bronze' else 18;tex.inputs['Detail'].default_value=3
 bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.008 if kind!='bronze' else .016;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
stone=material('FC_warm_granite',(.50,.455,.415));pale=material('FC_light_band',(.61,.58,.53));paving=material('FC_plaza_grid',(.43,.42,.40),kind='plaza');urnmat=material('FC_fluted_white',(.73,.735,.69),kind='urn');bronze=material('FC_patinated_bronze',(.25,.30,.27),.72,.38,'bronze');rock=material('FC_plinth_rock',(.53,.475,.39));dark=material('FC_plaque',(.18,.20,.19),.62,.15);letter=material('FC_engraving',(.012,.017,.014),.7)
soil=bpy.data.materials['FIN_garden_grass'];pathmat=bpy.data.materials['pink-path']
def remove_region(ob,predicate):
 bm=bmesh.new();bm.from_mesh(ob.data)
 doomed=[v for v in bm.verts if predicate(ob.matrix_world@v.co)]
 bmesh.ops.delete(bm,geom=doomed,context='VERTS');bm.to_mesh(ob.data);bm.free();ob.data.update()
def shift_region(ob,predicate,delta):
 inv=ob.matrix_world.inverted().to_3x3();d=inv@Vector(delta)
 for v in ob.data.vertices:
  if predicate(ob.matrix_world@v.co):v.co+=d
 ob.data.update()
def planar_path(name,points,width,mat=pathmat):
 # Catmull-Rom interpolation, independent closed short slabs.
 p=[Vector(points[0])]+[Vector(v) for v in points]+[Vector(points[-1])];qs=[]
 for i in range(1,len(p)-2):
  a,b,c,d=p[i-1:i+3]
  for j in range(10):
   t=j/10;qs.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 qs.append(Vector(points[-1]));vs=[];fs=[]
 for i,q in enumerate(qs):
  d=(qs[min(i+1,len(qs)-1)]-qs[max(0,i-1)]).normalized();u=Vector((-d.y,d.x))*width/2
  vs.extend([(q.x+u.x,q.y+u.y,.032),(q.x-u.x,q.y-u.y,.032)])
 for i in range(len(qs)-1):fs.append((i*2,i*2+1,i*2+3,i*2+2))
 ob=mesh(name,vs,fs,mat,'E_ENTRY');mod=ob.modifiers.new('paving thickness','SOLIDIFY');mod.thickness=.035;uv(ob,3);return ob
# Remove only east urn meshes, including the separately added foliage.
for ob in list(s.objects):
 if ob.type!='MESH':continue
 if ob.get('feature_id')=='FURNITURE':remove_region(ob,lambda p:59<p.x<71 and 87.7<p.y<90.3)
 if ob.get('feature_id')=='VEGETATION_V2':remove_region(ob,lambda p:59<p.x<71 and 87.6<p.y<90.4 and 1.45<p.z<2.7)
# Retreat northern stair opening as a rigid group, and its associated leaf skin.
for ob in s.objects:
 if ob.type!='MESH':continue
 if ob.get('feature_id')=='EOPEN':shift_region(ob,lambda p:True,(0,-6,0))
 elif ob.get('feature_id')=='VEGETATION_V2':shift_region(ob,lambda p:69.1<p.x<75.5 and 74.3<p.y<80.2 and p.z<1.1,(0,-6,0))
# Move the pre-existing spherical shrub away from the relocated stairs.
for ob in s.objects:
 if ob.type=='MESH' and (ob.get('feature_id')=='E_PLANTING' or ob.name.startswith('V2 leaves E_PLANTING')):
  shift_region(ob,lambda p:71.8<p.x<74.8 and 68.5<p.y<71.6 and p.z<2.5,(5,0,0))
# Fill the old hole and cut the new one in the terrain, so steps remain open.
ground=next(o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='GROUND')
patch=box('old north opening infill',(72.302,78,-.92),(3.25,4.25,1.84),soil,'E_ENTRY')
cutter=box('temporary relocated stair cut',(72.302,72,-1),(3.15,4.16,4),soil,'E_ENTRY')
bpy.context.view_layer.objects.active=ground;mod=ground.modifiers.new('north stair moved inward','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
# Shorten east edge walk at the aligned green tips; leave west unchanged.
for ob in s.objects:
 if ob.type=='MESH' and ob.get('feature_id')=='EDGE_PATHS' and 'edge-walk' in ob.name:
  for v in ob.data.vertices:
   p=ob.matrix_world@v.co
   if p.x>50 and p.y>Y:v.co.y-=p.y-Y
  # Apply new stone layout only to the east part through material assignment below.
# Replace only northern head of existing garden curve; keep every southern branch.
main=next(o for o in s.objects if o.name.startswith('EPATH__main-curve'))
bm=bmesh.new();bm.from_mesh(main.data);co=main.matrix_world.inverted()@Vector((0,70,0));no=main.matrix_world.to_3x3().transposed()@Vector((0,1,0))
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=co,plane_no=no,clear_outer=True)
cutends=[main.matrix_world@v.co for v in bm.verts if abs((main.matrix_world@v.co).y-70)<.001]
joinx=sum(p.x for p in cutends)/len(cutends)
bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(main.data);bm.free()
planar_path('E_ENTRY northern curve within garden',[(joinx,69.96),(83,72.7),(81.5,75.7),(77.5,76.4),(67.1,76.4)],1.55)
# Trim all east garden side-branches exactly at the walk edge, rather than overlap it.
for ob in s.objects:
 if ob.type=='MESH' and ob.get('feature_id')=='EPATH' and 'lawn-connection' in ob.name:
  bm=bmesh.new();bm.from_mesh(ob.data);c=ob.matrix_world.inverted()@Vector((67.10211756,0,0));n=ob.matrix_world.to_3x3().transposed()@Vector((-1,0,0))
  bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=c,plane_no=n,clear_outer=True);bm.to_mesh(ob.data);bm.free()
# Rebuild plaza boundary: lawn stays exactly fixed; garden side now ends at same tip.
old=next(o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='PLAZA');bpy.data.objects.remove(old,do_unlink=True)
garden_edge=[(67.10211756,Y),(71,Y),(77,Y+.65),(83,Y+3.4),(91,87),(102.30211756,87)]
plazapoly=[(-80,87),(-28.8,87),(-28.8,north[0][1])]+north+garden_edge+[(102.30211756,113),(-80,113)]
plaza=prism('FORECOURT photo grid plaza',plazapoly,-.035,.035,paving);uv(plaza,9.6)
for ob in s.objects:
 if ob.type=='MESH' and ob.get('feature_id')=='EDGE_PATHS' and 'edge-walk' in ob.name:
  # Avoid raising or reshaping west walk; retain original surfaces but use stone pattern.
  ob.data.materials.clear();ob.data.materials.append(paving);uv(ob,9.6)
# segmented curb around frozen lawn and garden end.
for ob in list(s.objects):
 if ob.type=='MESH' and ob.get('feature_id')=='EDGE_PATHS' and 'grass-curb' in ob.name:bpy.data.objects.remove(ob,do_unlink=True)
def curb(name,points,closed=False,width=.24,top=.15):
 pts=[Vector(p) for p in points];pts=pts+[pts[0]] if closed else pts
 lengths=[0]
 for a,b in zip(pts,pts[1:]):lengths.append(lengths[-1]+(b-a).length)
 def at(t):
  import bisect
  i=min(len(pts)-2,max(0,bisect.bisect_right(lengths,t)-1));return pts[i].lerp(pts[i+1],(t-lengths[i])/(lengths[i+1]-lengths[i]))
 n=math.ceil(lengths[-1]/.85);obs=[]
 for i in range(n):
  a=at(lengths[-1]*i/n+.004);b=at(lengths[-1]*(i+1)/n-.004);d=b-a;u=Vector((-d.y,d.x)).normalized()*width/2
  ob=prism(name+' %03d'%i,[tuple(a-u),tuple(b-u),tuple(b+u),tuple(a+u)],.016,top,stone,'LAWN_EDGE');uv(ob,1)
  mod=ob.modifiers.new('small chamfer','BEVEL');mod.width=.014;mod.segments=2;obs.append(ob)
 return obs
curbs=curb('LAWN_EDGE segmented granite',poly,True)
curbs+=curb('E_ENTRY aligned garden curb',garden_edge)
# White fluted shallow bowls, two exactly matching supports and finish.
def lathe(name,cx,cy,profile,mat,fid='E_ENTRY',flute=0):
 N=96;vs=[]
 for radius,z in profile:
  for i in range(N):
   t=i*math.tau/N;r=radius*(1+flute*math.cos(t*32));vs.append((cx+r*math.cos(t),cy+r*math.sin(t),z))
 fs=[]
 for j in range(len(profile)-1):
  for i in range(N):a=j*N+i;b=j*N+(i+1)%N;fs.append((a,b,b+N,a+N))
 fs.extend([tuple(range(N-1,-1,-1)),tuple((len(profile)-1)*N+i for i in range(N))])
 ob=mesh(name,vs,fs,mat,fid,True);uv(ob,1);return ob
leafm=bpy.data.materials.get('VEG1 olive') or bpy.data.materials['FIN_hedge'];red=material('FC_red_begonia',(.49,.018,.025),.83)
def petal_mesh(name,centres,mat,leaf=False):
 vs=[];fs=[]
 for cx,cy,z,a,sz in centres:
  if leaf:
   d=Vector((math.cos(a),math.sin(a),.4));u=Vector((-math.sin(a),math.cos(a),0));p=Vector((cx,cy,z));k=len(vs)
   vs.extend([tuple(p),tuple(p+d*sz*.48+u*sz*.34),tuple(p+d*sz+Vector((0,0,-.06))),tuple(p+d*sz*.48-u*sz*.34),tuple(p+d*sz*.45+Vector((0,0,.045)))])
   fs.extend([(k,k+1,k+4),(k+1,k+2,k+4),(k+2,k+3,k+4),(k+3,k,k+4)])
  else:
   for j in range(5):
    t=a+j*math.tau/5;p=Vector((cx,cy,z));d=Vector((math.cos(t),math.sin(t),.16));u=Vector((-math.sin(t),math.cos(t),0));k=len(vs)
    vs.extend([tuple(p),tuple(p+d*sz*.5+u*sz*.45),tuple(p+d*sz),tuple(p+d*sz*.5-u*sz*.45)]);fs.append((k,k+1,k+2,k+3))
 return mesh(name,vs,fs,mat,'E_ENTRY',True)
for idx,cx in enumerate([AX-3.5,AX+3.5]):
 box(f'E_ENTRY {idx} pedestal core',(cx,PY,.43),(2.15,2.15,.80),stone,'E_ENTRY',.025)
 box(f'E_ENTRY {idx} plinth foot',(cx,PY,.11),(2.22,2.22,.16),stone,'E_ENTRY',.012)
 box(f'E_ENTRY {idx} rounded coping',(cx,PY,.86),(2.30,2.30,.12),stone,'E_ENTRY',.045)
 # Panel seams on exposed sides, subtle and shallow.
 for side in [-1,1]:
  for xx in [-.69,.69]:box(f'E_ENTRY {idx} panel joint',(cx+xx,PY+side*1.077,.45),(.012,.009,.65),dark,'E_ENTRY')
 profile=[(.52,.92),(.61,.96),(.60,1.03),(.48,1.08),(.40,1.19),(.40,1.30),(.48,1.36),(.65,1.40),(.87,1.59),(1.10,1.77),(1.15,1.83),(1.10,1.88),(.99,1.85),(.88,1.67),(.66,1.49),(.0,1.47)]
 lathe(f'E_ENTRY {idx} fluted bowl',cx,PY,profile,urnmat,flute=.018)
 lathe(f'E_ENTRY {idx} soil',cx,PY,[(0,1.75),(1.02,1.75),(1.02,1.77),(0,1.77)],soil)
 leaves=[];flowers=[];rr=random.Random(817)
 for i in range(350):
  t=rr.random()*math.tau;r=math.sqrt(rr.random())*.96;z=1.80+.27*(1-r*r)+rr.uniform(-.04,.06)
  leaves.append((cx+r*math.cos(t),PY+r*math.sin(t),z,rr.random()*math.tau,rr.uniform(.11,.24)))
  if i%3==0:flowers.append((cx+r*math.cos(t),PY+r*math.sin(t),z+.10,rr.random()*math.tau,.055))
 petal_mesh(f'E_ENTRY {idx} broad leaves',leaves,leafm,True);petal_mesh(f'E_ENTRY {idx} red flowers',flowers,red)
# Low grass/earth feathering behind the granite, without changing the lawn outline.
grassm=bpy.data.materials['FIN_grass'];blades=[]
for i in range(700):
 j=rng.randrange(2,len(poly)-1);a=Vector(poly[j]);b=Vector(poly[j+1]);q=a.lerp(b,rng.random());d=(b-a).normalized();q+=Vector((-d.y,d.x))*.17
 if q.y<Y-1:blades.append((q.x,q.y,.056,rng.random()*math.tau,rng.uniform(.035,.085)))
petal_mesh('LAWN_EDGE sparse grass tips',blades,grassm,True)['feature_id']='LAWN_EDGE'
# Sculpture in west building-front garden. Geometry authored in local coordinates.
sculpt=[]
def loft(name,sections,mat=bronze,N=32,axis='x'):
 # sections: centre xyz, two local radii. Longitudinal anatomical volumes.
 vs=[]
 for j,(x,y,z,ra,rb) in enumerate(sections):
  for k in range(N):
   t=k*math.tau/N;w=1+.018*math.sin(t*5+j*.8)
   vs.append((x,y+ra*math.cos(t)*w,z+rb*math.sin(t)*w) if axis=='x' else (x+ra*math.cos(t)*w,y+rb*math.sin(t)*w,z))
 fs=[tuple(range(N-1,-1,-1)),tuple((len(sections)-1)*N+k for k in range(N))]
 for j in range(len(sections)-1):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;fs.append((a,b,b+N,a+N))
 ob=mesh('POET_DONKEY '+name,vs,fs,mat,'POET_DONKEY',True);uv(ob,.7);sculpt.append(ob);return ob
def tube(name,points,radii,mat=bronze,N=16):
 vs=[]
 for i,p in enumerate(points):
  p=Vector(p);d=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized();u=d.cross(Vector((0,1,0)))
  if u.length<.01:u=d.cross(Vector((1,0,0)))
  u.normalize();v=d.cross(u).normalized()
  for k in range(N):t=k*math.tau/N;vs.append(tuple(p+radii[i]*(u*math.cos(t)+v*math.sin(t))))
 fs=[tuple(range(N-1,-1,-1)),tuple((len(points)-1)*N+k for k in range(N))]
 for j in range(len(points)-1):
  for k in range(N):a=j*N+k;b=j*N+(k+1)%N;fs.append((a,b,b+N,a+N))
 ob=mesh('POET_DONKEY '+name,vs,fs,mat,'POET_DONKEY',True);uv(ob,.7);sculpt.append(ob);return ob
# Elongated donkey body, tucked haunches and descending neck/head.
loft('donkey torso',[(-.86,0,1.30,.08,.10),(-.68,0,1.42,.26,.38),(-.35,0,1.43,.34,.42),(.15,0,1.40,.38,.41),(.65,0,1.44,.32,.38),(.98,0,1.43,.22,.32),(1.08,0,1.43,.07,.14)])
loft('lowered neck',[(-1.26,0,.74,.13,.20),(-1.08,0,1.02,.19,.26),(-.86,0,1.34,.24,.35),(-.62,0,1.46,.25,.30)])
loft('long face',[(-1.64,0,.38,.11,.11),(-1.58,0,.49,.19,.18),(-1.41,0,.70,.19,.24),(-1.22,0,.94,.17,.22),(-1.09,0,1.02,.11,.16)])
loft('muzzle',[(-1.71,0,.39,.10,.11),(-1.64,0,.40,.16,.145),(-1.51,0,.47,.17,.12)])
for side in [-1,1]:
 tube('long ear '+str(side),[(-1.18,side*.13,1.04),(-1.31,side*.19,1.22),(-1.40,side*.22,1.38),(-1.42,side*.22,1.42)],[.075,.063,.030,.003],N=16)
 tube('front leg '+str(side),[(-.63,side*.23,1.33),(-.67,side*.26,.91),(-.77,side*.27,.58),(-.70,side*.28,.16),(-.79,side*.28,.095)],[.14,.105,.07,.068,.10])
 tube('hind leg '+str(side),[(.75,side*.23,1.37),(.77,side*.29,.99),(.57,side*.30,.68),(.83,side*.32,.37),(.85,side*.32,.14),(.76,side*.32,.09)],[.19,.15,.085,.064,.068,.10])
 loft('hoof front '+str(side),[(-.92,side*.28,.075,.055,.055),(-.83,side*.28,.075,.10,.07),(-.67,side*.28,.10,.08,.085)],N=20)
 loft('hoof rear '+str(side),[(.66,side*.32,.07,.06,.05),(.77,side*.32,.08,.10,.07),(.93,side*.32,.12,.075,.08)],N=20)
 tube('eye '+str(side),[(-1.35,side*.187,.86),(-1.35,side*.20,.86)],[.03,.022],dark,N=12)
tube('tail',[(.98,0,1.62),(1.12,.04,1.45),(1.15,.06,1.06),(1.02,.09,.78),(1.04,.13,.59)],[.065,.057,.044,.037,.07])
# continuous hanging robe with varying hem, shoulder and bowed head.
loft('rider body',[(.10,0,1.64,.27,.27),(.07,0,1.94,.31,.28),(-.06,0,2.27,.30,.25),(-.17,0,2.51,.25,.22),(-.23,0,2.62,.14,.13)],axis='z')
loft('bowed head',[(-.27,0,2.52,.11,.10),(-.34,0,2.68,.15,.14),(-.38,0,2.83,.14,.135),(-.39,0,2.92,.075,.08)],axis='z')
# Robe mantle: ring sections, long side hems, small asymmetric folds.
N=72;vs=[]
for j in range(13):
 t=j/12
 for k in range(N):
  a=k*math.tau/N;side=abs(math.sin(a));hem=1.57-.78*side+.10*math.cos(a)
  z=2.73*(1-t)+hem*t
  shoulder=math.sin(min(1,t*4)*math.pi/2)
  radx=.12+.18*shoulder+.36*t;rady=.115+.19*shoulder+.23*t
  fold=(.009+.025*t)*math.sin(5*a+4*t*t)+.008*math.sin(9*a+3*t)
  x=-.22*(1-t)+.08*t-.26*t*t*side+(radx+fold)*math.cos(a);y=(rady+fold)*math.sin(a)
  vs.append((x,y,z))
fs=[]
for j in range(12):
 for k in range(N):a=j*N+k;b=j*N+(k+1)%N;fs.append((a,b,b+N,a+N))
robe=mesh('POET_DONKEY draped robe folds',vs,fs,bronze,'POET_DONKEY',True);sculpt.append(robe);uv(robe,.8)
mod=robe.modifiers.new('cast bronze hem','SOLIDIFY');mod.thickness=.035
mod=robe.modifiers.new('soft drapery','SUBSURF');mod.levels=2;mod.render_levels=2
for side in [-1,1]:
 tube('sleeve '+str(side),[(-.19,side*.23,2.33),(-.35,side*.31,2.08),(-.53,side*.29,1.90)],[.14,.135,.10])
 tube('hand '+str(side),[(-.53,side*.29,1.91),(-.66,side*.26,1.88)],[.07,.065])
 tube('boot '+str(side),[(.0,side*.48,1.11),(-.06,side*.51,.86),(-.28,side*.52,.80)],[.09,.085,.095])
hat=lathe('POET_DONKEY broad traveller hat',-.39,0,[(0,2.86),(.32,2.86),(.36,2.89),(.27,2.93),(.16,3.07),(.08,3.12),(0,3.13)],bronze,'POET_DONKEY');sculpt.append(hat)
for side in [-1,1]:tube('loose rein '+str(side),[(-.63,side*.26,1.9),(-.95,side*.27,1.4),(-1.20,side*.24,.92),(-1.57,side*.17,.49)],[.012]*4,N=8)
base=loft('cast rock foot',[(-1.85,0,.025,.06,.025),(-1.5,0,.08,.44,.08),(-.6,0,.10,.56,.10),(.5,0,.12,.54,.12),(1.12,0,.14,.42,.14),(1.28,0,.075,.08,.075)])
# Subdivide anatomical forms so intersections read as a continuous casting.
anatomy=[o for o in sculpt if any(k in o.name for k in ['torso','neck','face','muzzle','leg ','hoof'])]
bpy.ops.object.select_all(action='DESELECT')
for o in anatomy:o.select_set(True)
bpy.context.view_layer.objects.active=anatomy[0];bpy.ops.object.join();body=bpy.context.object
mod=body.modifiers.new('unified cast anatomy','REMESH');mod.mode='VOXEL';mod.voxel_size=.027;mod.use_smooth_shade=True;bpy.ops.object.modifier_apply(modifier=mod.name)
mod=body.modifiers.new('soft cast transitions','SMOOTH');mod.factor=.65;mod.iterations=3;bpy.ops.object.modifier_apply(modifier=mod.name);uv(body,.75)
sculpt=[o for o in C.objects if o.get('feature_id')=='POET_DONKEY']
# local rough ashlar tapered pedestal.
ped=[]
for row in range(3):
 z=.16+row*.28;w=3.25-row*.09;d=1.80-row*.065
 ped.append(box('POET_DONKEY base core '+str(row),(0,0,z),(w,d,.28),rock,'POET_DONKEY',.015))
 for side in [-1,1]:
  n=4 if row%2==0 else 3
  for i in range(n):
   cx=-w/2+(i+.5)*w/n
   ob=box('POET_DONKEY rough ashlar',(cx,side*(d/2+.015),z),(w/n-.018,.07,.255),rock,'POET_DONKEY',.023)
   # small planar variations leave mortar courses legible.
   # Rough-faced ashlar, with a dressed rim retained around each stone.
   bpy.context.view_layer.objects.active=ob;ob.select_set(True)
   mod=ob.modifiers.new('rough stone divisions','SUBSURF');mod.subdivision_type='SIMPLE';mod.levels=3;mod.render_levels=3
   tex=bpy.data.textures.get('FC rock relief') or bpy.data.textures.new('FC rock relief',type='CLOUDS');tex.noise_scale=.14;tex.noise_depth=2
   mod=ob.modifiers.new('rough split face','DISPLACE');mod.texture=tex;mod.texture_coords='GLOBAL';mod.strength=.05;mod.mid_level=.4
   ped.append(ob)
 for side in [-1,1]:
  for i in range(2):ped.append(box('POET_DONKEY side ashlar',(side*(w/2+.01),(-.25+i*.5)*d,z),(.065,d/2-.018,.255),rock,'POET_DONKEY',.023))
ped.append(box('POET_DONKEY dressed coping',(0,0,.93),(3.10,1.76,.15),pale,'POET_DONKEY',.012))
ped.append(box('POET_DONKEY inset nameplate',(0,-1.055,.47),(1.13,.035,.47),dark,'POET_DONKEY',.008))
f=bpy.data.curves.new('traditional inscription','FONT');f.body='驢背詩思';f.font=bpy.data.fonts.load('C:/Windows/Fonts/simkai.ttf');f.size=.237;f.align_x='CENTER';f.align_y='CENTER';f.extrude=.0008
txt=bpy.data.objects.new('POET_DONKEY 驢背詩思',f);C.objects.link(txt);txt.location=(0,-1.077,.47);txt.rotation_euler=(math.pi/2,0,0);f.materials.append(letter);txt['feature_id']='POET_DONKEY';ped.append(txt)
root=bpy.data.objects.new('POET_DONKEY photo placed landmark',None);C.objects.link(root);root.location=(-56,119,.03);root.rotation_euler.z=math.radians(-8);root['feature_id']='POET_DONKEY';root['source_photos']=[4467,4468];root['label']='驴背诗思';root['hidden_surfaces']='Simplified; no rear-face evidence';root['placement_confidence']='inferred from west wing and garden border, not GPS'
for ob in sculpt:ob.location.z+=1.005;ob.parent=root
for ob in ped:ob.parent=root
# building-front lawn pocket supporting the sculpture, with a low curved stone border.
island=[(-74,113),(-71,111.5),(-63,111),(-53,111.7),(-45,113),(-37,116),(-35,120),(-35,126),(-74,126)]
isle=prism('POET_DONKEY west frontage lawn',island,-.02,.055,soil,'POET_GARDEN');uv(isle,24)
curb('POET_GARDEN stone border',island,True)
# Shared existing tree meshes add context behind the statue, without remodelling the building.
sources=[o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='VEGETATION_V2' and o.name.startswith('V2 tree 00 ')]
for i,(x,y,sc) in enumerate([(-63,122,.95),(-49,123,.78),(-69,118,1.1),(-57.8,123,.95)]):
 for src in sources:
  ob=bpy.data.objects.new('POET_GARDEN context tree '+str(i)+' '+src.data.name,src.data);C.objects.link(ob);ob.location=(x,y,.055);ob.scale=(sc,sc,sc);ob.rotation_euler.z=i*1.8;ob['feature_id']='POET_GARDEN';ob['geometry_confidence']='inferred tree context';ob['source_photos']=[4467,4468]
# Low clipped mounds made from leaves; small-scale ground support stays natural.
for i,(cx,cy,rx,ry,rz) in enumerate([(-61.3,115.7,1.9,1.25,1.2),(-49,119,1.7,1.2,.95),(-66,121,1.4,1.1,1.1)]):
 leaves=[]
 for j in range(4200):
  a=rng.random()*math.tau;u=rng.random();r=math.sqrt(1-u*u);leaves.append((cx+rx*r*math.cos(a),cy+ry*r*math.sin(a),.055+rz*u,rng.random()*math.tau,rng.uniform(.07,.14)))
 ob=petal_mesh('POET_GARDEN clipped mound '+str(i),leaves,leafm,True);ob['feature_id']='POET_GARDEN'
# Context details kept bounded: two rock groups and low natural leaf mounds.
for i,(x,y,rx,ry) in enumerate([(-61,120,1.2,.8),(-50,120,1.0,.65),(-47,122,.8,.5)]):
 ob=box('POET_GARDEN landscape rock '+str(i),(x,y,.32),(rx,ry,.62),rock,'POET_GARDEN',.18)
# A slim drainage joint in the broad forecourt, based on the visible longitudinal line.
box('FORECOURT longitudinal drain joint',(0,110.6,.036),(148,.038,.012),dark)
for ob in list(C.objects):
 if ob.type=='MESH' and not ob.data.uv_layers:uv(ob,1)
for name,h in fixed.items():assert digest(bpy.data.objects[name])==h,name
def cam(name,loc,target,scale=None,lens=40):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1500
 if scale:d.type='ORTHO';d.ortho_scale=scale
 return o
views={
 'entry':cam('FC aligned entry',(AX,Y+19,10),(AX,Y-3,0),23),
 'entry-oblique':cam('FC entry oblique',(AX+13,Y+24,25),(AX,Y-3,0),27),
 'entry-top':cam('FC entry top',(AX,Y-3,55),(AX,Y-3,0),29),
 'plaza':cam('FC plaza photo4474',(16,112,7),(16,53,.2),None,25),
 'edge':cam('FC edge close',(56,89,2.4),(56,76,.06),None,40),
 'statue':cam('FC statue photo4468',(-51.7,110.5,3.5),(-56,119,2.2),None,48),
 'statue-side':cam('FC statue alternate',(-49.5,114,4.3),(-56,119,2.1),None,48),
 'overall':bpy.data.objects['FINAL landscape']}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.threads_mode='FIXED';s.render.threads=12;s.render.resolution_percentage=100
s.view_settings.exposure=.4
s.camera=views['overall'];s['forecourt_revision']='East aligned entrance, photo paving, segmented curb, Poet on donkey sculpture. Proportion reconstruction.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'forecourt-complete-v2.blend'))
(O/'build-info.json').write_text(json.dumps(dict(baseline_sha256=basehash,protected=fixed,entry_axis=AX,entry_line=Y,urn_centres=[[AX-3.5,PY],[AX+3.5,PY]],moved_north_stair=[0,-6,0],reference_photos=[4490,4491,4492,4474,4485,4483,4467,4468],cameras={k:v.name for k,v in views.items()},new_objects=len(C.objects)),indent=2))
if '--build-only' in sys.argv:print('FORECOURT_BUILD_ONLY_COMPLETE',flush=True);sys.exit()
keys=['entry','entry-top','statue','plaza'] if '--diagnostic' in sys.argv else list(views)
for k in keys:
 s.camera=views[k];s.render.resolution_x=1100;s.render.resolution_y=825;s.render.filepath=str(O/(('diagnostic-' if '--diagnostic' in sys.argv else 'after-')+k+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==basehash
print('FORECOURT_BUILD_COMPLETE',flush=True)
