"""Independent, evidence-linked Guanghua lawn study. Run with Blender 4.4.
All metres and elevations are provisional. Never writes existing campus assets.
"""
import bpy, math, json, random, sys, hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-lawn-survey-v1'
MODEL=OUT/'model'; RENDER=OUT/'renders'
MODEL.mkdir(exist_ok=True);RENDER.mkdir(exist_ok=True)
D=json.loads((OUT/'survey.json').read_text(encoding='utf-8'))
FEATURES={f['id']:f for f in D['features']}
random.seed(927)
bpy.ops.wm.read_factory_settings(use_empty=True)
scene=bpy.context.scene;scene.unit_settings.system='METRIC'
scene['survey_status']='PROPORTION STUDY / NOT MEASURED'
scene['scope']='Guanghua Building south enclosure, including west and east gardens'
scene['source_photos']='IMG_4312-IMG_4616; 305 originals remain unchanged'
COL={}
for n in ['01_Ground_and_circulation','02_Garden_structures','03_Furniture_and_landmarks','04_Vegetation_inferred','05_Building_context','90_Review']:
 c=bpy.data.collections.new(n);scene.collection.children.link(c);COL[n[:2]]=c
M={}
def mat(n,c,rough=.7,metal=0,alpha=1):
 m=bpy.data.materials.new(n);m.diffuse_color=(*c,alpha);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,alpha);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal;p.inputs['Alpha'].default_value=alpha
 if alpha<1:m.surface_render_method='DITHERED'
 M[n]=m;return m
for n,c in {'soil':(.28,.31,.18),'turf':(.37,.49,.19),'lawn':(.46,.58,.26),'road':(.22,.25,.25),'paving':(.52,.52,.46),'pale':(.76,.74,.64),'joint':(.37,.39,.36),'stone':(.61,.56,.43),'concrete':(.55,.56,.48),'dark':(.07,.10,.095),'wood':(.28,.18,.10),'benchwood':(.51,.29,.13),'rail':(.12,.23,.20),'bronze':(.18,.28,.23),'blue':(.04,.08,.31),'red':(.75,.19,.09),'yellow':(.82,.68,.25),'silver':(.55,.61,.60),'hedge':(.20,.34,.11),'redhedge':(.29,.24,.15),'flower':(.63,.12,.16),'trunk':(.24,.22,.15)}.items():mat(n,c,metal=.5 if n in ['rail','bronze','silver'] else 0)
for i,c in enumerate([(.18,.31,.13),(.24,.37,.15),(.29,.40,.18),(.34,.43,.20)]):mat('leaf'+str(i),c)
mat('glass',(.41,.66,.66),.19,.12,.63)
B={};ROOTS={};META={};current=('GROUND','01')
def begin(fid,col='02',refs=None,note=None):
 global current
 current=(fid,col)
 if fid not in META:
  f=FEATURES.get(fid,{})
  META[fid]=dict(feature_id=fid,label=f.get('name',fid),source_photos=refs or f.get('photos',[]),existence_confidence='confirmed' if f or refs else 'inferred',geometry_confidence='inferred',scale_status='provisional metres; no measured control',note=note or 'Position, dimensions and elevation inferred from photos and GPS.')
 elif note:META[fid]['note']=note
def add(v,f,m,part='geometry'):
 key=(*current,part,m);vs,fs=B.setdefault(key,([],[]));offset=len(vs);vs.extend(v);fs.extend([tuple(i+offset for i in face) for face in f])
