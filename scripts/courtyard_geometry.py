"""Deterministic branch-and-leaf courtyard planting; no solid canopy blobs."""
import math, random
import bpy
from mathutils import Vector

def build_courtyard(xy, material):
 rng=random.Random(23307130129)
 bark=material('庭院树干纹理色',(.17,.115,.065))
 foliage=[material('庭院灌木叶片深绿',(.045,.115,.025)),
          material('庭院灌木叶片中绿',(.10,.22,.045)),
          material('庭院灌木叶片嫩绿',(.19,.30,.075)),
          material('庭院灌木叶片秋色',(.29,.23,.065))]
 buffers={}
 def add(mat,verts,faces):
  vs,fs=buffers.setdefault(mat.name,([],[]));base=len(vs)
  vs.extend(tuple(v) for v in verts);fs.extend(tuple(base+i for i in f) for f in faces)
 def branch(a,b,r1,r2):
  direction=(b-a).normalized();u=direction.cross(Vector((0,1,0))).normalized();v=direction.cross(u)
  verts=[p+(u*math.cos(i*math.tau/8)+v*math.sin(i*math.tau/8))*r for p,r in [(a,r1),(b,r2)] for i in range(8)]
  add(bark,verts,[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)])
 def leaf(p,size):
  theta=rng.uniform(0,math.tau);tilt=rng.uniform(-.55,.75)
  u=Vector((math.cos(theta),math.sin(theta),tilt)).normalized()*size
  v=Vector((-math.sin(theta),math.cos(theta),rng.uniform(-.35,.35)))*size*.38
  add(rng.choices(foliage,[3,5,3,1])[0],[p-u,p+v,p+Vector((0,0,size*.12)),p+u,p-v],[(0,1,2),(1,3,2),(3,4,2),(4,0,2)])
 def spray(p,r,density):
  for _ in range(density):
   q=Vector((rng.gauss(0,r*.45),rng.gauss(0,r*.45),rng.gauss(0,r*.28)))
   if q.length<r:leaf(p+q,rng.uniform(.055,.105))
 for px,py,h,density in [(165,198,5.6,.45),(176,202,6.3,.6),(149,200,4.7,.8)]:
  base=xy((px,py));base.z=.15
  trunk=[base+Vector((.09*math.sin(i),.075*math.cos(i),h*i/6)) for i in range(7)]
  for i in range(6):branch(trunk[i],trunk[i+1],.12*(1-i/7),.12*(1-(i+1)/7))
  for i in range(14):
   z=h*(.28+.045*i);theta=i*2.399+rng.uniform(-.3,.3)
   a=base+Vector((0,0,z));length=h*(.28-.009*i)
   b=a+Vector((math.cos(theta)*length,math.sin(theta)*length,length*.43))
   mid=a.lerp(b,.48)+Vector((0,0,-.12));branch(a,mid,.047,.025);branch(mid,b,.025,.014)
   for j in range(3):
    phi=theta+(j-1)*.8;start=a.lerp(b,.5+j*.2)
    end=start+Vector((math.cos(phi)*.65,math.sin(phi)*.65,.45+rng.random()*.22))
    branch(start,end,.017,.006)
    for k in range(3):
     tip=end+Vector((rng.uniform(-.4,.4),rng.uniform(-.4,.4),rng.uniform(.15,.45)))
     branch(end,tip,.006,.002)
     if rng.random()<density:spray(tip,.42,65)
 for px,py,r in [(162,202,1.3),(165,207,1),(177,196,.9),(150,211,.65)]:
  p=xy((px,py));p.z=r*.68
  for _ in range(round(2400*r*r)):
   theta=rng.uniform(0,math.tau);z=rng.uniform(-.8,1);rad=r*math.sqrt(max(0,1-z*z))*rng.uniform(.72,1)
   q=p+Vector((math.cos(theta)*rad,math.sin(theta)*rad,z*r*.72))
   leaf(q,rng.uniform(.045,.08))
  for i in range(7):
   theta=i*math.tau/7;branch(xy((px,py))+Vector((0,0,.1)),p+Vector((math.cos(theta)*r*.65,math.sin(theta)*r*.65,.2)),.035,.005)
 for name,(verts,faces) in buffers.items():
  mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(bpy.data.materials[name])
  obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj['campusVegetation']=True;obj['source']='field photo courtyard; explicit branches and leaves; seed 23307130129'
 stones=[material('庭院假山砂岩'+str(i),(.12+i*.009,.085+i*.007,.055+i*.005)) for i in range(5)]
 for px,py,sx,sy,sz in [(155,205,1.2,.9,1.5),(158,204,.8,.8,2),(159,207,1.1,.8,1.2),(154,209,.9,.6,.55),(161,205,.65,.65,1)]:
  p=xy((px,py));p.z=sz*.48+.1;bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=1,location=p)
  obj=bpy.context.object;obj.name='西庭院层理假山';obj.scale=(sx,sy,sz*.56);obj.rotation_euler.z=px*.7
  for vertex in obj.data.vertices:
   vertex.co*=rng.uniform(.94,1.06);vertex.co.x+=.10*math.sin(vertex.co.z*12)
  for mat in stones:obj.data.materials.append(mat)
  for face in obj.data.polygons:face.material_index=rng.randrange(len(stones));face.use_smooth=True
