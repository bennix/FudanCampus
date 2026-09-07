"""Map building 14: facade study from the supplied photograph; rear inferred."""
def build_yifu_science(x,y,box,mat,mesh,current,bpy):
 import math
 white=mat('Science warm stone',(.73,.73,.64));edge=mat('Science pale limestone edges',(.84,.83,.72));brick=mat('Science terracotta brick',(.40,.205,.105));glass=mat('Science pale blue glazing',(.29,.45,.47),.22);frame=mat('Science window aluminium',(.55,.61,.59),.42);dark=mat('Science deep window recess',(.105,.15,.15));base=mat('Science banded sandstone base',(.50,.50,.42));roof=mat('Science roof membrane',(.40,.43,.41))
 # Procedural fine brick surface is retained in Blender, with matching GLB base colour.
 nodes=brick.node_tree.nodes;links=brick.node_tree.links
 noise=nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95
 bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.07
 links.new(noise.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
 def b(name,dx,dy,z,w,d,h,m):
  ob=box('逸夫科技楼 · '+name,x+dx,y+dy,z,w,d,h,m);ob['building_id']='14';ob['building_name']='逸夫科技楼';ob['map_source']='map + user facade photograph';return ob
 b('西侧高塔',-15.2,1,15.7,14.2,14.2,31.4,white)
 b('中部次高塔',-4.5,1.8,12.5,8.7,14.0,25,white)
 b('高塔红砖竖塔',-16.4,-1,16.7,2.6,14.2,33.4,brick)
 b('次高塔红砖竖塔',-.15,4,13.5,2.0,10.3,27,brick)
 for z in [4.5,7.8,11.1,14.4,17.7,21,24.3,27.6,30.3]:
  for dx in [-17.0,-15.8]:b('红砖塔窄竖窗',dx,-8.16,z,.32,.12,1.6,dark)
 # Deep projecting stone frames around the tall window bays.
 for dx,height,dy in [(-22.0,31.9,-6.3),(-9,31.9,-6.3),(-8.4,26.0,-5.6),(-.5,26,-5.6)]:b('竖向石材边框',dx,dy,height/2,1.0,1.0,height,edge)
 def window(dx,dy,z,w,h=1.8,side=False):
  if not side:
   b('窗洞',dx,dy,z,w,.18,h,dark);b('蓝绿玻璃',dx,dy-.12,z,w-.14,.045,h-.12,glass)
   for q in [-.35,-.15,.05,.25,.45]:b('铝合金窗梃',dx+w*q,dy-.16,z,.055,.055,h,frame)
   b('上部横窗梃',dx,dy-.16,z+h*.22,w,.055,.055,frame)
   b('窗台石材',dx,dy-.22,z-h/2-.10,w+.2,.4,.18,edge)
  else:
   b('侧窗洞',dx,dy,z,.18,w,h,dark);b('侧玻璃',dx+.12,dy,z,.045,w-.14,h-.12,glass)
   for q in [-.3,0,.3]:b('侧窗梃',dx+.16,dy+w*q,z,.055,.055,h,frame)
 for z in [6.0,9.15,12.3,15.45,18.6,21.75,24.9,28.05]:
  window(-19.8,-6.19,z,2.9);window(-12.45,-6.19,z,4.9)
 for z in [6,9.15,12.3,15.45,18.6,21.75]:window(-4.5,-5.29,z,6.2)
 for z in [6,9.15,12.3,15.45,18.6,21.75]:
  for dy in [-1,3,7]:window(-.10,dy,z,2.6,1.8,True)
 for dx in [-20.5,-11.8,-4.5]:window(dx,-6.2,2.3,2.8,2.8)
 for dx,dy,w,d,h in [(-15.2,1,14.2,14.2,31.4),(-4.5,1.8,8.7,14,25)]:
  b('屋面',dx,dy,h+.12,w-.3,d-.3,.2,roof)
  for off in [-w/2+.2,w/2-.2]:b('屋顶竖向挑片',dx+off,dy-3,h+.8,.4,3,1.6,edge)
 # Tall transparent entrance hall between tower and brick-clad low auditorium.
 b('门厅内墙',3.3,3,4.7,7.2,10.2,9.4,white)
 window(3.5,-6.5,5.0,7.5,8.1)
 for z in [2.1,4.5,6.9]:b('门厅玻璃横梁',3.5,-6.69,z,7.5,.08,.075,frame)
 b('附馆红砖体量',15.0,1,4.6,16,15,9.2,brick)
 b('附馆底部石材',15,-6.64,1.65,16,.3,3.3,base)
 for z in [.7,1.4,2.1,2.8]:b('底部水平石材带',15,-6.84,z,16,.12,.14,edge)
 # Large flat overhang and exposed structural beams, the strongest photo feature.
 b('大挑檐',10.5,-.2,10.35,27,21,1.45,edge)
 b('附馆屋面',10.5,-.2,11.12,26.7,20.7,.14,roof)
 for dx in [-1,3.5,8,12.5,17,21.5]:b('挑檐下梁',dx,-.2,9.50,.3,20,.42,base)
 # Cylindrical far-right support column.
 n=20;cx=x+23.1;cy=y-8.4;r=.45;top=9.9
 verts=[(cx+r*math.cos(i*2*math.pi/n),cy+r*math.sin(i*2*math.pi/n),z) for z in [0,top] for i in range(n)]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 ob=mesh('逸夫科技楼 · 挑檐圆柱',verts,faces,edge);ob['building_id']='14';ob['building_name']='逸夫科技楼'
 for i in range(4):b('门厅台阶',3.5,-8.3-i*.55,.12*(4-i),8.4,2.4,.18,base)
