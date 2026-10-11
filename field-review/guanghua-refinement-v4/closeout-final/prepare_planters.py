"""Use independent reviewed outlines, rebuild topology as global polygon solids."""
import json,math,sys
from pathlib import Path
import numpy as np
from collections import defaultdict
from shapely import Polygon,Point,LineString,box,constrained_delaunay_triangles
from shapely.ops import split,unary_union
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O.parent/'road-rebuild-v1'))
from road_geometry import triangulate,extrude
src=(O.parent/'entry-planters-v5/prepare_geometry.py').read_text(encoding='utf-8')
exec(src[src.index('Y0='):src.index('pack=dict(')])
old=json.loads((O.parent/'entry-planters-v5/geometry-pack.json').read_text(encoding='utf-8'))
def domain(rows):
 return unary_union([Polygon(r['exterior'],r['holes']) for r in rows]).buffer(0).simplify(.00004,preserve_topology=True)
def solid(name,g,top,bottom,role,side,mat):
 g=g.buffer(.00005).buffer(-.00005).simplify(.00004,preserve_topology=True)
 # One global triangulation removes the old per-cell T-junctions.
 v,f,_=triangulate(g,.38)
 vv,ff=extrude([(x,y,top(x,y)) for x,y in v],f,bottom=-.035)
 # extrude's bottom vertex ordering matches top vertex ordering.
 for i in range(len(v),len(vv)):
  x,y,_=vv[i];vv[i]=(x,y,bottom(x,y))
 return dict(name=name,vertices=vv,faces=ff,role=role,side=side,material=mat)
new=dict(plans=old['plans'],checks=old['checks'],objects=[],topology='Global constrained triangulation; shared top/bottom/boundary indices')
for side,spec in SPECS.items():
 p=Plan(side,spec);plans=old['plans'][side];mask=p.inner.buffer(1.85,quad_segs=36)
 def wall(x,y):
  # Narrow continuous rise at each step produces connected top and cap surfaces.
  a=p.wall_height(x,y-0.009);b=p.wall_height(x,y+0.009)
  return .5*(a+b)
 for stem,key in [('wall','wall'),('coping','coping')]:
  g=domain(plans[key])
  for role,part in [('retaining',g.difference(mask)),('flower plinth',g.intersection(mask))]:
   top=lambda x,y,stem=stem:wall(x,y)+(p.cap_thickness(x,y) if stem=='coping' else 0)
   bottom=wall if stem=='coping' else lambda x,y:.035
   new['objects'].append(solid('P5 '+side+' '+role+' '+stem,part,top,bottom,stem,side,'cap' if stem=='coping' else 'stone'))
 outerline=LineString(bez(spec['outer_path'],100));om=p.outer.buffer(1.85,quad_segs=36)
 for stem,w,r in [('wall',.25,1.38),('coping',.31,1.5)]:
  g=rounded(outerline.buffer(w,quad_segs=6).union(p.outer.buffer(r,quad_segs=32)),.23).intersection(box(-150,70,150,120))
  def ot(x,y,stem=stem):
   d=Point(x,y).distance(p.outer);t=min(1,max(0,(d-1.85)/1.15));t=t*t*(3-2*t)
   return .785+(p.ramp_z(y)+.75-.785)*t+(.13 if stem=='coping' else 0)
  for role,part in [('outer rail',g.difference(om)),('outer flower plinth',g.intersection(om))]:
   bot=(lambda x,y:ot(x,y)-.13) if stem=='coping' else lambda x,y:.035
   new['objects'].append(solid('P5 '+side+' '+role+' '+stem,part,ot,bot,stem,side,'cap' if stem=='coping' else 'stone'))
 soil=domain(plans['planting']);new['objects'].append(solid('P5 '+side+' planting surface',soil,lambda x,y:p.soil_height(x,y),lambda x,y:.035,'soil',side,'soil'))
 for role,key,baseheight,mat in [('burgundy shrubs','red',spec['red_height'],'red'),('green shrubs','green',spec['green_height'],'green')]:
  g=domain(plans['zones'][key])
  def canopy(x,y):
   d=Point(x,y).distance(g.boundary);f=math.sin(min(1,d/.55)*math.pi/2)
   return p.soil_height(x,y)+.16+baseheight*f+f*(.042*math.sin(4.4*x+1.7*y)+.028*math.cos(2.2*x-4.9*y))
  new['objects'].append(solid('P5 '+side+' '+role,g,canopy,lambda x,y:p.soil_height(x,y)-.025,'vegetation',side,mat))
(O/'planter-pack.json').write_text(json.dumps(new,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
print('PLANTER_TOPOLOGY_PREPARED',len(new['objects']),flush=True)
