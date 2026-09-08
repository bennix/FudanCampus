"""20: photo-derived south facade; rear elevation is approximate."""
def build_physics(x,y,mat,mesh,current,bpy):
 import math
 brick=mat('Physics red brick',(.49,.235,.15));pale=mat('Physics pale stone',(.78,.78,.70));dark=mat('Physics window frames',(.13,.15,.14));glass=mat('Physics glazing',(.29,.38,.39),.3);joint=mat('Physics brick joints',(.39,.28,.22))
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs)
  vs.extend([(x+dx+a*w/2,y+dy+c*d/2,z+e*h/2) for a,c,e in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
  fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 b(0,0,9.25,92.8,13.6,18.5,brick)
 b(0,-.35,10,13.4,14.3,20,brick)
 b(0,-.35,20.15,14.4,15.2,.3,pale)
 for cx in [-26.6,26.6]:b(cx,0,18.6,39.4,14.4,.28,pale)
 b(0,-6.95,.35,92.8,.35,.7,pale)
 for cx in range(-42,43,6):
  fy=-7.58 if abs(cx)<7 else -6.92
  b(cx,fy,9.2,4.05,.22,17.2,pale)
  for floor in range(5):
   z=2+floor*3.45
   b(cx,fy-.16,z,3.6,.14,2.35,dark)
   b(cx,fy-.25,z,3.42,.045,2.17,glass)
   for dx in [-.9,0,.9]:b(cx+dx,fy-.29,z,.05,.06,2.35,dark)
   b(cx,fy-.29,z+.36,3.6,.06,.055,dark)
 for i in range(184):b(0,-6.812,.6+i*.095,92.7,.014,.007,joint)
 # Broad entrance canopy with three rows of inset square motifs.
 b(0,-10,4.15,22,6.8,.9,pale)
 for z in [3.91,4.16,4.41]:
  for i in range(57):b(-10.65+i*.38,-13.411,z,.10,.018,.11,joint)
 for cx in [-9,-5,5,9]:
  vs,fs=buffers.setdefault(pale.name,([],[]));n=len(vs)
  for z in [.45,3.7]:
   vs.extend([(x+cx+.19*math.cos(i*math.tau/20),y-11.65+.19*math.sin(i*math.tau/20),z) for i in range(20)])
  fs.extend([(n+i,n+(i+1)%20,n+(i+1)%20+20,n+i+20) for i in range(20)])
 b(0,-7.62,1.75,5,.12,3.3,dark)
 for cx in [-1.6,0,1.6]:b(cx,-7.72,1.75,1.45,.04,3.05,glass)
 for i in range(5):b(0,-10.7-i*.55,.5-i*.09,14,3,.16,pale)
 for name,(vs,fs) in buffers.items():
  ob=mesh('恒隆物理楼 · '+name,vs,fs,bpy.data.materials[name]);ob['building_id']='20';ob['building_name']='恒隆物理楼';ob['source']='user front photograph; rear inferred'
