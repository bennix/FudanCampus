import bpy, math, random, os, json
from mathutils import Vector
random.seed(21)
OUT='/Users/zhipingxu/FudanCampus/output'
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
 if c.name != 'Collection': bpy.data.collections.remove(c)
COL={}
for name in ['00 Terrain and roads','01 Historic courtyards','02 West academic blocks','03 North campus','04 East campus','05 Landscape','06 Cameras']:
 c=bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); COL[name]=c
current=COL['00 Terrain and roads']
def mat(name,color,rough=.75):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
 return m
stone=mat('Warm ivory plaster',(0.66,.65,.58)); white=mat('Pale limestone',(0.79,.8,.75)); trim=mat('Window frames and coping',(.85,.85,.78)); roof=mat('Charcoal grey roof tiles',(.19,.225,.22)); flat=mat('Weathered flat roof',(.48,.52,.50)); glass=mat('Dark blue grey glazing',(.105,.18,.21),.28); asphalt=mat('Road asphalt',(.30,.32,.30)); pathmat=mat('Walkway stone',(.60,.59,.52)); soil=mat('Dry olive lawn',(.32,.355,.23)); darksoil=mat('Courtyard lawn',(.38,.39,.28)); bark=mat('Tree bark',(.22,.18,.13)); leaves=[mat('Canopy %d'%i,c) for i,c in enumerate([(.16,.25,.12),(.23,.31,.16),(.29,.35,.20),(.19,.29,.19),(.32,.36,.22)])]; water=mat('Still fountain water',(.15,.28,.28),.18)
# Subtle real-world surface grain, no display platform.
for m,scale,strength in [(soil,65,.16),(darksoil,50,.13),(roof,140,.18),(asphalt,100,.12),(stone,95,.08)]:
 nt=m.node_tree; noise=nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=scale
 bump=nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=strength; bump.inputs['Distance'].default_value=.12
 nt.links.new(noise.outputs['Fac'],bump.inputs['Height']); nt.links.new(bump.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
buffers={}
def mesh(name,v,f,m):
 me=bpy.data.meshes.new(name); me.from_pydata(v,[],f); me.materials.append(m); ob=bpy.data.objects.new(name,me); current.objects.link(ob); return ob
def box(name,x,y,z,w,d,h,m,batch=False):
 v=[(x+a*w/2,y+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]; f=[(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]
 if batch:
  key=(current.name,m.name); vs,fs=buffers.setdefault(key,([],[])); n=len(vs);vs.extend(v);fs.extend([tuple(n+i for i in face) for face in f]);return
 return mesh(name,v,f,m)
def line(name,points,width,m,z=.21):
 for a,b in zip(points,points[1:]):
  dx=b[0]-a[0];dy=b[1]-a[1];ob=box(name,(a[0]+b[0])/2,(a[1]+b[1])/2,z+random.uniform(0,.006),width,math.hypot(dx,dy),.14,m);angle=-math.atan2(dx,dy); cx=(a[0]+b[0])/2; cy=(a[1]+b[1])/2
  for vert in ob.data.vertices:
   vx=vert.co.x-cx;vy=vert.co.y-cy;vert.co.x=cx+vx*math.cos(angle)-vy*math.sin(angle);vert.co.y=cy+vx*math.sin(angle)+vy*math.cos(angle)
def cylinder(name,x,y,z,r,depth,m,n=24):
 v=[(x+r*math.cos(i*2*math.pi/n),y+r*math.sin(i*2*math.pi/n),z+zz*depth/2) for zz in [-1,1] for i in range(n)];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)];return mesh(name,v,f,m)
def building(name,x,y,w,d,floors=3,pitched=False,m=None):
 h=floors*3.25+random.uniform(0,.06); m=m or stone
 ob=box(name,x,y,h/2+.25,w,d,h,m); ob['floors']=floors;ob['source']='Single photograph; approximate relative dimensions'
 box(name+' foundation',x,y,.35,w+.65,d+.65,.7,pathmat,True)
 for zz in [1.0,h-.2]:box('Cornice',x,y,zz,w+.35,d+.35,.25,trim,True)
 for side in [-1,1]:
  nx=max(2,int(w/3.1));ny=max(2,int(d/3.2))
  for floor in range(floors):
   z=2.05+3.25*floor
   for i in range(nx):
    xx=x-w/2+(i+.5)*w/nx
    box('Frame',xx,y+side*(d/2+.06),z,1.55,.16,1.94,trim,True);box('Window',xx,y+side*(d/2+.16),z,1.14,.08,1.55,glass,True)
   for j in range(ny):
    yy=y-d/2+(j+.5)*d/ny
    box('Frame',x+side*(w/2+.06),yy,z,.16,1.55,1.94,trim,True);box('Window',x+side*(w/2+.16),yy,z,.08,1.14,1.55,glass,True)
 if pitched:
  e=h+.45;rise=min(w,d)*.32;wx=w/2+.65;dy=d/2+.65
  if w>=d:
   v=[(x-wx,y-dy,e),(x+wx,y-dy,e),(x+wx,y+dy,e),(x-wx,y+dy,e),(x-wx+dy*.65,y,e+rise),(x+wx-dy*.65,y,e+rise)]
   f=[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)]
   box('Roof ridge',x,y,e+rise,w-dy*1.3,.32,.27,roof,True)
  else:
   v=[(x-wx,y-dy,e),(x+wx,y-dy,e),(x+wx,y+dy,e),(x-wx,y+dy,e),(x,y-dy+wx*.65,e+rise),(x,y+dy-wx*.65,e+rise)];f=[(0,1,4),(1,2,5,4),(2,3,5),(3,0,4,5)]
  mesh(name+' hipped tiled roof',v,f,roof)
 else:
  box('Flat roof',x,y,h+.3,w+.4,d+.4,.35,flat,True)
  for xx in [x-w/2,x+w/2]:box('Parapet',xx,y,h+.8,.3,d,1,white,True)
  for yy in [y-d/2,y+d/2]:box('Parapet',x,yy,h+.8,w,.3,1,white,True)
  box('Stair housing',x+w*.24,y+d*.15,h+1.6,3.7,4.5,2.5,m,True)
  for i in range(max(1,int(w/12))):box('Roof vent',x-w*.3+i*10,y-d*.22,h+.9,1.4,1.4,1.1,trim,True)
 # entrance doors and shallow stair
 box('Entrance',x,y-d/2-.19,1.6,2.3,.13,2.7,glass,True)
 for i in range(3):box('Entry step',x,y-d/2-.5-i*.32,.14*(3-i),3.6,1.2,.2,pathmat,True)
 return ob