def box(x,y,z,w,d,h,m,part='geometry'):
 v=[(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 add(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m,part)
def prism(poly,z0,z1,m,part='geometry'):
 if sum(poly[i][0]*poly[(i+1)%len(poly)][1]-poly[(i+1)%len(poly)][0]*poly[i][1] for i in range(len(poly)))<0:poly=list(reversed(poly))
 n=len(poly);v=[(x,y,z) for z in [z0,z1] for x,y in poly];f=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];add(v,f,m,part)
def beam(a,b,w,m,part='geometry',depth=None):
 a,b=Vector(a),Vector(b);n=(b-a).normalized();u=n.cross(Vector((0,0,1)))
 if u.length<.001:u=n.cross(Vector((0,1,0)))
 u.normalize();v=n.cross(u).normalized();u*=w/2;v*=(depth or w)/2
 pts=[tuple(p+su*u+sv*v) for p in [a,b] for su,sv in [(-1,-1),(1,-1),(1,1),(-1,1)]]
 add(pts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m,part)
def cyl(x,y,z,r,h,m,r2=None,steps=16,part='geometry'):
 r2=r if r2 is None else r2;v=[(x+rr*math.cos(i*2*math.pi/steps),y+rr*math.sin(i*2*math.pi/steps),zz) for zz,rr in [(z,r),(z+h,r2)] for i in range(steps)]
 add(v,[tuple(range(steps-1,-1,-1)),tuple(range(steps,steps*2))]+[(i,(i+1)%steps,(i+1)%steps+steps,i+steps) for i in range(steps)],m,part)
def blob(x,y,z,rx,ry,rz,m,part='geometry',n=12,k=6):
 v=[(x,y,z-rz)]+[(x+rx*math.sin(j*math.pi/k)*math.cos(i*2*math.pi/n),y+ry*math.sin(j*math.pi/k)*math.sin(i*2*math.pi/n),z-rz*math.cos(j*math.pi/k)) for j in range(1,k) for i in range(n)]+[(x,y,z+rz)];top=len(v)-1
 f=[(0,1+(i+1)%n,1+i) for i in range(n)]+[(top,1+(k-2)*n+i,1+(k-2)*n+(i+1)%n) for i in range(n)]
 for j in range(k-2):
  for i in range(n):a=1+j*n+i;b=1+j*n+(i+1)%n;f.append((a,b,b+n,a+n))
 add(v,f,m,part)
def curve(pts,s=5):
 if len(pts)<3:return pts
 out=[];p=[pts[0]]+pts+[pts[-1]]
 for i in range(1,len(p)-2):
  a,b,c,d=map(Vector,p[i-1:i+3])
  for j in range(s):t=j/s;out.append(tuple(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t**3)))
 return out+[tuple(pts[-1])]
def edges(pts,w):
 left=[];right=[]
 for i,p in enumerate(pts):
  a=Vector(pts[max(0,i-1)]);b=Vector(pts[min(len(pts)-1,i+1)]);d=(b-a).normalized();n=Vector((-d.y,d.x))*w/2;v=Vector(p);left.append(tuple(v+n));right.append(tuple(v-n))
 return left,right
def ribbon(pts,w,z0,z1,m,part='path',smooth=False):
 pts=curve(pts) if smooth else pts;l,r=edges(pts,w);prism(l+list(reversed(r)),z0,z1,m,part);return l,r
def rail(pts,z,h=1.05,m='rail',cross=False):
 for a,b in zip(pts,pts[1:]):
  a,b=Vector(a),Vector(b);n=max(1,math.ceil((b-a).length/2.3))
  for j in range(n):
   p=a+(b-a)*j/n;q=a+(b-a)*(j+1)/n
   beam((*p,z),(*p,z+h),.12 if cross else .065,m,'rail-post')
   for zz in [.40,h]:beam((*p,z+zz),(*q,z+zz),.10 if cross else .055,m,'rail-bar')
   if cross:
    beam((*p,z+.2),(*q,z+h-.12),.09,m,'rail-cross');beam((*p,z+h-.12),(*q,z+.2),.09,m,'rail-cross')
 beam((*pts[-1],z),(*pts[-1],z+h),.12 if cross else .065,m,'rail-post')
def stair(a,b,w,z0,z1,n=6):
 a,b=Vector(a),Vector(b);d=(b-a)/n;u=Vector((-d.y,d.x)).normalized()*w/2
 for i in range(n):p=a+d*i;q=p+d;prism([tuple(p-u),tuple(q-u),tuple(q+u),tuple(p+u)],z0-.08,z0+(z1-z0)*(i+1)/n,'pale','steps')
def hedge(pts,w=0.9,z=0,h=.7,red=False):ribbon(pts,w,z,z+h,'redhedge' if red else 'hedge','hedge',smooth=len(pts)>3 and pts[0]!=pts[-1])
def bench(x,y,z=0,angle=0,length=1.9,blue=False):
 def p(a,b,c):t=math.radians(angle);return (x+a*math.cos(t)-b*math.sin(t),y+a*math.sin(t)+b*math.cos(t),z+c)
 wood='blue' if blue else 'benchwood'
 for xx in [-length*.38,length*.38]:
  beam(p(xx,-.23,0),p(xx,-.23,.45),.06,'rail','bench');beam(p(xx,.20,0),p(xx,.22,1.05),.06,'rail','bench');beam(p(xx,-.26,.43),p(xx,.25,.43),.055,'rail','bench')
 for yy in [-.20,-.07,.06,.19]:beam(p(-length/2,yy,.46),p(length/2,yy,.46),.105,wood,'bench',.045)
 for zz in [.68,.83,.98]:beam(p(-length/2,.25,zz),p(length/2,.25,zz),.105,wood,'bench',.045)
