"""Photo-specific geometry for map building 16. Front elevation faces south.
Back elevation remains inferred. Dimensions stay within the mapped footprint.
"""
def build_yifu(x,y,box,mat,mesh,current,bpy):
 import math
 plaster=mat('Yifu off-white ceramic facade',(.76,.77,.74))
 red=mat('Yifu reddish brown stone',(.38,.18,.125))
 joint=mat('Yifu ceramic joints',(.62,.65,.63))
 metal=mat('Yifu charcoal window frames',(.095,.115,.12))
 glazing=mat('Yifu blue grey glass',(.21,.32,.36),.23)
 pale=mat('Yifu canopy edges',(.85,.86,.82))
 roofmat=mat('Yifu roof membrane',(.46,.48,.45))
 def b(name,dx,dy,z,w,d,h,m):
  ob=box('逸夫楼 · '+name,x+dx,y+dy,z,w,d,h,m)
  ob['building_id']='16';ob['building_name']='逸夫楼';ob['map_source']='map + user facade photograph'
  return ob
 def extrusion(name,outline,bottom,top,material):
  verts=[(x+px,y+py,z) for z in [bottom,top] for px,py in outline];n=len(outline)
  faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
  ob=mesh('逸夫楼 · '+name,verts,faces,material);ob['building_id']='16';ob['building_name']='逸夫楼';return ob
 # Staggered main tower, western wing, and recessed eastern upper wing.
 b('主楼',-.6,1.0,11.35,13.6,14,22.7,plaster)
 b('西侧楼体',-11,2.0,9.7,8,12,19.4,plaster)
 b('后侧东翼',9.5,6,9.8,7,10,19.6,plaster)
 b('主楼屋面',-.6,1,22.75,13.4,13.8,.15,roofmat)
 for dx in [-7.4,6.2]:b('女儿墙',dx,1,23.0,.18,14.1,.5,plaster)
 for dy in [-6,8]:b('女儿墙',-.6,dy,23.0,13.7,.18,.5,plaster)
 # Photo's tall red-brown circulation fin projects above the roof.
 outline=[(-7.5+1.15*math.cos(math.pi+i*math.pi/20),-6.0+1.15*math.sin(math.pi+i*math.pi/20)) for i in range(21)]+[(-6.35,6.95),(-8.65,6.95)]
 extrusion('圆弧红褐色竖塔',outline,0,24.2,red)
 # Each bay has dark outlines and thin mullions, instead of repeated white frames.
 def window(dx,dy,z,w=2.3,h=1.55,side=False):
  if not side:
   b('窗框',dx,dy,z,w,.15,h,metal);b('玻璃',dx,dy-.095,z,w-.15,.055,h-.15,glazing)
   for q in [-.25,.25]:b('竖窗梃',dx+w*q,dy-.14,z,.055,.06,h,metal)
   b('横窗梃',dx,dy-.14,z+h*.13,w,.06,.055,metal)
  else:
   b('侧窗框',dx,dy,z,.15,w,h,metal);b('侧玻璃',dx+.095,dy,z,.055,w-.15,h-.15,glazing)
   b('侧窗梃',dx+.14,dy,z,.06,.055,h,metal)
   b('侧横窗梃',dx+.14,dy,z+h*.13,.06,w,.055,metal)
 for z in [5.2,8.8,12.4,20.0]:
  for dx in [-5.1,-2.0,1.1,4.2]:window(dx,-6.09,z,2.45)
 # Recessed continuous ribbon on the upper floor with an overhanging white cap.
 b('上层退台暗窗带',-.6,-6.10,16.2,12.1,.12,1.8,metal)
 for dx in [-5.1,-2,1.1,4.2]:window(dx,-6.2,16.2,2.7,1.65)
 b('上层遮阳横板',-.6,-6.6,17.37,13.8,1.25,.35,pale)
 for z in [4.6,7.6,10.6,13.6,16.6]:
  for dx in [-13.0,-9.6]:window(dx,-4.08,z,2.5)
 for z in [5.2,8.8,12.4,16.2,20.0]:
  for dy in [-2.8,2.0,6.0]:window(6.29,dy,z,1.7,1.6,True)
 for z in [5,8,11,14,17]:
  for dy in [3.5,7.5]:window(13.09,dy,z,2.2,1.6,True)
 # Thin ceramic-panel seams keep the facade readable at closer viewing distance.
 for z in [3.5,6.7,9.75,12.8,15.85,19.1,22.1]:b('水平面砖接缝',-.6,-6.025,z,13.5,.018,.025,joint)
 for dx in [-6.5,-3.5,-.5,2.5,5.5]:b('竖向面砖接缝',dx,-6.025,12,.02,.018,21.8,joint)
 # Recessed glazed entry and long thin canopy supported by slender columns.
 for dx in [-4.5,-1.5,1.5]:window(dx,-6.12,1.75,2.7,2.9)
 b('入口雨棚',-5.0,-8.15,3.5,19.0,4.8,.42,pale)
 b('雨棚收边',-5,-10.6,3.39,19.0,.18,.3,joint)
 for dx in [-12.5,-6,2.2]:b('入口柱',dx,-9.35,1.7,.46,.46,3.4,red)
 for i in range(3):b('入口台阶',-4,-9.2-i*.7,.12*(3-i),17,3.2,.18,joint)
 # Low east annex: white floating fascia, red panels with horizontal stone bands.
 arc=[(10+5.8*math.cos(math.pi+i*math.pi/32),-3+7.4*math.sin(math.pi+i*math.pi/32)) for i in range(33)]
 extrusion('附楼弧形红墙',arc+[(15.8,3.5),(4.2,3.5)],0,6.4,red)
 b('附楼白色檐口',9.0,-4.0,7.25,13.7,15.4,1.65,plaster)
 b('附楼屋面',9.0,-4.0,8.15,13.4,15.1,.14,roofmat)
 for z in [1.8,4.25]:
  for i in range(32):
   p,q=arc[i],arc[i+1];extrusion('弧墙浅色石材横带',[p,q,(q[0]+.05,q[1]-.05),(p[0]+.05,p[1]-.05)],z-.10,z+.10,joint)
 b('附楼右侧竖向红墙',15.1,-8.0,5.35,1.5,6.6,10.7,red)
 b('附楼悬挑红褐色板',14.7,-11.1,6.0,3.0,.65,7.8,red)
 b('附楼入口暗面',4.7,-10.39,2.1,2.3,.15,4.0,metal)
 # Gold-toned building name, modelled text so it remains visible in GLB.
 fontpath='/System/Library/Fonts/Supplemental/Songti.ttc'
 try:
  font=bpy.data.fonts.load(fontpath)
  text=bpy.data.curves.new('逸夫楼楼名','FONT');text.body='逸 夫 楼';text.font=font;text.size=.65;text.align_x='CENTER';text.extrude=.012
  ob=bpy.data.objects.new('逸夫楼 · 楼名',text);current.objects.link(ob);ob.location=(x-.6,y-6.15,22.12);ob.rotation_euler=(1.57079632679,0,0);text.materials.append(mat('Yifu signage',(.40,.36,.23)))
  bpy.context.view_layer.objects.active=ob;ob.select_set(True);bpy.ops.object.convert(target='MESH');ob.select_set(False)
  ob['building_id']='16';ob['building_name']='逸夫楼'
 except Exception as e:print('Sign font unavailable:',e)
