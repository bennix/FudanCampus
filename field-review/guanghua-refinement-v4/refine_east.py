import bpy,math,json,ast,hashlib,sys,bmesh
from pathlib import Path
from mathutils import Vector
R=Path.cwd(); O=R/'field-review/guanghua-refinement-v4'; stage=sys.argv[-1]
base=R/'field-review/guanghua-complete-v3/guanghua-complete-v3.blend'
bpy.ops.wm.open_mainfile(filepath=str(base));s=bpy.context.scene
M={m.name:m for m in bpy.data.materials};B={};ROOTS={};META={};COL={'02':bpy.data.collections['02_Garden_structures']};current=('ETERR','02')
tree=ast.parse((R/'scripts/build_guanghua_lawn.py').read_text(encoding='utf-8'))
names={'add','box','prism','beam','cyl','curve','edges','ribbon','rail','bench','flush','mat'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<helpers>','exec'))
M['turf']=M['FIN_garden_grass'];M['rail']=M['metal-green'];M['benchwood']=M['seat-orange']
# Segment strips avoid unstable tessellation of a long concave n-gon.
def ribbon(pts,w,z0,z1,m,part='path',smooth=False):
 pts=curve(pts) if smooth else pts;l,r=edges(pts,w)
 for i in range(len(pts)-1):prism([l[i],r[i],r[i+1],l[i+1]],z0,z1,m,part)
 return l,r
DX=-6.697882438088101

def begin(fid,refs):
 global current
 current=(fid,'02');META[fid]=dict(feature_id=fid,label=fid,source_photos=refs,existence_confidence='confirmed',geometry_confidence='inferred',scale_status='proportional metres; not measured',revision='v4',note='Manual multi-view constraints. No photogrammetry. Invisible geometry unresolved.')

def cam(name,loc,target,scale=None,lens=32):
 d=bpy.data.cameras.new('V4 '+name);o=bpy.data.objects.new('V4 '+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1000
 if scale:d.type='ORTHO';d.ortho_scale=scale
 return o
views={
 'east-top':cam('east-top',(85,50,140),(85,50,0),52),
 'east-entry':cam('east-entry',(109+DX,53.5,2.15),(95+DX,53.5,1.5),None,25),
 'east-overview':cam('east-overview',(117,26,33),(85,51,0),48),
 'east-exit':cam('east-exit',(88+DX,47.8,3.9),(78+DX,45,0.7),None,29)}
s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=True;s.render.resolution_x=960;s.render.resolution_y=760;s.render.resolution_percentage=100
for o in bpy.data.objects:
 if o.get('feature_id') in {'VEGETATION','E_TREES'}:o.hide_render=True

def render(prefix):
 for k,c in views.items():
  s.camera=c;s.render.filepath=str(O/f'{prefix}-{k}.png');bpy.ops.render.render(write_still=True)
if stage=='before':
 render('before');sys.exit()
# Replace only terrace and its circulation; existing ramp and four openings untouched at this stage.
for o in list(bpy.data.objects):
 if o.get('feature_id') in {'ETERR','EPATH'}:bpy.data.objects.remove(o,do_unlink=True)

def stairs(a,b,w,z0,z1,n,part):
 a,b=Vector(a),Vector(b);d=(b-a)/n;u=Vector((-d.y,d.x)).normalized()*w/2
 for i in range(n):
  p=a+d*i;q=p+d;z=z0+(z1-z0)*(i+1)/n
  prism([tuple(p-u),tuple(q-u),tuple(q+u),tuple(p+u)],-.02,z,'warm-granite',part)
  beam((*tuple(p-u),z),(*tuple(p+u),z),.055,'grey-granite',part+'-nose',.035)

def platform(poly,z,part,material='warm-impressed-paving'):
 prism(poly,-.02,z-.045,'aged-wall',part+'-support');prism(poly,z-.045,z,material,part+'-surface')

def planted(pts,z,width=.7,height=.55,red=False):
 pts=curve(pts,10);ribbon(pts,width,-.02,z+.35,'warm-granite','wall');ribbon(pts,width+.045,z+.35,z+.40,'grey-granite','coping');ribbon(pts,width*.94,z+.4,z+.4+height,'leaf-bronze' if red else 'leaf-green','hedge')

begin('ETERR',[4556,4561,4564,4565,4568])
stairs((106.5,53.5),(104.05,53.5),5.6,.06,.97,7,'road-flight-7')
platform([(104.05,50.7),(104.05,56.3),(98.8,56.3),(98.8,50.7)],.97,'lower','dark-paving')
for x in [99.6,101.2,102.8]:
 for y in [51.6,53.2,54.8]:box(x,y,.978,.48,.48,.016,'pale-inlay','square-inlay')
stairs((98.8,53.5),(96.64,53.5),3.1,.97,1.75,6,'middle-flight-6')
mid=[(96.64,51.95),(96.64,56.3),(95.6,57.9),(92,57.9),(90.3,56.8),(90.3,51.95)]
platform(mid,1.75,'middle')
stairs((93,51.95),(93,50.9),4.5,1.75,2.17,3,'upper-turn-flight-3')
upper=[(95.25,50.9),(95.25,47.2),(93.8,45.4),(90.3,44.7),(87.5,45.4),(86,47.1),(86,49.9),(88,50.9)]
platform(upper,2.17,'upper')
stairs((94,58.95),(94,57.9),1.8,1.33,1.75,3,'north-exit-3-inferred-count')
stairs((84.95,47.8),(86,47.8),1.8,1.75,2.17,3,'west-exit-3-inferred-count')
planted([(104,50.3),(102,49.5),(99,50.2)],.97,1.0)
planted([(104,56.8),(102,57.9),(99,56.8)],.97,1.0)
planted([(98.4,50.2),(97.4,48.7),(95.4,47.0)],1.75,1.05,.6,True)
planted([(96.6,56.5),(95.8,58.1),(95.1,58.25)],1.75,.65,.45)
planted([(92.9,58.1),(91.2,57.6),(90,56.6),(90,52.1)],1.75,.65,.48)
planted([(95.65,50.5),(95.6,47.2),(94,45),(90.3,44.3),(87,45.0),(85.7,46.8)],2.17,.65,.55,True)
planted([(85.7,48.95),(86.7,50.5),(88.9,51.1)],2.17,.65,.55,True)
planted([(104,48),(101,46.5),(97,45.5)],.2,1.3,.5)
bench(91.3,55.7,1.75,90,2.1);bench(92,45.4,2.17,180,2.1);bench(88,46.1,2.17,145,2.1)
# Visible stone courses at the outer wall, approximate course size; no added hidden facade.
for z in [.35,.75,1.15,1.55,1.95]:
 beam((95.85,47,z),(97.8,49.7,z),.018,'joint-dark','outer-wall-courses',.012)
begin('EPATH',[4496,4507,4513,4565,4568,4574,4581,4585])
route=curve([(73,85.5),(85,83),(89.8,74),(87.6,66.5),(79.8,61),(80.7,55),(82,53),(83,46),(85,39),(81,33),(83.7,25),(92,18),(106.5,15.5)],10)
ribbon(route,1.65,.025,.095,'pink-path','main-curve')
for pts in [[(81,33),(78,29),(73,27)],[(83.2,42),(79.8,39.5),(76,39),(73,40)],[(83,66),(78,67),(73,68)]]:
 pts[0]=min(route,key=lambda p:(Vector(p)-Vector(pts[0])).length);ribbon(curve(pts,10),1.5,.026,.095,'pink-path','lawn-connection')
# Broad mound below exits. Width tapers to zero only at ground endpoint; no narrow triangular spine.
def graded(pts,zs,width,part,shoulder):
 l,r=edges(pts,width);ol,orr=edges(pts,width+shoulder*2)
 for i in range(len(pts)-1):
  top=[(*l[i],zs[i]),(*r[i],zs[i]),(*r[i+1],zs[i+1]),(*l[i+1],zs[i+1])]
  add([(x,y,-.03) for x,y,z in top]+top,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'pink-path',part)
  for inner,outer in [(l,ol),(r,orr)]:
   top=[(*inner[i],zs[i]-.015),(*outer[i],.008),(*outer[i+1],.008),(*inner[i+1],zs[i+1]-.015)]
   add([(x,y,-.04) for x,y,z in top]+top,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'turf',part+'-terrain')
pts=curve([(84.95,47.8),(82.8,47.8),(81.6,45.5),(82.1,43)],10)
# Last point joins existing main path precisely.
pts[-1]=min(route,key=lambda p:(Vector(p)-Vector(pts[-1])).length)
graded(pts,[1.75+(0.095-1.75)*i/(len(pts)-1) for i in range(len(pts))],1.8,'west-exit-path',2.7)
pts=curve([(94,58.95),(94,62),(91.6,66),(89.1,70.4)],10);pts[-1]=min(route,key=lambda p:(Vector(p)-Vector(pts[-1])).length)
graded(pts,[1.33+(0.095-1.33)*i/(len(pts)-1) for i in range(len(pts))],1.8,'north-exit-path',2.7)
flush()
terrain=[]
for ob in bpy.data.objects:
 if ob.get('revision')=='v4' and '-terrain' in ob.name:
  ob.data.calc_loop_triangles()
  for tri in ob.data.loop_triangles:
   if tri.normal.z>.01:terrain.append([ob.data.vertices[i].co.copy() for i in tri.vertices])
def ground_at(x,y):
 z=.07
 for a,b,c in terrain:
  den=(b.y-c.y)*(a.x-c.x)+(c.x-b.x)*(a.y-c.y)
  if abs(den)<1e-8:continue
  u=((b.y-c.y)*(x-c.x)+(c.x-b.x)*(y-c.y))/den;v=((c.y-a.y)*(x-c.x)+(a.x-c.x)*(y-c.y))/den;w=1-u-v
  if min(u,v,w)>=-1e-5:z=max(z,u*a.z+v*b.z+w*c.z)
 return z
for ob in bpy.data.objects:
 if ob.get('revision')=='v4' and any(p in ob.name for p in ['__main-curve__','__lawn-connection__']):
  for v in ob.data.vertices:
   if v.co.z>.06:v.co.z=max(v.co.z,ground_at(v.co.x,v.co.y)+.025)
# Helpers use east local coordinates; apply the established overall east registration once.
for fid,root in ROOTS.items():root.location.x=DX
for o in bpy.data.objects:
 if o.type=='MESH' and o.get('revision')=='v4':
  bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
  uv=o.data.uv_layers.new(name='V4_surface')
  for p in o.data.polygons:
   ax=max(range(3),key=lambda k:abs(p.normal[k])); axes=[k for k in range(3) if k!=ax]
   for li in p.loop_indices:
    co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co[axes[0]]*.30,co[axes[1]]*.30)
  o['uncertainty']='Exit counts and terrain grades inferred; observed two separate exits confirmed. Positions and widths approximate.'
s.camera=views['east-overview'];s['refinement_v4']='East terrace topology iteration; LAWN preserved.'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage01-east.blend'))
render('after')
print('V4_EAST_DONE')