# Map coordinates: supplied image displayed at 1888 x 1334.
ROOT='/Users/zhipingxu/FudanCampus'
S=.8
records=json.load(open(ROOT+'/references/buildings.json'))
def xy(x,y):return ((x-1200)*S,(1000-y)*S)
def mapbox(name,x,y,w,d,m,z=.08,h=.14):
 xx,yy=xy(x,y);return box(name,xx,yy,z,w*S,d*S,h,m)
def mapline(name,points,width,m,z=.24):line(name,[xy(*p) for p in points],width*S,m,z)
box('Continuous earth',0,300,-.5,3200,3200,.8,soil)
# Surrounding streets follow the map, including the northwest extension.
mapline('邯郸路',[(640,1005),(1830,1005)],24,asphalt)
mapline('国定路',[(1555,1005),(1543,807),(1537,600),(1527,541)],18,asphalt)
mapline('国权路',[(533,981),(694,989),(893,997)],15,asphalt)
mapline('北侧边界道路',[(595,88),(1028,459),(1081,571),(1392,570),(1527,541),(1820,541)],10,asphalt)
mapline('北区西侧道路',[(694,104),(549,268),(539,331),(578,460),(641,533),(683,555),(704,694)],8,asphalt)
# Main campus road network from the map.
for y,points in [(620,[(706,620),(1518,615)]),(765,[(755,789),(1008,765),(1271,765),(1450,765)]),(934,[(818,942),(1109,934),(1272,934),(1442,934)]),(990,[(995,990),(1518,990)])]:mapline('Campus east west road',points,7,pathmat)
for x,points in [(970,[(970,620),(971,741),(977,771),(1010,845),(1006,937),(1018,990)]),(1035,[(1035,619),(1040,759)]),(1128,[(1128,686),(1128,927)]),(1172,[(1174,679),(1174,985)]),(1270,[(1257,620),(1270,768),(1270,987)]),(1440,[(1441,615),(1442,985)]),(1518,[(1518,618),(1518,987)])]:mapline('Campus north south road',points,7,pathmat,z=.255)
for pts in [[(780,638),(791,758),(815,792),(822,911)],[(834,696),(964,696)],[(1010,697),(1250,697)],[(858,758),(855,880),(858,930)],[(838,843),(1017,839)],[(826,898),(997,883)],[(1190,893),(1260,893)],[(1283,892),(1429,892)],[(1460,851),(1514,851)],[(1562,682),(1805,682)],[(1566,747),(1805,741)],[(1571,791),(1804,790)],[(1669,803),(1669,979)],[(1680,923),(1750,923)]]:mapline('Pedestrian connection',pts,4,pathmat,z=.27)
for y in [242,274,303,328,449,479,509,538,570]:mapline('North residence path',[(574 if y<350 else 696,y),(805 if y<350 else 832,y)],3,pathmat)
mapline('North residence outer loop',[(660,212),(899,384),(820,434),(837,558),(697,570),(598,468),(558,356),(600,281),(660,212)],5,pathmat)
# Landscaped precincts, sports courts and recognisable map landmarks.
mapbox('国旗坪',1358,813,151,76,darksoil)
mapbox('中央草坪',1149,810,31,77,darksoil)
mapbox('东区草坪',1726,832,121,65,darksoil)
mapbox('新闻学院庭院',1693,947,96,64,darksoil)
mapbox('北区中心绿地',704,365,37,63,darksoil)
sports=mat('Sports court blue',(.20,.43,.53));track=mat('Court surround',(.55,.53,.38))
mapbox('室外球场',1372,960,134,56,sports,z=.12)
for x in [1323,1361,1400,1430]:
 for y in [946,974]:
  mapline('Court lines',[(x-12,y-9),(x+12,y-9),(x+12,y+9),(x-12,y+9),(x-12,y-9)],.45,trim,z=.3)
  mapline('Court centre',[(x,y-9),(x,y+9)],.4,trim,z=.31)
