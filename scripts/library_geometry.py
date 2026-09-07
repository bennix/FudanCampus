"""Building 56: map U footprint, photographed two-storey entrance elevation.
Side/rear wings remain inferred; this partial photograph does not define them.
"""
def build_library(x,y,mat,mesh,current,bpy):
 import math
 brick=mat('Library muted red brick',(.43,.225,.16));mortar=mat('Library mortar',(.37,.275,.22));cream=mat('Library ivory panels',(.80,.80,.72));stone=mat('Library entry steps',(.55,.56,.51));bronze=mat('Library bronze doors',(.39,.30,.17),.4);dark=mat('Library dark steel',(.12,.16,.15));glass=mat('Library green grey glazing',(.27,.37,.35),.25);roof=mat('Library flat roof',(.40,.42,.38));gold=mat('Library gold signage',(.68,.55,.29),.45)
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs);vs.extend([(x+dx+a*w/2,y+dy+q*d/2,z+c*h/2) for a,q,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]);fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 # Map footprint: the enclosed northern bar, and two deeper side wings.
 front=8.7
 b(0,14.1,5.6,40,10.8,11.2,brick)
 for cx in [-25.9,25.9]:
  b(cx,0,8.15,13,39.2,16.3,brick);b(cx,0,16.42,13.3,39.5,.24,cream)
  for zz in [2.0,5.1,8.2,11.3,14.4]:
   for dx in [-4,0,4]:
    b(cx+dx,-19.69,zz,2.9,.16,2.1,dark);b(cx+dx,-19.80,zz,2.7,.08,1.9,glass);b(cx+dx,-19.87,zz,.07,.06,2.1,bronze)
   for yy in range(-15,17,5):
    side=cx-6.59 if cx>0 else cx+6.59
    b(side,yy,zz,.16,3.4,2.1,dark)
  b(cx,-19.74,.5,13.3,.25,1.0,cream)
 b(0,14.1,11.24,40.4,11.1,.20,cream)
 b(0,front-.1,.5,40.2,.3,1,cream)
 # Front masonry joints sit behind the protruding steel glazing frames.
 for i in range(45):b(0,front-.024,.6+i*.235,39.95,.025,.015,mortar)
 for row in range(44):
  for col in range(81):
   xx=-19.75+col*.49+(row%2)*.245
   if xx<20:b(xx,front-.026,.72+row*.235,.015,.024,.22,mortar)
 def window(cx,z,w,h):
  b(cx,front-.15,z,w,.2,h,dark);b(cx,front-.28,z,w-.16,.07,h-.12,glass)
  for dx in [-w*.25,0,w*.25]:b(cx+dx,front-.34,z,.065,.055,h,dark)
  b(cx,front-.34,z+h*.22,w,.06,.065,dark)
 # Narrow full-height bays, separated by exposed brick piers.
 for cx in [-16.4,-11.3,3.0,8.3,13.6]:
  window(cx,7.9,3.7,4.5)
  b(cx,front-.20,5.0,3.9,.18,1.45,cream)
  if cx<0:window(cx,2.55,3.7,3.25)
 # Three bronze-framed entrances, each aligned with an upper glazed bay.
 for cx in [3,8.3,13.6]:
  b(cx,front-.24,2.20,3.65,.18,3.55,bronze)
  b(cx,front-.38,2.14,3.24,.08,3.15,glass)
  for dx in [-1.60,0,1.60]:b(cx+dx,front-.46,2.1,.08,.08,3.15,bronze)
  b(cx,front-.46,3.08,3.27,.08,.085,bronze)
  for dx in [-.18,.18]:b(cx+dx,front-.54,1.70,.035,.07,.50,gold)
  # Shallow white hood, rather than an invented large canopy.
  b(cx,front-.53,4.02,4.05,1.0,.18,cream)
 # Open central door reads as a shaded recess, as in the reference.
 b(8.75,front-.45,1.92,1.22,.055,2.9,dark)
 for cx in [.55,5.5,10.85,16.1]:
  b(cx,front-.58,3.40,.27,.27,.42,dark)
  b(cx,front-.73,3.43,.15,.04,.23,cream)
 # The broad entry steps and flanking low walls.
 for i in range(6):b(7.8,front-1.6-i*.55,.60-i*.09,23+i*.55,1.3,.18,stone)
 for cx in [-5.2,20.8]:b(cx,front-2,.44,1.0,4.5,.88,cream)
 # Gold vertical lettering on the blank brick pier left of the doors.
 try:
  font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
  for ch,z in zip('图书馆',[8.2,6.7,5.2]):
   curve=bpy.data.curves.new('图书馆竖排字','FONT');curve.body=ch;curve.font=font;curve.align_x='CENTER';curve.size=.9;curve.extrude=.02
   ob=bpy.data.objects.new('理科图书馆 · '+ch,curve);current.objects.link(ob);ob.location=(x-5.1,y+front-.25,z);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(gold)
   bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['building_id']='56';ob['building_name']='理科图书馆'
 except Exception as e:print('Library lettering:',e)
 for mname,(vs,fs) in buffers.items():
  ob=mesh('理科图书馆 · '+mname,vs,fs,bpy.data.materials[mname]);ob['building_id']='56';ob['building_name']='理科图书馆';ob['source']='map footprint; partial entrance photo; other elevations inferred'
