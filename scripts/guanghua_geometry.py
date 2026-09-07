"""Photo-based symmetrical Guanghua facade; rear elevations are inferred.
Local dimensions fit the traced campus footprint. All detail shares building ID 27.
"""
def build_guanghua(x,y,mat,mesh):
 import math
 stone=mat('Guanghua rose grey stone',(.49,.405,.405))
 pale=mat('Guanghua light stone edges',(.68,.59,.55))
 dark=mat('Guanghua recessed bronze',(.19,.155,.16))
 silver=mat('Guanghua curtain wall mullions',(.64,.69,.70),.42)
 blues=[mat('Guanghua blue glazing '+str(i),c,.18) for i,c in enumerate([(.075,.20,.36),(.12,.29,.47),(.18,.33,.47),(.095,.245,.40)])]
 roof=mat('Guanghua roof',(.31,.32,.34))
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs)
  vs.extend([(x+dx+a*w/2,y+dy+q*d/2,z+c*h/2) for a,q,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
  fs.extend([tuple(n+j for j in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 def curtain(cx,cy,bottom,width,height,cols,rows,side=False):
  cw=width/cols;rh=height/rows
  for i in range(cols):
   for j in range(rows):
    u=cx if side else cx-width/2+(i+.5)*cw;v=cy-width/2+(i+.5)*cw if side else cy
    b(u,v,bottom+(j+.5)*rh,.12 if side else cw-.07,cw-.07 if side else .12,rh-.08,blues[(i*3+j*7)%4])
  for i in range(cols+1):
   if side:b(cx+.12,cy-width/2+i*cw,bottom+height/2,.13,.11,height,silver)
   else:b(cx-width/2+i*cw,cy-.12,bottom+height/2,.11,.13,height,silver)
  for j in range(rows+1):
   if side:b(cx+.12,cy,bottom+j*rh,.13,width,.10,silver)
   else:b(cx,cy-.12,bottom+j*rh,width,.13,.10,silver)
 def pyramid(cx,cy,z,w,d,h):
  vs,fs=buffers.setdefault(blues[0].name,([],[]));n=len(vs)
  vs.extend([(x+cx-w/2,y+cy-d/2,z),(x+cx+w/2,y+cy-d/2,z),(x+cx+w/2,y+cy+d/2,z),(x+cx-w/2,y+cy+d/2,z),(x+cx,y+cy,z+h)])
  fs.extend([tuple(n+i for i in f) for f in [(0,1,4),(1,2,4),(2,3,4),(3,0,4)]])
  # Glass pyramid ridges and horizontal glazing courses.
  for k in range(1,5):
   factor=1-k/5;zz=z+h*k/5
   for sign in [-1,1]:b(cx,cy+sign*d*factor/2,zz,w*factor,.09,.09,silver);b(cx+sign*w*factor/2,cy,zz,.09,d*factor,.09,silver)
 # Lowest broad podium, a recessed entrance wall and a continuous front colonnade.
 b(0,1,2.0,122,30,4,stone)
 b(0,-15.5,4.15,64,1,5.7,dark)
 curtain(0,-16.08,1.7,62,5.0,31,2)
 for i in range(-15,16):b(i*2.0,-18.4,4.0,.52,.8,5.8,pale)
 b(0,-18.0,7.2,66,4.1,.7,pale)
 b(0,-20.5,1.15,69,7,2.3,stone)
 for i in range(10):b(0,-24.6-i*.47,1.1-i*.105,72+i*.5,1.0,.22,pale)
 # Twin towers. Heavy stone side piers bracket slender, blue, gridded glazing.
 for cx in [-15.6,15.6]:
  b(cx,0,36.2,20.2,23,58.4,stone) # z 7 to 65.4
  curtain(cx,-11.59,15.8,13.7,48.8,8,25)
  curtain(cx+10.16,0,15.8,15.4,48.8,7,25,True)
  # rear curtain wall uses a broad inset; back detailing remains inferred.
  b(cx,11.56,40.2,13.7,.12,48.8,blues[1])
  for dx in [-9.5,-8.2,8.2,9.5]:b(cx+dx,-11.70,40.4,.19,.2,49,pale)
  for zz in range(17,66,2):
   for dx in [-8.55,8.55]:b(cx+dx,-11.69,zz,3.0,.12,.065,pale)
  # Tall open stone posts below the main curtain-wall field.
  b(cx,-11.72,11.1,16.6,.15,6.8,dark)
  curtain(cx,-11.82,8,15.4,6.9,8,3)
  for dx in [-8,-5.3,-2.65,0,2.65,5.3,8]:b(cx+dx,-12.45,11.2,.55,1.0,7.3,pale)
  b(cx,-12.0,15.1,21.2,2.0,.75,pale)
  # Stepped shoulders and recessed rooftop colonnade; flat caps and thin antennae.
  b(cx,0,66.1,18.8,21.3,1.4,stone)
  b(cx,0,69.9,15.6,18.5,6.3,dark)
  for dx in [-7.5,-5,-2.5,0,2.5,5,7.5]:
   b(cx+dx,-10.0,70.0,.46,1.0,6.7,pale)
   b(cx+dx,10.0,70.0,.46,1.0,6.7,pale)
  for dy in [-7,-3.5,0,3.5,7]:
   for dx in [-8.0,8.0]:b(cx+dx,dy,70.0,.8,.46,6.7,pale)
  b(cx,0,73.65,18.2,22,.6,pale)
  b(cx,0,74.25,3,3,.65,stone)
  b(cx,0,77.05,.11,.11,5.0,silver)
 # The connecting mid-rise remains well below the tower roofs, with a columned crown.
 b(0,3,16.5,11.4,18,25,stone)
 curtain(0,-6.1,7.6,9.4,21.1,5,11)
 b(0,3,30.4,11.8,18.2,1.2,pale)
 b(0,2,33.8,11.3,15.7,5.6,dark)
 for dx in [-4.8,-2.4,0,2.4,4.8]:b(dx,-6.5,33.8,.44,.8,5.7,pale)
 b(0,2,36.8,12.3,18.1,.65,pale)
 # Symmetrical stepped side wings: tall inner shoulders, lower outer pavilions.
 for sign in [-1,1]:
  cx=sign*34.6
  b(cx,3,10,18,24,20,stone)
  curtain(cx,-9.08,4.2,16.4,14.2,9,7)
  for zz in [9.6,14.3,18.8]:b(cx,-9.34,zz,18.4,.7,.48,pale)
  b(cx,3,20.4,19.2,25.2,.7,pale)
  pyramid(cx,3,20.8,4.6,5.0,2.2)
  cx=sign*51.5
  b(cx,0,7.4,21.4,27,14.8,stone)
  curtain(cx,-13.61,3.4,19.7,10.4,11,5)
  for zz in [7.5,11.8,14.7]:b(cx,-13.8,zz,22,.6,.46,pale)
  for dx in [-9,-4.5,0,4.5,9]:b(cx+dx,-13.84,6.8,.36,.4,7.1,pale)
  b(cx,0,15.2,22.7,28.1,.65,pale)
  b(cx,0,15.6,21.9,27.4,.18,roof)
  pyramid(cx+sign*5.2,-1,15.75,7.4,8.0,3.3)
  # side-facing glazing supplies coherent orbit views.
  curtain(sign*62.26,0,3.4,23,10.4,11,5,True)
 for mname,(vs,fs) in buffers.items():
  import bpy
  ob=mesh('光华楼 · '+mname,vs,fs,bpy.data.materials[mname]);ob['building_id']='27';ob['building_name']='光华楼';ob['source']='user front photograph; rear inferred'