mapbox('篮球场',1495,875,33,24,sports)
mapbox('停车场',1421,644,52,54,asphalt)
for x in range(1400,1442,7):mapline('Parking bay',[(x,624),(x,640)],.35,trim,z=.36)
# Gardens are landmarks rather than invented buildings.
pois=[('57','国旗坪',1358,813),('58','毛主席像',1150,917),('62','望道园',1098,954),('68','曦园',1230,957),('49G','燕园',950,964),('65','复旦正门',1150,997),('28','国定路校门',1538,704),('69','国顺路校门',1268,997),('54','国权路校门',995,997),('76','室外球场',1368,960)]
for name,x,y in [('曦园',1230,957),('燕园',960,958),('望道园',1098,957)]:
 xx,yy=xy(x,y);cylinder(name+' garden',xx,yy,.18,18,.12,darksoil,48)
xx,yy=xy(1243,960);cylinder('曦园水池',xx,yy,.3,8,.2,water,48)
xx,yy=xy(1150,917);box('Statue plinth',xx,yy,1.5,4,4,3,stone);box('Statue abstract body',xx,yy,5,1.5,1.2,4,white);cylinder('Statue head',xx,yy,7.6,.65,1.1,white)
import sys
sys.path.insert(0,ROOT+'/scripts')
from gate_geometry import build_gate
gx0,gy0=xy(1150,992)
build_gate(gx0,gy0,mat,mesh,current,bpy)
for name,x,y in [('Guoding gate',1538,704)]:
 xx,yy=xy(x,y)
 for dx in [-9,9]:box(name+' pier',xx+dx,yy,2.5,1,1,5,stone)
 box(name+' lintel',xx,yy,5.1,19,1,.55,white)