def skylight(x,y,z=0,size=4):
 box(x,y,z+.34,size,size,.68,'concrete','skylight-base')
 for dy in [-1,1]:
  for zz in [.62,.76,.9]:box(x,y+dy*size/2,z+zz,size,.10,.065,'rail','vent-louvre')
 for dx in [-1,1]:
  for zz in [.62,.76,.9]:box(x+dx*size/2,y,z+zz,.10,size,.065,'rail','vent-louvre')
 z+=.96;s=size/2;v=[(x-s,y-s,z),(x+s,y-s,z),(x+s,y+s,z),(x-s,y+s,z),(x,y,z+size*.25)]
 add(v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],'glass','skylight-glass')
 for i in range(4):beam(v[i],v[4],.055,'silver','skylight-frame');beam(v[i],v[(i+1)%4],.065,'rail','skylight-frame')
def flush():
 for (fid,col,part,m),(v,f) in B.items():
  if not v:continue
  if fid not in ROOTS:
   root=bpy.data.objects.new(fid+' | '+META[fid]['label'],None);COL[col].objects.link(root);ROOTS[fid]=root
   for k,val in META[fid].items():root[k]=val
  mesh=bpy.data.meshes.new(fid+'_'+part);mesh.from_pydata(v,[],f);mesh.materials.append(M[m]);mesh.update();mesh.validate()
  ob=bpy.data.objects.new(fid+'__'+part+'__'+m,mesh);COL[col].objects.link(ob);ob.parent=ROOTS[fid]
  for k,val in META[fid].items():ob[k]=val
 B.clear()

# Stage 01: placement and circulation. Baseline snapshots are hashed before any output.
protected=json.loads((ROOT/'assets/protected-buildings.json').read_text(encoding='utf-8'))['files']
baseline={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in protected if (ROOT/p).exists()}
for p in ['web/public/models/buildings/27.glb','assets/buildings/27.blend','scripts/build_campus.py','web/public/buildings.json']:
 if (ROOT/p).exists():baseline[p]=hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
(MODEL/'baseline-sha256.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
begin('GROUND','01',refs=[4474],note='Single landscape slab. Surface holes are cut for photographed openings; no underground plan is invented.')
box(14.5,57,-2.05,189,112,4,'turf','terrain')
begin('BOUNDARY','01',refs=[4312,4400,4523,4556])
box(-85,57,-.15,10,134,.3,'road','west-road');box(114,57,-.15,10,134,.3,'road','east-road');box(14.5,-4,-.145,209,10,.3,'road','south-road')
for x in [-78.5,107.5]:box(x,56,.07,3,111,.14,'paving','sidewalk');box(x+(1.6 if x<0 else -1.6),56,.14,.20,111,.28,'pale','curb')
box(14.5,3,.06,189,3,.12,'paving','south-sidewalk')
for x in [-81,110]:box(x,56,.015,.1,126,.03,'yellow','road-edge')
begin('LAWN','01')
lawn=[(-25,16),(70,16),(70,80),(69,84),(66,87),(61,88),(-16,88),(-21,87),(-24,84),(-25,80)]
prism(lawn,-.03,.03,'lawn','turf')
ribbon(lawn+[lawn[0]],.25,.02,.16,'pale','lawn-edging')
begin('PLAZA','01')
prism([(-80,87),(-24,87),(-18,89),(64,89),(70,87),(109,87),(109,113),(-80,113)],-.025,.06,'paving','plaza')
for x in range(-78,110,5):box(x,100,.067,.19,26,.018,'pale','grid-band')
for y in range(88,114,5):box(14.5,y,.069,189,.19,.018,'pale','grid-band')
for path_index,p in enumerate(D['paths']):
 fid='WPATH' if p['id'].startswith(('west-garden','ding','west-terrace','west-main')) else 'EPATH' if p['id'].startswith(('east-garden','east-terrace','east-main')) else 'EDGE_PATHS'
 begin(fid,'01',refs=p['photos']);smooth=len(p['points'])>3
 dz=path_index*.003
 ribbon(p['points'],p['width']+.25,-.015,.07+dz,'pale','curb-'+p['id'],smooth)
 ribbon(p['points'],p['width'],.069+dz,.085+dz,'paving' if 'inner' in p['id'] else 'stone',p['id'],smooth)
flush()
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL/'guanghua-lawn-stage01-layout.blend'))

