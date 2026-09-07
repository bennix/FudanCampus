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
box('Continuous earth',0,70,-.48,2400,2400,.8,soil)
# Campus stretches north; east side is divided by a broad avenue.
box('East main avenue',101,65,.02,16,635,.18,asphalt)
for xx in [89.5,112.5]:box('Avenue sidewalk',xx,65,.13,5,635,.2,pathmat)
for xx in [87,92,110,115]:box('Avenue curb',xx,65,.23,.28,635,.35,trim,True)
for y in range(-230,380,11):box('Lane dash',101,y,.13,.17,5,.025,trim,True)
for y in [-155,4,156,278]:
 box('West east campus lane',-37,y,.02,238,5,.15,asphalt)
 for yy in [y-3.5,y+3.5]:box('Lane walk',-37,yy,.11,238,1.6,.13,pathmat)
for x in [-151,-76,-25,75]:box('North south campus lane',x,67,.045,4.5,445,.15,asphalt)
# Historical precinct, matching the low grey-roof foreground and central quadrangles.
current=COL['01 Historic courtyards']
for spec in [('South west hall',-18,-134,39,13),('South central hall',29,-134,42,14),('South east hall',66,-130,16,30),('Front west pavilion',-18,-155,31,12),('Front central pavilion',20,-157,27,13),('Front east wing',51,-163,13,28),('Small lodge',66,-153,15,10),('West long historic hall',-48,-104,13,45)]:building(*spec,2,True,white)
# broad foreground quadrangle
box('South quadrangle',20,-90,.04,101,57,.13,darksoil)
for x in [-31,71]:line('Quadrangle border',[(x,-120),(x,-58)],1.5,pathmat)
for y in [-120,-59]:line('Quadrangle border',[(-31,y),(71,y)],1.5,pathmat)
for spec in [('West courtyard wing',-37,-30,13,43),('Courtyard south hall',-17,-48,27,11),('East garden building',58,-33,12,34),('East garden south hall',58,-60,31,11),('Central villa west',-15,-23,13,15),('Central villa east',30,-20,12,16),('Central main hall',-4,17,30,17),('Main hall east annex',20,22,11,20),('West academic long hall',-45,31,12,43),('East pavilion',55,21,28,12),('North courtyard west',-19,65,12,20),('North courtyard east',26,65,15,21),('North court header',8,91,37,13)]:building(*spec,3 if spec[0]=='Central main hall' else 2,True,white)
# central garden paths and formal beds
for y in [-36,-7,39,76]:line('Formal transverse walk',[(-25,y),(46,y)],2.1,pathmat)
for x in [-24,9,45]:line('Formal longitudinal walk',[(x,-52),(x,82)],2,pathmat)
for y in [-23,13,57]:
 for x in [-7,28]:box('Formal garden lawn',x,y,.03,23,17,.12,darksoil)
# a low cloister around the eastern garden
for x in [43,76]:
 box('Cloister roof',x,-25,3.6,2.7,43,.3,roof,True)
 for y in range(-45,-3,4):box('Cloister column',x,y,1.8,.28,.28,3.6,white,True)
box('Cloister end',59.5,-45,3.6,35,2.7,.3,roof,True)
# fountain west of central precinct
cylinder('Fountain stone basin',-65,4,.42,5.1,.8,trim,64);cylinder('Fountain dark water',-65,4,.86,4.2,.05,water,64);cylinder('Fountain center',-65,4,1.0,.6,.5,stone)
# west campus flat-roof blocks, including distinctive twin tall slabs at front
current=COL['02 West academic blocks']
for x in [-113,-80]:
 building('Foreground twin slab',x,-153,15,52,7,False,white)
 for yy in [-174,-160,-146,-132]:
  box('Twin slab projecting stair pier',x+8.5,yy,10.8,3,3,21,stone,True)
 building('Twin slab end tower',x+8,-164,6,10,8,False,stone)
building('Twin slab linking bridge',-96.5,-150,20,9,4,False,white)
for spec in [('West L south bar',-140,-115,38,13,3),('West L north wing',-126,-92,12,36,3),('West free standing block',-163,-67,17,31,5),('West U long wing',-137,-14,12,51,4),('West U top bar',-118,6,36,12,4),('West U east wing',-99,-12,12,43,4),('Midwest tower',-84,31,14,24,6),('West teaching block',-158,55,16,36,5),('West lab',-126,67,25,13,4),('West broad laboratory',-128,108,36,16,5),('West pavilion',-91,110,18,24,4),('West back block',-156,149,20,37,6),('West cross block',-119,159,42,13,4),('Middle long teaching wing',-54,122,13,43,5),('Middle header',-29,142,40,14,4)]:building(*spec)
# northern dense parallel buildings
current=COL['03 North campus']
for row,y in enumerate([196,236,279,320]):
 for col,x in enumerate([-149,-114,-78]):
  building('North teaching %d %d'%(row,col),x,y,25 if col!=2 else 16,13 if col!=2 else 26,3+(row+col)%3,False,white if col%2==0 else stone)
for x in [-31,1,34,65]:
 for j,y in enumerate([181,225,269,315]):building('North linear residence',x,y,12,32,4 if j<3 else 3,j==3,white)