# Buildings assembled as joined-looking wings, with one semantic label per building.
labels=[]
for r in records:
 x,y=xy(r['x'],r['y']);w=r['w']*S;d=r['d']*S;floors=r['floors'];form=r['form'];id=r['id']
 current=COL['03 North campus'] if r['y']<585 else COL['04 East campus'] if r['x']>1545 else COL['01 Historic courtyards'] if r['x']<1040 and r['y']>770 else COL['02 West academic blocks']
 before=set(bpy.data.objects);counts={k:len(v[0]) for k,v in buffers.items()}
 def part(suffix,dx,dy,pw,pd,f=floors,hip=False):
  ob=building(r['name']+suffix,x+dx,y+dy,pw,pd,f,hip,white if form in ['hip','tower'] else stone)
  ob['building_id']=id;ob['building_name']=r['name'];ob['map_source']=r['source'];return ob
 if id=='51':
  from office_geometry import build_office
  build_office(x,y,mat,mesh,current,bpy)
 elif id=='55':
  from chemistry_geometry import build_chemistry
  build_chemistry(x,y,mat,mesh,current,bpy)
 elif id=='20':
  from physics_geometry import build_physics
  build_physics(x,y,mat,mesh,current,bpy)
 elif form=='yifu':
  import sys
  sys.path.insert(0,ROOT+'/scripts')
  from yifu_geometry import build_yifu
  build_yifu(x,y,box,mat,mesh,current,bpy)
 elif form=='yifu_science':
  import sys
  sys.path.insert(0,ROOT+'/scripts')
  from yifu_science_geometry import build_yifu_science
  build_yifu_science(x,y,box,mat,mesh,current,bpy)
 elif form=='library':
  import sys
  sys.path.insert(0,ROOT+'/scripts')
  from library_geometry import build_library
  build_library(x,y,mat,mesh,current,bpy)
 elif form=='tower':
  import sys
  sys.path.insert(0,ROOT+'/scripts')
  from guanghua_geometry import build_guanghua
  build_guanghua(x,y,mat,mesh)
 elif form in ['H','U']:
  part(' · 西翼',-w*.4,0,w*.2,d)
  part(' · 东翼',w*.4,0,w*.2,d)
  part(' · 横楼',0,d*.36 if form=='U' else 0,w*.61,d*.28)
 else:part('',0,0,w,d,hip=form=='hip')
 # Rotate all components together about the traced footprint centre.
 angle=math.radians(r['angle']);co=math.cos(angle);si=math.sin(angle)
 def rot(v):
  vx=v[0]-x;vy=v[1]-y;return (x+vx*co-vy*si,y+vx*si+vy*co,v[2])
 if angle:
  for ob in set(bpy.data.objects)-before:
   if ob.type=='MESH':
    for v in ob.data.vertices:v.co=rot(v.co)
  for k,(vs,fs) in buffers.items():
   start=counts.get(k,0)
   for i in range(start,len(vs)):vs[i]=rot(vs[i])
 height=r.get('height',floors*3.25+(min(w,d)*.32 if form=='hip' else 3))
 labels.append(dict(id=id,name=r['name'],position=[x,height+2,-y],source=r['source'],category='building',mapPixel=[r['x'],r['y']]))