# Stage 02: independently evidenced garden groups.
begin('WTERR')
prism([(-74,43),(-51,43),(-51,48),(-54,48),(-54,54),(-51,54),(-51,71),(-74,71)],-.02,1.2,'concrete','raised-platform')
prism([(-73.8,43.2),(-51.2,43.2),(-51.2,47.8),(-54.2,47.8),(-54.2,54.2),(-51.2,54.2),(-51.2,70.8),(-73.8,70.8)],1.2,1.23,'stone','stone-platform')
stair((-46,51),(-48,51),3,0,.6,4);box(-49,51,.3,2,3,.6,'pale','stair-landing');stair((-50,51),(-54,51),3,.6,1.2,4)
rail([(-74,43),(-51,43),(-51,47.8)],1.23,cross=True,m='wood');rail([(-51,54.2),(-51,71),(-74,71)],1.23,cross=True,m='wood')
for yy in [49.4,52.6]:
 railpoints=[(-46,yy,0),(-48,yy,.6),(-50,yy,.6),(-52,yy,.9),(-54,yy,1.2)]
 for x,y,z in railpoints:beam((x,y,z),(x,y,z+1.05),.12,'wood','stair-rail')
 for a,b in zip(railpoints,railpoints[1:]):
  beam((a[0],a[1],a[2]+1.05),(b[0],b[1],b[2]+1.05),.10,'wood','stair-rail')
  beam((a[0],a[1],a[2]+.2),(b[0],b[1],b[2]+.94),.09,'wood','stair-rail-cross')
  beam((a[0],a[1],a[2]+.94),(b[0],b[1],b[2]+.2),.09,'wood','stair-rail-cross')
for x,y in [(-63,50),(-63,64)]:
 box(x,y,1.37,6.5,6.5,.28,'pale','skylight-planter');skylight(x,y,1.51,4.0)
 hedge([(x-3,y-3),(x+3,y-3),(x+3,y+3),(x-3,y+3),(x-3,y-3)],.85,1.51,.65)
hedge([(-73,44),(-73,70)],1.5,1.2,.85,True);bench(-70,57,1.23,90);bench(-58,69,1.23,0)
for y in [44,47.7,54.3,58,61.5,69.5]:box(-62,y,1.245,20,.10,.015,'joint','paving-bands')
for x in [-71,-67,-59,-55]:box(x,57,1.247,.1,27,.015,'joint','paving-bands')
for fid,x,y,size in [('WSKY1',-36,43,4),('WSKY2',-55,83,4.1),('WSKY2',-59.6,83,4.1),('ESKY',83,45,3.7)]:begin(fid);skylight(x,y,0,size)

holes=[]
for fid,x,y in [('WOPEN',-32,81),('EOPEN',79,78),('WOPEN_S',-32,48),('EOPEN_S',78,49.5)]:
 begin(fid,note='Visible railed stair opening; depth/step count provisional, lower interior omitted.')
 w,d=3.2,4.2;poly=[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)];holes.append((fid,poly))
 for xx in [x-w/2-.15,x+w/2+.15]:box(xx,y,-.55,.3,d+.6,1.8,'concrete','opening-wall')
 box(x,y+d/2+.15,-.55,w,.3,1.8,'concrete','opening-wall');box(x,y-d/2+.15,-1.25,w,.30,.35,'dark','occluded-interior-limit')
 stair((x,y-d/2),(x,y+d/2),w-.3,-1.5,.07,10)
 rail([(x-w/2-.25,y-d/2),(x-w/2-.25,y+d/2+.3),(x+w/2+.25,y+d/2+.3),(x+w/2+.25,y-d/2)],.12)
 beam((x,y-d/2,-1.1),(x,y+d/2,.98),.045,'silver','stair-handrail')
 hedge([(x-w/2-1,y-d/2-.5),(x-w/2-1,y+d/2+1),(x+w/2+1,y+d/2+1)],.75,0,.63)
 for i in range(3):box(x,y+d/2+1.3+i*.65,.06,1.0,.43,.12,'paving','stepping-stones')

