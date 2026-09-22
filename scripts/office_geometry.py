"""51 comprehensive office: user photograph, unseen elevations approximate."""
def build_office(x,y,mat,mesh,current,bpy):
 import math
 wall=mat('Office ivory walls',(.76,.75,.68));trim=mat('Office pale pilasters',(.85,.83,.75));glass=mat('Office grey green glass',(.29,.37,.36),.3);frame=mat('Office aluminium',(.40,.44,.42));roof=mat('Office canopy grey',(.39,.42,.40));pink=mat('Office entry stone',(.63,.49,.41));dark=mat('Office lettering',(.24,.24,.21))
 buf={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buf.setdefault(m.name,([],[]));n=len(vs)
  vs.extend([(x+dx+a*w/2,y+dy+c*d/2,z+e*h/2) for a,c,e in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
  fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 # Lower blank west volume, recessed three-storey link, five-storey east wing.
 b(-14,-1,6.5,13.6,20.4,13,wall)
 b(-14,-10.9,7,3.8,1.3,14,trim)
 b(-14,-10.9,14.1,4.1,1.6,.2,trim)
 b(-14,-1,13.1,14,20.7,.22,trim)
 b(-1,3,5.6,12.4,16.4,11.2,wall)
 b(13,0,9.1,15.6,22.4,18.2,wall)
 b(13,0,18.3,16,22.7,.25,trim)
 b(-1,3,11.3,12.6,16.6,.2,trim)
 def window(cx,fy,z,w=2.25):
  b(cx,fy-.08,z,w,.15,2.1,frame);b(cx,fy-.18,z,w-.14,.04,1.96,glass)
  b(cx,fy-.22,z,.055,.04,2.1,frame);b(cx,fy-.22,z+.55,w,.04,.05,frame)
  for i in range(4):b(cx,fy-.225,z+.7+i*.08,w-.15,.02,.022,trim)
 for cx in [7.3,10.9,14.5,18.1]:
  for z in [2,5.4,8.8,12.2,15.6]:window(cx,-11.2,z)
 for cx in [5.35,9.1,12.7,16.3,20.65]:b(cx,-11.28,9.1,.21,.3,18.2,trim)
 for cx in [-5,-1,3]:
  for z in [2,5.5,9]:window(cx,-5.2,z,3.1)
 for cx in [-7.1,5.1]:b(cx,-5.25,5.6,.22,.25,11.2,trim)
 b(0,-8,3.5,11,6.2,.42,roof)
 for cx in [-4.2,4.2]:b(cx,-9.8,1.65,.48,.55,3.3,pink)
 b(0,-5.45,1.55,4,.2,2.8,frame)
 for cx in [-.95,.95]:b(cx,-5.58,1.55,1.75,.04,2.6,glass)
 b(0,-8,.12,12,7,.24,pink)
 for name,(vs,fs) in buf.items():
  ob=mesh('综合办公楼 · '+name,vs,fs,bpy.data.materials[name]);ob['building_id']='51';ob['building_name']='综合办公楼'
 try:
  font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
  for ch,z in zip('综合楼',[11.4,10.6,9.8]):
   c=bpy.data.curves.new('综合楼字','FONT');c.body=ch;c.font=font;c.size=.65;c.align_x='CENTER';c.extrude=.01
   ob=bpy.data.objects.new('综合楼门牌',c);current.objects.link(ob);ob.location=(x-8.5,y-11.25,z);ob.rotation_euler=(math.pi/2,0,0);c.materials.append(dark)
   bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['building_id']='51';ob['building_name']='综合办公楼'
 except Exception as e:print(e)
