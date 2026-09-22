"""55: photographed entrance facade; orientation and unseen wings approximate."""
def build_chemistry(x,y,mat,mesh,current,bpy):
 import math
 brick=mat('Chemistry red brick',(.46,.20,.12));pale=mat('Chemistry pale panels',(.78,.79,.73));tile=mat('Chemistry canopy tile',(.57,.60,.56));dark=mat('Chemistry dark frames',(.12,.14,.13));glass=mat('Chemistry glazing',(.26,.35,.34),.3);joint=mat('Chemistry joints',(.35,.31,.27));gold=mat('Chemistry signage',(.65,.51,.27))
 buffers={}
 def b(dx,dy,z,w,d,h,m):
  vs,fs=buffers.setdefault(m.name,([],[]));n=len(vs)
  vs.extend([(x+dx+a*w/2,y+dy+c*d/2,z+e*h/2) for a,c,e in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
  fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
 # H-shaped footprint retained, entrance is on the linking bar.
 b(0,0,6.3,65.6,10,12.6,brick)
 for cx in [-25,25]:b(cx,0,6.3,15.6,32.8,12.6,brick)
 for left,right,fy in [(-17.2,17.2,-5),(-32.8,-17.2,-16.4),(17.2,32.8,-16.4)]:
  b((left+right)/2,fy-.08,.4,right-left,.2,.8,pale)
  for i in range(118):b((left+right)/2,fy-.012,.8+i*.1,right-left,.018,.008,joint)
  count=int((right-left)/4.7)
  for j in range(count):
   cx=left+(j+.5)*(right-left)/count
   for z in [2.6,6.6,10.3]:
    b(cx,fy-.14,z,2.7,.2,2.65,dark);b(cx,fy-.26,z,2.55,.06,2.5,glass)
    b(cx,fy-.3,z,.065,.04,2.65,dark);b(cx,fy-.3,z+.35,2.7,.04,.065,dark)
   for z in [4.65,8.5]:b(cx,fy-.17,z,2.85,.25,1.2,pale)
 # Square tiled portico and two substantial square columns.
 b(0,-8,4.6,12,5,.85,tile)
 for cx in [-5,5]:
  b(cx,-9.1,2.15,.75,.75,4.3,tile)
  for i in range(27):b(cx,-9.481,.12+i*.155,.75,.013,.009,joint)
  for dx in [-.23,0,.23]:b(cx+dx,-9.484,2.15,.009,.012,4.3,joint)
 for i in range(78):b(-5.97+i*.155,-10.51,4.6,.009,.016,.85,joint)
 for z in [4.3,4.46,4.62,4.78,4.94]:b(0,-10.51,z,12,.016,.009,joint)
 b(0,-5.35,2,6.8,.5,4,dark)
 for cx in [-1.7,0,1.7]:b(cx,-5.63,1.6,1.55,.07,2.9,glass)
 b(0,-5.67,3.65,6.5,.08,.7,brick)
 b(0,-8,.12,13,6,.24,pale)
 for name,(vs,fs) in buffers.items():
  ob=mesh('化学楼 · '+name,vs,fs,bpy.data.materials[name]);ob['building_id']='55';ob['building_name']='化学楼'
 try:
  font=bpy.data.fonts.load('/System/Library/Fonts/Supplemental/Songti.ttc')
  curve=bpy.data.curves.new('化学楼门头','FONT');curve.body='化  学  楼';curve.font=font;curve.size=.46;curve.align_x='CENTER';curve.extrude=.01
  ob=bpy.data.objects.new('化学楼门头',curve);current.objects.link(ob);ob.location=(x,y-5.74,3.45);ob.rotation_euler=(math.pi/2,0,0);curve.materials.append(gold)
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['building_id']='55';ob['building_name']='化学楼'
 except Exception as e:print(e)