# Western garage mouths, with short visible descending aprons only.
for fid,cy,closed in [('WB1',48,False),('WB2',70,True)]:
 begin(fid,note='Garage facade, retaining walls and short apron only. Underground extent unknown.')
 holes.append((fid,[(-80.1,cy-3),(-71.8,cy-3),(-71.8,cy+3),(-80.1,cy+3)]))
 v=[(-80,cy-3,0),(-72,cy-3,-1.0),(-72,cy+3,-1.0),(-80,cy+3,0)];add(v,[(0,1,2,3)],'paving','sloped-apron')
 for yy in [cy-3.15,cy+3.15]:box(-75.6,yy,-.05,8.8,.30,1.9,'concrete','retaining-wall')
 box(-72,cy,1.35,.7,7.1,.65,'concrete','door-lintel');box(-72.1,cy,1.86,.17,6.6,.73,'blue','garage-sign')
 for yy in [cy-3.25,cy+3.25]:box(-72,yy,.16,.7,.5,2.5,'concrete','door-jamb')
 if closed:
  for yy in [cy-2.23,cy-.75,cy+.75,cy+2.23]:box(-72.05,yy,-.05,.10,1.45,1.95,'pale','closed-door')
 else:box(-71.9,cy,-.05,.08,5.95,1.95,'dark','unknown-dark-interior')
 hedge([(-71.5,cy-3.3),(-71.5,cy+3.3)],1.2,1.4,.9,True)

# Small glass enclosures have photographed frames, simplified sloping roofs.
for fid,x,y,w,d in [('WGLASS',-57,7,4,6.5),('WGLASS2',-72,28,3.8,5.5)]:
 begin(fid)
 box(x,y,.12,w+.3,d+.3,.24,'concrete','glass-plinth')
 corners=[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)]
 ztops=[2.6,2.6,1.45,1.45];v=[(*p,.24) for p in corners]+[(*p,z) for p,z in zip(corners,ztops)]
 add(v,[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],'glass','glass-enclosure')
 for i in range(4):beam(v[i],v[i+4],.08,'rail','glass-frame');beam(v[i+4],v[(i+1)%4+4],.08,'rail','glass-frame')
 for yy in [y-d/4,y,y+d/4]:
  zz=2.6-(yy-(y-d/2))/d*1.15
  for xx in [x-w/2,x+w/2]:beam((xx,yy,.24),(xx,yy,zz),.065,'rail','glass-frame')
  beam((x-w/2,yy,zz),(x+w/2,yy,zz),.065,'rail','glass-frame')
 if fid=='WGLASS':
  box(-66,7,.34,14,5,.68,'concrete','low-vent-deck');box(-66,7,.72,14.3,5.3,.12,'wood','deck')
  for z in [.19,.34,.49]:box(-66,4.46,z,13.5,.12,.08,'rail','deck-louvre')

begin('ETERR')
# Broad road-facing stair climbs westwards, then staggered upper landings.
stair((106.5,54),(102,54),6,0,.9,6)
prism([(97,48),(102,48),(102,61),(97,61)],-.02,.9,'concrete','first-landing');box(99.5,54.5,.92,5,13,.04,'stone','first-paving')
stair((97,51),(94.5,51),3,.9,1.5,4)
prism([(87,47),(94.5,47),(94.5,61),(91,65),(85,62),(85,53)],-.02,1.5,'concrete','upper-platform')
prism([(87.2,47.2),(94.3,47.2),(94.3,60.8),(90.9,64.7),(85.2,61.8),(85.2,53)],1.5,1.54,'stone','upper-paving')
stair((80.5,54),(85.2,54),2.2,0,1.5,9)
for pts,z in [([(97,48),(99,47),(102,48)],.9),([(87,47),(86,49),(85,51)],1.5),([(85,57),(85,61),(89,64),(93,62)],1.5),([(101,56.5),(101,60),(98,61)],.9)]:
 ribbon(curve(pts),.45,0,z+.48,'concrete','curved-planter-wall');hedge(pts,1.15,z+.4,.75,True)
bench(90,61.6,1.54,0);bench(86.2,58.2,1.54,90);bench(99.6,58.3,.95,0)