# Landscape: avoid building footprints, including rotated residential blocks.
current=COL['05 Landscape']
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1);tmp=bpy.context.object;iv=[v.co.copy() for v in tmp.data.vertices];iff=[tuple(p.vertices) for p in tmp.data.polygons];bpy.data.objects.remove(tmp,do_unlink=True)
def tree(x,y,s=1):
 h=random.uniform(5.5,8)*s;box('Trunk',x,y,h*.31,.42*s,.42*s,h*.62,bark,True)
 for k in range(5):
  r=random.uniform(1.55,2.45)*s;cx=x+random.uniform(-1.15,1.15)*s;cy=y+random.uniform(-1.15,1.15)*s;cz=h*.70+random.uniform(-.6,.8)*s
  m=random.choice(leaves);vs,fs=buffers.setdefault((current.name,m.name),([],[]));n=len(vs);vs.extend([(cx+v.x*r,cy+v.y*r,cz+v.z*r*1.12) for v in iv]);fs.extend([tuple(n+i for i in f) for f in iff])
def free(px,py):
 if abs(px-1150)<12 and py>958:return False
 # Keep the photographed approach lawns clear in front of both entrances.
 for r in records:
  if r['id'] in ['14','16','27','56'] and abs(px-r['x'])<r['w']*.7 and r['y']<py<r['y']+r['d']/2+28:return False
 for r in records:
  a=math.radians(r['angle']);dx=(px-r['x'])*S;dy=-(py-r['y'])*S;ux=dx*math.cos(a)+dy*math.sin(a);uy=-dx*math.sin(a)+dy*math.cos(a)
  if abs(ux)<r['w']*S/2+4 and abs(uy)<r['d']*S/2+4:return False
 return True
for py in [610,755,929,983]:
 for px in range(716,1517,14):
  if free(px,py):tree(*xy(px,py),.9)
for px in [1261,1434,1526,1551]:
 for py in range(605,989,14):
  if free(px,py):tree(*xy(px,py),.9)
for i in range(600):
 px=random.uniform(720,1800);py=random.uniform(634,977)
 if free(px,py) and not(1280<px<1440 and 774<py<850) and not(1302<px<1440 and py>937):tree(*xy(px,py),random.uniform(.65,.9))
for py in range(248,560,13):
 px=558+(py-248)*.4
 if free(px,py):tree(*xy(px,py),.9)
for (cname,mname),(v,f) in buffers.items():current=COL[cname];mesh(mname+' details',v,f,bpy.data.materials[mname])
for id,name,px,py in pois:
 x,y=xy(px,py);labels.append(dict(id=id,name=name,position=[x,10 if id=='65' else 4,-y],source='map',category='landmark',mapPixel=[px,py]))
