"""Photo study of the red-brick Fudan gate, placed at map landmark 65.
Dimensions and concealed rear surfaces are inferred from the supplied photograph.
"""
def build_gate(x,y,mat,mesh,current,bpy):
 import math
 brick=mat('Gate warm red brick',(.45,.18,.12));mortar=mat('Gate pale mortar',(.63,.53,.44));white=mat('Gate white concrete',(.80,.80,.74));iron=mat('Gate black iron',(.055,.065,.055),.48);gold=mat('Gate brass plaques',(.55,.42,.18),.35);red=mat('Gate red lettering',(.42,.055,.035));concrete=mat('Gate grey threshold',(.47,.48,.43))
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs);vs.extend([(x+dx+a*w/2,y+dy+q*d/2,z+c*h/2) for a,q,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]);fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 def brickwall(cx,w,d,h):
  b(cx,0,h/2,w,d,h,brick)
  for j in range(int(h/.20)):
   b(cx,-d/2-.015,.10+j*.20,w,.025,.012,mortar)
   count=int(w/.42)
   for k in range(count):
    xx=cx-w/2+.22+k*.42+(j%2)*.21
    if xx<cx+w/2-.03:b(xx,-d/2-.018,.20+j*.20,.012,.026,.185,mortar)
  b(cx,-d/2-.10,.32,w+.10,.20,.64,white)
 # Red piers and flanking walls surround an open central carriageway.
 for cx in [-4.9,4.9,-8.0,8.0]:brickwall(cx,.86,3.9,7.8)
 for cx in [-11.0,11.0]:brickwall(cx,5.2,2.9,7.8)
 b(0,0,7.05,15.15,3.45,1.60,white)
 b(0,0,8.02,28.1,5.2,.38,white)
 b(0,0,8.29,28.35,5.4,.16,concrete)
 # Deep beam underside defines the shady openings.
 b(0,1.30,5.86,9,1.0,.45,white)
 b(0,-1.75,.1,27,6.1,.18,concrete)
 # Decorative white openwork screens attached to each red wall.
 for cx in [-11.7,11.7]:
  for dx in [-.96,.96]:b(cx+dx,-1.56,4.5,.15,.24,3.6,white)
  for z in [2.7,6.3]:b(cx,-1.56,z,2.07,.24,.15,white)
  for col in range(4):
   for row in range(6):
    xx=cx-.72+col*.48;zz=3.02+row*.54
    for dx in [-.16,.16]:b(xx+dx,-1.61,zz,.075,.23,.40,white)
    for dz in [-.20,.20]:b(xx,-1.61,zz+dz,.39,.23,.075,white)
 # Open black swing gates are folded back along the driveway.
 for sign in [-1,1]:
  gx=sign*4.34
  for yy in [-1.5,2.7]:b(gx,yy,1.8,.10,.11,3.5,iron)
  for zz in [.35,1.1,2.8,3.35]:b(gx,.6,zz,.10,4.25,.09,iron)
  for j in range(24):b(gx,-1.5+j*.18,1.8,.065,.052,3.20,iron)
  # Side pedestrian leaves retain the same picket rhythm.
  for j in range(12):b(sign*(5.5+j*.18),.75,1.6,.055,.10,3.0,iron)
  for zz in [.2,1.2,2.95]:b(sign*6.5,.75,zz,2.4,.11,.09,iron)
 for cx in [-9.15,9.15]:
  b(cx,-1.51,3.65,.92,.12,.78,gold)
  b(cx,-1.52,2.83,.77,.12,.39,white)
 # Red building title: font-based interpretation, not a traced signature.
 font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
 for i,ch in enumerate('复旦大学'):
  curve=bpy.data.curves.new('校门题字','FONT');curve.body=ch;curve.font=font;curve.align_x='CENTER';curve.size=1.24;curve.extrude=.012
  ob=bpy.data.objects.new('复旦正门 · '+ch,curve);current.objects.link(ob);ob.location=(x-3.3+i*2.20,y-1.79,6.69);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(red)
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['landmark_id']='65';ob['landmark_name']='复旦正门'
 for mname,(vs,fs) in buffers.items():
  ob=mesh('复旦正门 · '+mname,vs,fs,bpy.data.materials[mname]);ob['landmark_id']='65';ob['landmark_name']='复旦正门';ob['source']='user photograph; position assumed at map main gate 65'