begin('ERAMP',note='Curve, depth and span inferred; photographed vine pergola and retaining walls. No garage interior.')
ramp=curve([(109,19),(102,21),(97,25),(94,31),(94,39)],6);left,right=edges(ramp,6.7);holes.append(('ERAMP',left+list(reversed(right))))
zs=[-.02-2.2*i/(len(ramp)-1) for i in range(len(ramp))]
v=[(p[0],p[1],zs[i]) for side in [left,right] for i,p in enumerate(side)];n=len(ramp)
add(v,[(i,i+n,i+n+1,i+1) for i in range(n-1)],'paving','visible-curved-ramp')
for side in [left,right]:
 for i in range(n-1):
  p,q=side[i],side[i+1];beam((*p,zs[i]+.6),(*q,zs[i+1]+.6),.24,'concrete','ramp-retaining-wall',1.25)
for i in range(4,n-1,4):
 for side in [left,right]:
  x,y=side[i];beam((x,y,zs[i]+.65),(x,y,3.15),.19,'wood','pergola-post')
 beam((*left[i],3.15),(*right[i],3.15),.22,'wood','pergola-beam')
for i in range(3,n-1):beam((*left[i],3.30),(*right[i],3.30),.12,'wood','pergola-slats')
for side in [left,right]:
 for i in range(4,n-1):beam((*side[i],3.15),(*side[i+1],3.15),.22,'wood','pergola-edge')
for i in range(6,n-1,3):
 for side in [left,right]:x,y=side[i];blob(x,y,3.45,1.3,1.0,.4,'leaf1','vines')
box(94,39,-.8,6.6,.1,2.7,'dark','unobserved-interior-limit')

# Landmarks are recognizable proxies; sculptural ornament is intentionally unresolved.
begin('DING','03',note='Square bronze ding form confirmed in 4348. Relief, inscriptions and exact profile omitted.')
for z,w,h,m in [(.16,4.6,.32,'joint'),(.51,3.4,.38,'pale'),(.80,1.95,.20,'bronze')]:box(-35,27,z,w,w,h,m,'tiered-plinth')
for dx in [-.53,.53]:
 for dy in [-.53,.53]:box(-35+dx,27+dy,1.21,.22,.24,.68,'bronze','ding-leg')
v=[(-35+sx*r,27+sy*r,z) for z,r in [(1.52,.62),(2.25,.86)] for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]];add(v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'bronze','square-ding-body')
box(-35,27,2.30,1.82,1.82,.12,'bronze','rim')
for xx in [-35.58,-34.42]:
 for yy in [26.73,27.27]:box(xx,yy,2.65,.14,.14,.6,'bronze','handle')
 box(xx,27,2.93,.14,.68,.14,'bronze','handle')
begin('SIGN','03',note='FUDAN lettering and heart-seat arrangement confirmed; font and dimensions approximate.')
box(26,10,.20,9.0,1.5,.4,'blue','sign-base');bench(29.5,10,.42,0,1.3,True)
flush()
font=bpy.data.curves.new('FUDAN approximate lettering','FONT');font.body='FUDAN';font.size=1.35;font.extrude=.10;font.align_x='LEFT'
ob=bpy.data.objects.new('SIGN__FUDAN',font);COL['03'].objects.link(ob);ob.location=(22.1,9.6,.42);ob.rotation_euler=(math.pi/2,0,0);font.materials.append(M['blue']);ob.parent=ROOTS['SIGN'];ob['feature_id']='SIGN';ob['source_photos']=[4603,4604,4606];ob['geometry_confidence']='inferred'
begin('SIGN','03')
heart=[]
for i in range(65):
 t=2*math.pi*i/64;xx=16*math.sin(t)**3;zz=13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t);heart.append((29.4+xx*.095,10.35,1.8+zz*.095))
for a,b in zip(heart,heart[1:]):beam(a,b,.18,'red','heart-frame',.20)
begin('FLOWER','03',note='Two inclined circular metal rims confirmed. Floral planting represented as approximate masses.')
for r in [1.5,1.08]:
 pts=[(38+r*math.cos(t),4+math.sin(t)*r*.65,1.25+math.sin(t)*r*.65) for t in [i*2*math.pi/64 for i in range(65)]]
 for a,b in zip(pts,pts[1:]):beam(a,b,.08,'pale','inclined-ring')
