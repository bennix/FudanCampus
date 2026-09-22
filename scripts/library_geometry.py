"""Building 56: continuous two-storey frontage confirmed by user photographs.
Rear depth remains approximate; no forward-projecting side wings.
"""
def build_library(x,y,mat,mesh,current,bpy):
 import math
 brick=mat('Library muted red brick',(.43,.225,.16));mortar=mat('Library mortar',(.37,.275,.22));cream=mat('Library ivory panels',(.80,.80,.72));stone=mat('Library entry steps',(.55,.56,.51));bronze=mat('Library bronze doors',(.39,.30,.17),.4);dark=mat('Library dark steel',(.12,.16,.15));glass=mat('Library green grey glazing',(.27,.37,.35),.25);roof=mat('Library flat roof',(.40,.42,.38));gold=mat('Library gold signage',(.68,.55,.29),.45)
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs);vs.extend([(x+dx+a*w/2,y+dy+q*d/2,z+c*h/2) for a,q,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]);fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 # The frontage is straight: both ends share the central bar's depth and height.
 front=8.7
 b(0,14.1,5.6,40,10.8,11.2,brick)
 for cx in [-26,26]:
  b(cx,14.1,5.6,12,10.8,11.2,brick)
  b(cx,14.1,11.24,12,11.1,.20,cream)
  b(cx,front-.1,.5,12,.3,1,cream)
  b(cx,front-.42,10.48,12,.94,.16,cream)
  for i in range(128):b(cx,front-.024,.6+i*.08,12,.025,.006,mortar)
 b(0,14.1,11.24,40.4,11.1,.20,cream)
 b(0,front-.1,.5,40.2,.3,1,cream)
 # The new oblique photographs show deep brick reveals and fine running bond.
 for i in range(128):b(0,front-.024,.6+i*.08,39.95,.025,.006,mortar)
 for row in range(128):
  for col in range(181):
   xx=-19.9+col*.22+(row%2)*.11
   if xx<20:b(xx,front-.026,.64+row*.08,.006,.024,.074,mortar)
 for left,right in [(-20,-18.25),(-14.55,-13.15),(-9.45,1.15),(4.85,6.45),(10.15,11.75),(15.45,20)]:
  width=right-left;cx=(left+right)/2
  b(cx,front-.37,5.85,width,.74,10.7,brick)
  for i in range(133):b(cx,front-.746,.54+i*.08,width,.012,.006,mortar)
  for row in range(133):
   for j in range(int(width/.22)+1):
    xx=left+j*.22+(row%2)*.11
    if xx<right:b(xx,front-.75,.58+row*.08,.006,.012,.074,mortar)
 b(0,front-.42,10.48,40,.94,.16,cream)
 def window(cx,z,w,h):
  b(cx,front-.15,z,w,.2,h,dark);b(cx,front-.28,z,w-.16,.07,h-.12,glass)
  for dx in [-w*.25,0,w*.25]:b(cx+dx,front-.34,z,.065,.055,h,dark)
  b(cx,front-.34,z+h*.22,w,.06,.065,dark)
 # Narrow full-height bays, separated by exposed brick piers.
 for cx in [-29,-23.8,-16.4,-11.3,3.0,8.3,13.6,23.8,29]:
  window(cx,7.9,3.7,4.5)
  b(cx,front-.20,5.0,3.9,.18,1.45,cream)
  if cx<0 or cx>20:window(cx,2.55,3.7,3.25)
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
 # Two curved approach ramps follow the stair edges, rising to the landing.
 for side in [-1,1]:
  vs,fs=buffers.setdefault(stone.name,([],[]))
  for i in range(24):
   t=i/24;u=(i+1)/24
   def cross(v):
    cx=7.8+side*(12.5+2.1*(1-v)**2)
    return cx,front-5.4+v*4.9,.09+v*.59
   a,ay,az=cross(t);c,cy,cz=cross(u);n=len(vs)
   vs.extend([(x+a-.8,y+ay,az),(x+a+.8,y+ay,az),(x+c+.8,y+cy,cz),(x+c-.8,y+cy,cz)])
   fs.append((n,n+1,n+2,n+3))
   b((a+c)/2+side*.83,(ay+cy)/2,(az+cz)/2+.07,.14,.24,.14,cream)
 # Visible rainwater pipes, air-conditioning condensers and their grilles.
 for cx in [-18.8,17.1]:
  b(cx,front-.86,5.3,.10,.12,9.6,cream)
  b(cx,front-1.02,1.35,1.0,.55,.78,cream)
  b(cx,front-1.31,1.35,.77,.035,.57,dark)
  for j in range(8):b(cx,front-1.335,1.1+j*.065,.77,.025,.018,stone)
 b(18.4,front-.9,.8,.85,.55,1.4,cream)
 for j in range(16):b(18.4,front-1.19,.2+j*.075,.66,.025,.025,dark)
 # Gold vertical lettering on the blank brick pier left of the doors.
 try:
  font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
  for ch,z in zip('图书馆',[8.2,6.7,5.2]):
   curve=bpy.data.curves.new('图书馆竖排字','FONT');curve.body=ch;curve.font=font;curve.align_x='CENTER';curve.size=.9;curve.extrude=.02
   ob=bpy.data.objects.new('理科图书馆 · '+ch,curve);current.objects.link(ob);ob.location=(x-5.1,y+front-.80,z);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(gold)
   bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['building_id']='56';ob['building_name']='理科图书馆'
 except Exception as e:print('Library lettering:',e)
 for mname,(vs,fs) in buffers.items():
  ob=mesh('理科图书馆 · '+mname,vs,fs,bpy.data.materials[mname]);ob['building_id']='56';ob['building_name']='理科图书馆';ob['source']='map footprint; partial entrance photo; other elevations inferred'
