"""55 photo refinement; local +X east, -Y south/front; inferred metres."""
import math
FOOTPRINT=[(-32.8,-19.6),(-20.4,-19.6),(-20.4,-6.8),(19.6,-6.8),(19.6,-19.6),(32.8,-19.6),(32.8,19.6),(19.6,19.6),(19.6,6.8),(-20.4,6.8),(-20.4,19.6),(-32.8,19.6),(-32.8,9.2),(-28.2,9.2),(-28.2,-9.2),(-32.8,-9.2)]

def build_chemistry(x,y,mat,mesh,current,bpy):
 brick=mat('Chemistry deep red brick',(.34,.095,.055));pale=mat('Chemistry white spandrel panels',(.84,.85,.81));roof=mat('Chemistry white roof',(.91,.92,.90));tile=mat('Chemistry pale ceramic tile',(.77,.78,.70));dark=mat('Chemistry dark bronze frames',(.075,.065,.055));glass=mat('Chemistry glazing',(.14,.235,.225),.32);joint=mat('Chemistry tile joints',(.39,.41,.36));stone=mat('Chemistry entrance granite',(.37,.39,.37));gold=mat('Chemistry signage',(.65,.45,.18))
 objects=[];buffers={};attributes={}
 def box(name,cx,cy,z,w,d,h,m,**extras):
  # Keep window-segment and entrance-roof metadata for spatial checks; batch
  # the remaining repeated details by material to reduce runtime draw calls.
  if extras.get('component')=='window glass':name=f'wall {extras["wall_segment"]:02d} window glass'
  elif extras.get('component')=='portico roof':name=extras['entrance']+' portico roof'
  else:
   name=m.name+(' walls and raised centre' if m==brick else '')
   extras={}
  key=(name,m.name);vs,fs=buffers.setdefault(key,([],[]));n=len(vs)
  vs.extend([(cx+a*w/2,cy+b*d/2,z+c*h/2) for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]])
  fs.extend([tuple(n+i for i in f) for f in [(0,4,6,2),(1,3,7,5),(0,1,5,4),(2,6,7,3),(0,2,3,1),(4,5,7,6)]])
  attributes[key]=extras
 def inside(px,py):
  return ((-20.4<=px<=19.6 and abs(py)<=6.8) or (19.6<=px<=32.8 and abs(py)<=19.6) or (-32.8<=px<=-20.4 and abs(py)<=19.6 and not(px < -28.2 and abs(py)<9.2)))
 # Adjacent roof cells have no overlapping top faces; raised centre has no low roof.
 xs=[-32.8,-28.2,-20.4,-6.5,6.5,19.6,32.8];ys=[-19.6,-9.2,-6.8,6.8,9.2,19.6]
 for xa,xb in zip(xs,xs[1:]):
  for ya,yb in zip(ys,ys[1:]):
   if not inside((xa+xb)/2,(ya+yb)/2):continue
   top=14.4 if xa>=-6.5 and xb<=6.5 and ya>=-6.8 and yb<=6.8 else 12.6
   box('white roof slabs',(xa+xb)/2,(ya+yb)/2,top-.09,xb-xa,yb-ya,.18,roof,component='roof')
 for sign in [-1,1]:box('raised centre returns',sign*6.5,0,13.41,.18,13.6,1.62,brick)
 for seg,(a,b) in enumerate(zip(FOOTPRINT,FOOTPRINT[1:]+FOOTPRINT[:1])):
  ax,ay=a;bx,by=b;length=math.hypot(bx-ax,by-ay);tx,ty=(bx-ax)/length,(by-ay)/length;nx,ny=ty,-tx;cx,cy=(ax+bx)/2,(ay+by)/2
  linking=abs(abs(cy)-6.8)<.01 and abs(tx)>.5;east=abs(cx-32.8)<.01 and abs(ty)>.5;doorway=linking or east
  def facebox(label,u,z,w,h,depth,offset,m,**extras):
   box(f'wall {seg:02d} '+label,cx+tx*u+nx*offset,cy+ty*u+ny*offset,z,w if abs(tx)>.5 else depth,depth if abs(tx)>.5 else w,h,m,wall_segment=seg,**extras)
  if doorway:
   half=1.8 if linking else 2.1
   u0=-cx/tx if linking else 0
   for lo,hi in [(-length/2,u0-half),(u0+half,length/2)]:
    facebox('brick pier',(lo+hi)/2,6.3,hi-lo,12.6,.20,-.10,brick)
   facebox('brick over door',u0,7.95,half*2,9.3,.20,-.10,brick)
  else:facebox('brick wall',0,6.3,length,12.6,.20,-.10,brick)
  if linking:facebox('raised centre brick',-cx/tx,13.41,13,1.62,.20,-.10,brick)
  count=max(1,round(length/3.45));pitch=length/count
  for j in range(count):
   u=-length/2+(j+.5)*pitch;w=min(1.9,pitch-.85)
   for floor,z in enumerate([2.6,6.6,10.3]):
    if doorway and floor==0 and abs(u)<(3.8 if linking else 4.0):continue
    facebox('window glass',u,z,w,2.65,.04,.045,glass,component='window glass',window_width=w)
    for du in [-w/2,0,w/2]:facebox('window vertical frames',u+du,z,.055,2.76,.065,.069,dark)
    for dz in [-1.3525,-.72,.92,1.3525]:facebox('window horizontal frames',u,z+dz,w-.055,.055,.065,.069,dark)
    facebox('sill',u,z-1.43,w+.16,.12,.20,.075,pale)
   for z in [4.65,8.5]:facebox('white spandrels',u,z,w+.10,1.22,.09,.025,pale)
  if doorway:
   half=1.8 if linking else 2.1
   u0=-cx/tx if linking else 0
   for lo,hi in [(-length/2,u0-half),(u0+half,length/2)]:
    facebox('plinth',(lo+hi)/2,.37,hi-lo,.74,.10,.025,pale)
  else:facebox('plinth',0,.37,length,.74,.10,.025,pale)
  if linking:
   # Split at world x +/-6.5, not at the asymmetric linking wall midpoint.
   for lo,hi in [(-20.4,-6.5),(6.5,19.6)]:facebox('roof coping',((lo+hi)/2-cx)/tx,12.56,hi-lo,.18,.28,0,roof)
   facebox('central roof coping',-cx/tx,14.36,13,.18,.28,0,roof)
  else:facebox('roof coping',0,12.56,length,.18,.28,0,roof)
 # Visible through-passage in front photograph; exact depth inferred.
 for sign in [-1,1]:box('passage side walls',sign*1.9,0,1.65,.20,13.6,3.3,brick)
 box('passage ceiling',0,0,3.4,3.6,13.6,.20,pale);box('passage floor',0,0,.08,3.6,13.6,.16,stone)
 def entrance(label,cx,cy,nx,ny,width,depth):
  tx,ty=-ny,nx
  def e(name,u,v,z,w,d,h,m,**extras):
   box(label+' '+name,cx+tx*u+nx*v,cy+ty*u+ny*v,z,w if tx else d,d if tx else w,h,m,entrance=label,**extras)
  e('portico roof',0,depth/2,3.96,width,depth,.56,tile,component='portico roof',width=width)
  e('white top',0,depth/2,4.265,width+.05,depth+.05,.05,roof)
  for u in [-width/2+.36,width/2-.36]:
   e('small ceramic columns',u,depth-.38,1.84,.42,.42,3.68,tile)
   for i in range(24):e('column grout',u,depth-.163,.16+i*.15,.42,.012,.009,joint)
   for du in [-.07,.07]:e('column grout vertical',u+du,depth-.163,1.84,.009,.012,3.68,joint)
  for i in range(int(width/.15)):e('fascia vertical grout',-width/2+.075+i*.15,depth+.008,3.96,.009,.012,.56,joint)
  for z in [3.76,3.91,4.06,4.21]:e('fascia horizontal grout',0,depth+.008,z,width,.012,.009,joint)
  for u in [-width/2-.008,width/2+.008]:
   for i in range(int(depth/.15)):e('side fascia grout',u,.075+i*.15,3.96,.012,.009,.56,joint)
   for z in [3.76,3.91,4.06,4.21]:e('side fascia grout',u,depth/2,z,.012,depth,.009,joint)
  e('entry landing',0,depth/2,.16,width+.3,depth+.2,.32,stone)
  for i in range(2):e('entry step',0,depth+.3+i*.3,.10-i*.05,width+.6,.3,.20-i*.10,stone)
  doorw=3.5 if label!='east' else 4.1
  for u in [-doorw/2,0,doorw/2]:e('door jambs',u,.12,1.61,.055,.08,2.9,dark)
  for z in [.17,2.55,3.08]:e('door lintels',0,.12,z,doorw,.08,.065,dark)
  for u in [-doorw/4,doorw/4]:
   e('door glass',u,.10,1.40,doorw/2-.09,.025,2.30,glass)
   e('door handles',u*.11,.22,1.35,.025,.035,.45,gold)
  e('transom',0,.10,2.81,doorw-.08,.025,.45,glass);e('entrance sign backing',0,.05,3.48,doorw+.35,.10,.54,brick)
  from pathlib import Path
  fontpath='C:/Windows/Fonts/simhei.ttf'
  if Path(fontpath).exists():
   curve=bpy.data.curves.new(label+' chemistry sign','FONT');curve.body='化  学  楼';curve.size=.38;curve.align_x='CENTER';curve.extrude=.006;curve.font=bpy.data.fonts.load(fontpath)
   ob=bpy.data.objects.new(label+' 化学楼门头',curve);current.objects.link(ob);ob.location=(x+cx+nx*.12,y+cy+ny*.12,3.34);ob.rotation_euler=(math.pi/2,0,math.atan2(nx,-ny));curve.materials.append(gold)
   bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False);ob['building_id']='55';ob['building_name']='化学楼';objects.append(ob)
 entrance('front',0,-6.8,0,-1,6.8,2.2);entrance('rear',0,6.8,0,1,6.8,2.0);entrance('east',32.8,0,1,0,7.2,2.5)
 for (name,m),(vs,fs) in buffers.items():
  me=mesh('化学楼 · '+name,[(x+a,y+b,c) for a,b,c in vs],fs,bpy.data.materials[m]);me['building_id']='55';me['building_name']='化学楼'
  for k,v in attributes[(name,m)].items():me[k]=v
  objects.append(me)
 return objects