blob(38,4,1.25,1.42,.85,.85,'hedge','green-backdrop')
for i in range(22):t=i*2*math.pi/22;blob(38+2*math.cos(t),4+1.5*math.sin(t),.27,.23,.23,.25,'flower','flowers')
begin('FURNITURE','03',refs=[4340,4360,4455,4491,4547,4556,4566,4603],note='Furniture types observed. Counts and exact placements are a first-pass selection, not a full inventory.')
for x,y,z,a in [(-32,32,0,90),(-33,58,0,90),(77,62,0,-90),(77,29,0,-90),(-45,75,0,20),(-69,10,.8,0),(12,5,0,0),(52,5,0,0),(105,64,0,90)]:bench(x,y,z,a)
for x in [-30,-23,69,76]:
 box(x,89,.45,2,2,.90,'concrete','urn-plinth');box(x,89,.96,2.15,2.15,.12,'pale','plinth-cap');cyl(x,89,1.02,.5,.32,'pale',.35);cyl(x,89,1.34,.45,.5,'pale',.92);cyl(x,89,1.84,.95,.08,'pale')
 blob(x,89,2.04,.82,.82,.33,'hedge','urn-planting')
 for i in range(8):t=i*math.pi/4;blob(x+.65*math.cos(t),89+.65*math.sin(t),2.12,.16,.16,.15,'flower','urn-flowers')
for x,y in [(-84,100),(-81,100),(-78,100),(9,2),(13,2),(17,2),(103,99),(107,99),(111,99)]:cyl(x,y,.04,.40,.10,'concrete');blob(x,y,.52,.38,.38,.38,'pale','stone-bollard')
for i in range(12):
 t=2*math.pi*i/12;a=(104+1.45*math.cos(t),37+1.45*math.sin(t),.5);b=(104+1.45*math.cos(t+math.pi/6),37+1.45*math.sin(t+math.pi/6),.5);beam(a,b,.38,'benchwood','tree-ring-seat',.08)

# Vegetation establishes zones only; no claim of exact tree inventory.
begin('VEGETATION','04',refs=[4312,4338,4378,4474,4505,4556],note='Representative canopy masses. Tree locations/counts/species and all heights remain inferred.')
treepts=[(-75,y) for y in [10,21,35,80,91]]+[(-44,y) for y in [9,18,34,63,76,88]]+[(87,y) for y in [9,16,34,71,85]]+[(105,y) for y in [8,45,69,82,96]]+[(x,6) for x in [-29,-17,-4,9,51,65,80,95]]+[(-67,78),(-54,34),(-39,52),(97,74),(99,88),(104,37)]
for j,(x,y) in enumerate(treepts):
 h=random.uniform(7,11);r=random.uniform(2.8,4.5);cyl(x,y,0,.20,h*.7,'trunk',.11,10,'tree-trunk')
 for i in range(3):t=i*2*math.pi/3+.5;beam((x,y,h*.4),(x+1.5*math.cos(t),y+1.5*math.sin(t),h*.75),.13,'trunk','branch')
 blob(x,y,h*.78,r,r,h*.35,'leaf'+str(j%4),'canopy')
for x,y,r in [(-39,29,1.2),(-38,36,1.4),(-45,67,1.4),(79,40,1.2),(84,60,1.3),(97,68,1.5),(-60,77,1.4),(-36,76,1.3)]:blob(x,y,r*.75,r,r,r*.75,'hedge','rounded-shrub')
hedge([(-72,4),(-40,4)],1.3,0,.8,True);hedge([(47,4),(67,4)],1.3,0,.8,True);hedge([(-76,75),(-76,92)],1.3,0,1,True)
flush()

