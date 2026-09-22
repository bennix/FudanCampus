"""Photo study of the red-brick Fudan gate, placed at map landmark 65.
South/front follows photos 2–3; north/rear follows photo 1 supplied 2026-09-20.
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
  # Rear-facing brickwork, previously missing from the model.
  for j in range(int(h/.20)):
   b(cx,d/2+.015,.10+j*.20,w,.025,.012,mortar)
   for k in range(int(w/.42)):
    xx=cx-w/2+.22+k*.42+(j%2)*.21
    if xx<cx+w/2-.03:b(xx,d/2+.018,.20+j*.20,.012,.026,.185,mortar)
  b(cx,d/2+.10,.32,w+.10,.20,.64,white)
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
  for dx in [-.72,.72]:b(cx+dx,-1.56,4.75,.13,.24,5.5,white)
  for z in [2.0,7.5]:b(cx,-1.56,z,1.57,.24,.13,white)
  for col in range(3):
   for row in range(12):
    xx=cx-.46+col*.46;zz=2.27+row*.45
    for dx in [-.14,.14]:b(xx+dx,-1.61,zz,.065,.23,.33,white)
    for dz in [-.165,.165]:b(xx,-1.61,zz+dz,.34,.23,.065,white)
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
 # Rear side passages stay open; no freestanding white-framed glazing.
 blue=mat('Gate traffic blue',(.035,.14,.36))
 for sign in [-1,1]:
  b(sign*8.52,2.04,4.1,.085,.09,7.3,white)
  b(sign*4.17,2.75,.68,.45,.48,1.36,red)
  b(sign*2.18,2.76,1.15,3.75,.09,.13,white)
  for j in range(9):b(sign*(.45+j*.40),2.70,1.15,.22,.02,.085,red)
  b(sign*4.90,2.015,2.2,.73,.045,.94,blue)
  # Security cameras on short white brackets.
  b(sign*5.55,2.22,3.55,.8,.07,.07,white)
  b(sign*5.32,2.42,3.51,.26,.43,.16,iron)
  # Low extensions visible beside the front gate.
  b(sign*16.25,.3,1.8,5.3,2.7,3.6,brick)
  b(sign*16.25,.3,3.66,5.55,2.9,.18,white)
  for j in range(4):
   wx=sign*(14.45+j*1.03)
   b(wx,-1.09,2.85,.67,.08,.42,white)
   b(wx,-1.145,2.85,.49,.035,.28,iron)
 # Supplied font's lowercase t is the entire calligraphic university wordmark.
 from pathlib import Path
 font=bpy.data.fonts.load(str(Path(__file__).resolve().parents[1]/'references'/'fudan-1.ttf'))
 curve=bpy.data.curves.new('复旦字体 t 校名','FONT');curve.body='t';curve.font=font;curve.size=1;curve.extrude=.003;curve.resolution_u=16
 ob=bpy.data.objects.new('复旦正门 · 复旦大学字标 t Mesh',curve);current.objects.link(ob);curve.materials.append(red)
 bpy.ops.object.select_all(action='DESELECT');bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH')
 verts=ob.data.vertices
 minx=min(v.co.x for v in verts);maxx=max(v.co.x for v in verts);miny=min(v.co.y for v in verts);maxy=max(v.co.y for v in verts)
 scale=min(8.0/(maxx-minx),1.24/(maxy-miny))
 for v in verts:
  v.co.x=(v.co.x-(minx+maxx)/2)*scale
  v.co.y=(v.co.y-(miny+maxy)/2)*scale
  v.co.z*=scale
 ob.location=(x,y-1.79,7.04);ob.rotation_euler=(math.pi/2,0,0);ob.select_set(False)
 ob['landmark_id']='65';ob['landmark_name']='复旦正门';ob['source_glyph']='t';ob['source_font']='fudan-1.ttf';ob['side']='front'
 for mname,(vs,fs) in buffers.items():
  ob=mesh('复旦正门 · '+mname,vs,fs,bpy.data.materials[mname]);ob['landmark_id']='65';ob['landmark_name']='复旦正门';ob['source']='user photograph; position assumed at map main gate 65'