json.dump(dict(version='map-v17-chemistry-east',coordinateSystem='Three.js Y-up, north = -Z',buildings=labels),open(ROOT+'/web/public/buildings.json','w'),ensure_ascii=False,indent=2)
current=COL['06 Cameras']
def camera(name,pos,target,lens):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);current.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=5000;return ob
cam=camera('01 Map corrected aerial',(-650,-880,950),(-20,260,0),46)
top=camera('02 Map aligned plan',(-20,320,1300),(-20,320,0),45);top.data.type='ORTHO';top.data.ortho_scale=1120
camera('03 Main campus',(-380,-460,500),(30,160,0),46)
yx,yy=xy(1050,681)
yifu_cam=camera('04 Yifu photo detail',(yx+31,yy-69,9),(yx,yy,11),49)
sx,sy=xy(940,752)
science_cam=camera('05 Yifu science photo detail',(sx+18,sy-45,8),(sx,sy,14),26)
gx,gy=xy(1364,719)
guanghua_cam=camera('06 Guanghua photo detail',(gx,gy-104,7),(gx,gy,35),24)
lx,ly=xy(1079,899)
library_cam=camera('07 Science library entrance',(lx+3,ly-22,3.5),(lx+3,ly+8.7,5.5),26)
px,py=xy(1150,747)
physics_cam=camera('09 Physics photo',(px-8,py-29,7),(px,py,9),18)
cx,cy=xy(1078,799)
chemistry_cam=camera('10 Chemistry entrance',(cx+50.8,cy-2,3),(cx+32.8,cy,6),22)
ox,oy=xy(993,918)
office_cam=camera('11 Office entrance',(ox-4,oy-32,5),(ox,oy-3,8),20)
gate_cam=camera('08 Fudan gate photo',(gx0-6,gy0-34,3),(gx0,gy0,4),34)
gate_rear_cam=camera('12 Fudan gate rear',(gx0+2,gy0+22,3),(gx0,gy0,4.1),25)
# Merge detailed facade pieces by material to keep the local viewer responsive.
for bid in ['14','16']:
 groups={}
 for obj in list(bpy.data.objects):
  if obj.type=='MESH' and obj.get('building_id')==bid:
   groups.setdefault(obj.data.materials[0].name,[]).append(obj)
 for material,objects in groups.items():
  vertices=[];faces=[]
  for obj in objects:
   offset=len(vertices);vertices.extend([tuple(obj.matrix_world @ v.co) for v in obj.data.vertices]);faces.extend([tuple(offset+i for i in p.vertices) for p in obj.data.polygons])
  current=COL['02 West academic blocks'];ob=mesh(('逸夫科技楼' if bid=='14' else '逸夫楼')+' · '+material,vertices,faces,bpy.data.materials[material]);ob['building_id']=bid;ob['building_name']='逸夫科技楼' if bid=='14' else '逸夫楼';ob['source']='user facade photographs'
  for obj in objects:bpy.data.objects.remove(obj,do_unlink=True)
import bmesh
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
scene=bpy.context.scene;scene.camera=cam
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.77,.86,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
ld=bpy.data.lights.new('Soft afternoon sun','SUN');lo=bpy.data.objects.new('Soft afternoon sun',ld);current.objects.link(lo);lo.rotation_euler=(math.radians(27),math.radians(-22),math.radians(-32));ld.energy=2.4;ld.angle=.10
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=2200;scene.render.resolution_y=1600;scene.render.resolution_percentage=75
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=OUT+'/campus_aerial.png'
scene['Reference']='User supplied Fudan Campus Map Northern Part plus photograph';scene['Reconstruction notes']='Map-traced simplified footprints and map-era names. Estimated heights and facades; not a surveyed model.'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/FudanCampus.blend')
from export_modular import export_modular
export_modular()
# Optional legacy combined export; the website uses campus-manifest.json.
if os.environ.get('EXPORT_LEGACY') == '1':
 bpy.ops.export_scene.gltf(filepath=ROOT+'/web/public/campus.glb',export_format='GLB',export_cameras=False,export_lights=False,export_extras=True)
render_views=[('gate-rear',gate_rear_cam,'fudan_gate_rear.png',1500,1050),('office',office_cam,'office_detail.png',1400,1000),('chemistry',chemistry_cam,'chemistry_detail.png',1400,1000),('physics',physics_cam,'physics_detail.png',1500,1000),('aerial',cam,'campus_aerial.png',1650,1200),('plan',top,'campus_plan.png',1650,1200),('yifu',yifu_cam,'yifu_detail.png',1500,1000),('science',science_cam,'yifu_science_detail.png',1500,1000),('guanghua',guanghua_cam,'guanghua_detail.png',1800,1300),('library',library_cam,'science_library_detail.png',1500,1100),('gate',gate_cam,'fudan_gate_detail.png',1500,1050)]
selected=os.environ.get('RENDER_VIEWS','').split(',')
for key,view,filename,rx,ry in render_views:
 if selected!=[''] and key not in selected:continue
 scene.camera=view;scene.render.resolution_x=rx;scene.render.resolution_y=ry;scene.render.resolution_percentage=100;scene.render.filepath=OUT+'/'+filename;bpy.ops.render.render(write_still=True)
print('BUILD_COMPLETE',len(records),'building labels',len(bpy.data.objects),'objects')