# True holes are subtracted from the ground slab rather than painted dark squares.
ground=next(o for o in bpy.data.objects if o.name.startswith('GROUND__terrain'))
for fid,poly in holes:
 begin('CUT_'+fid,'90');prism(poly,-4.2,4.5,'dark','cutter');flush();cut=next(o for o in bpy.data.objects if o.name.startswith('CUT_'+fid+'__'))
 bpy.context.view_layer.objects.active=ground;mod=ground.modifiers.new('Opening '+fid,'BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.ops.object.modifier_apply(modifier=mod.name)
 bpy.data.objects.remove(cut,do_unlink=True);bpy.data.objects.remove(ROOTS.pop('CUT_'+fid),do_unlink=True);META.pop('CUT_'+fid)

# Existing Guanghua geometry is a separate, scaled contextual reference only.
sys.path.insert(0,str(ROOT/'scripts'))
from guanghua_geometry import build_guanghua
begin('CONTEXT_GUANGHUA','05',refs=[4315,4474],note='Existing repo facade reused as context at provisional scale 1.5. Not a newly surveyed building; no accepted asset changed.')
context=bpy.data.objects.new('CONTEXT_GUANGHUA | existing building reference',None);COL['05'].objects.link(context)
for k,val in META['CONTEXT_GUANGHUA'].items():context[k]=val
context.location=(20,153,0);context.scale=(1.5,1.5,1.5)
def context_mat(n,c,rough=.6):return mat(n,c,rough)
def context_mesh(n,v,f,m):
 me=bpy.data.meshes.new(n);me.from_pydata(v,[],f);me.materials.append(m);me.update();o=bpy.data.objects.new(n,me);COL['05'].objects.link(o);o.parent=context;o['feature_id']='CONTEXT_GUANGHUA';o['geometry_confidence']='inferred existing context';return o
build_guanghua(0,0,context_mat,context_mesh)

# Lighting and fixed review cameras.
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
world=bpy.data.worlds.new('Overcast daylight');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(.75,.81,.85,1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.75;scene.world=world
light=bpy.data.lights.new('Daylight','SUN');light.energy=2.0;light.angle=.15;o=bpy.data.objects.new('Daylight',light);COL['90'].objects.link(o);o.rotation_euler=(math.radians(28),math.radians(-22),math.radians(-35))
scene.view_settings.view_transform='AgX'
def camera(name,loc,target,ortho=None,lens=40):
 data=bpy.data.cameras.new(name);data.lens=lens;ob=bpy.data.objects.new(name,data);COL['90'].objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
 if ortho:data.type='ORTHO';data.ortho_scale=ortho
 return ob
cams={
 '01-overhead':camera('01-overhead',(14.5,63,270),(14.5,63,0),220),
 '02-aerial':camera('02-aerial',(245,-218,233),(14,80,40),340),
 '03-west-garden':camera('03-west-garden',(-15,18,34),(-55,57,0),70),
 '04-east-garden':camera('04-east-garden',(147,7,42),(91,48,0),65),
 '05-north-photo-4474':camera('05-north-photo-4474',(-2.5,116,4.7),(15,33,0),None,24),
}
scene.camera=cams['02-aerial'];scene.render.resolution_x=1500;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
# Set useful native opening view.
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=245;area.spaces.active.region_3d.view_location=(15,60,0)
manifest={fid:{**meta,'objects':[o.name for o in bpy.data.objects if o.get('feature_id')==fid]} for fid,meta in META.items()}
(MODEL/'component-evidence.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(MODEL/'guanghua-lawn-v1.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.type in ['MESH','FONT','EMPTY'] and not o.name.startswith('CUT_'):o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(MODEL/'guanghua-lawn-v1.glb'),export_format='GLB',use_selection=True,export_extras=True,export_cameras=False,export_lights=False,export_apply=True)
# A second export omits the contextual building but preserves editable landscape units.
for o in COL['05'].objects:o.select_set(False)
bpy.ops.export_scene.gltf(filepath=str(MODEL/'guanghua-lawn-site-only.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
changed=[p for p,h in baseline.items() if hashlib.sha256((ROOT/p).read_bytes()).hexdigest()!=h]
assert not changed,changed
(MODEL/'build-summary.json').write_text(json.dumps(dict(stage='02 evidence-limited site model',features=len(FEATURES),components=len(manifest),mesh_objects=sum(o.type=='MESH' for o in bpy.data.objects),vertices=sum(len(o.data.vertices) for o in bpy.data.objects if o.type=='MESH'),baseline_unchanged=True,protected_files_checked=len(baseline),scale='inferred, not measured',opening_cutouts=[h[0] for h in holes],views=list(cams)),indent=2),encoding='utf-8')
for name in ['01-overhead','02-aerial','03-west-garden','04-east-garden','05-north-photo-4474']:
 scene.camera=cams[name];scene.render.resolution_x=1400 if name in ['01-overhead','02-aerial'] else 1100;scene.render.resolution_y=1080 if name=='01-overhead' else 850
 # Overhead and local diagnostics reveal garden geometry with canopy masses hidden.
 COL['04'].hide_render=name in ['01-overhead','03-west-garden','04-east-garden'];COL['05'].hide_render=name in ['01-overhead','03-west-garden','04-east-garden']
 scene.render.filepath=str(RENDER/(name+'.png'));bpy.ops.render.render(write_still=True)
print('GUANGHUA LAWN STUDY COMPLETE',str(MODEL))