for y in [176,218,261,304,342]:line('Northern cross street',[(-171,y),(85,y)],3.5,asphalt)
for x in [-171,-96,-60,-12,19,51]:line('Northern walk',[(x,170),(x,345)],2,pathmat)
# separate east campus with towers, long slabs and open land on the front right
current=COL['04 East campus']
for spec in [('East front lone hall',162,-22,30,13,3),('East low wing',131,29,28,12,3),('East white crossbar',169,48,35,12,4),('East cross wing',184,57,12,29,4),('East boundary slab',223,18,15,43,5),('East tall tower one',221,95,17,15,11),('East tall tower two',244,99,13,17,13),('East tower podium',231,81,40,10,3),('East central midrise',160,124,18,21,8),('East central tall slab',146,153,14,21,13),('East tower attached wing',164,154,15,16,10),('East teaching south',143,93,34,14,4),('East north bar',163,206,49,12,6),('East parallel bar',184,229,54,12,5),('East north laboratory',143,244,29,15,6),('East north slim tower',125,266,12,17,9),('East rear residences',191,275,50,12,5),('East edge bar',219,249,13,40,5)]:building(*spec,False,white if 'tower' in spec[0] else stone)
for y in [63,184,292]:line('East campus access',[(115,y),(253,y)],4.5,asphalt)
line('East perimeter lane',[(253,2),(253,290)],4,asphalt)
for x,y in [(136,17),(198,112),(196,155),(213,199),(166,300),(208,306),(121,323)]:building('East small auxiliary',x,y,17,10,2,True,white)
# Tree canopy geometry shared in batched meshes to keep navigation light
current=COL['05 Landscape']
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=1);tmp=bpy.context.object;iv=[v.co.copy() for v in tmp.data.vertices];iff=[tuple(p.vertices) for p in tmp.data.polygons];bpy.data.objects.remove(tmp,do_unlink=True)
def tree(x,y,s=1):
 h=random.uniform(5.5,8)*s
 box('Trunk',x,y,h*.31,.42*s,.42*s,h*.62,bark,True)
 for k in range(5):
  r=random.uniform(1.55,2.45)*s;cx=x+random.uniform(-1.15,1.15)*s;cy=y+random.uniform(-1.15,1.15)*s;cz=h*.70+random.uniform(-.6,.8)*s
  m=random.choice(leaves);vs,fs=buffers.setdefault((current.name,m.name),([],[]));n=len(vs)
  vs.extend([(cx+v.x*r,cy+v.y*r,cz+v.z*r*1.12) for v in iv]);fs.extend([tuple(n+i for i in f) for f in iff])
for x in [85,117]:
 for y in range(-211,356,9):tree(x+random.uniform(-.5,.5),y,.85)
for x in [-171,-72,72]:
 for y in range(-116,345,13):tree(x,y,.8)
for y in [-118,-60,-37,-6,40,79]:
 for x in range(-23,70,16):tree(x,y,.72)
for y in [177,216,260,305,345]:
 for x in range(-163,82,15):tree(x,y,.65)
for x,y,w,d in [(-63,-90,9,40),(-111,48,21,15),(60,114,34,31),(190,80,22,11),(192,177,25,12),(128,212,12,22),(231,307,20,35)]:
 for i in range(15):tree(x+random.uniform(-w/2,w/2),y+random.uniform(-d/2,d/2),random.uniform(.65,1))
# benches and slender campus lamps
for y in range(-125,321,24):
 for x in [91,111]:
  box('Light pole',x,y,3.8,.15,.15,7.5,roof,True);box('Light head',x,y,7.6,.7,.38,.18,trim,True)
for y in [-110,-80,-36,0,44,76]:
 for x in [-28,48]:
  box('Garden bench seat',x,y,.65,2.7,.65,.18,stone,True)
  for dx in [-.9,.9]:box('Bench legs',x+dx,y,.3,.15,.5,.6,roof,True)
# Batched facade and foliage layers remain separated by material and district.
for (cname,mname),(v,f) in buffers.items():
 current=COL[cname];mesh(mname+' details',v,f,bpy.data.materials[mname])
current=COL['06 Cameras']
def camera(name,pos,target,lens):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);current.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.lens=lens;data.clip_end=5000;return ob
cam=camera('01 Reference aerial',(-205,-575,445),(5,65,0),48)
top=camera('02 Master plan',(25,65,900),(25,65,0),45);top.data.type='ORTHO';top.data.ortho_scale=690
camera('03 Historic precinct',(163,-265,173),(-4,-37,0),49)
import bmesh
for obj in bpy.data.objects:
 if obj.type=='MESH':
  bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
scene=bpy.context.scene;scene.camera=cam
world=bpy.data.worlds.new('Daylight sky') if not bpy.data.worlds else bpy.data.worlds[0];scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.77,.86,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65
ld=bpy.data.lights.new('Soft afternoon sun','SUN');lo=bpy.data.objects.new('Soft afternoon sun',ld);current.objects.link(lo);lo.rotation_euler=(math.radians(27),math.radians(-22),math.radians(-32));ld.energy=2.4;ld.angle=.10
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=2000;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG';scene.render.filepath=OUT+'/campus_aerial.png'
scene['Reference']='微信图片_20260907075718_9_139.jpg';scene['Reconstruction notes']='Approximate single-image reconstruction. No model platform, display case, indoor surroundings or model markers. Ground dimensions are inferred, not surveyed.'
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=OUT+'/FudanCampus.blend')
bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath='/Users/zhipingxu/FudanCampus/web/public/campus.glb',export_format='GLB',export_cameras=False,export_lights=False)
print('BUILD_COMPLETE',len(bpy.data.objects))
