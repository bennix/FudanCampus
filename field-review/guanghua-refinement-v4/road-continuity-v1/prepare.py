import sys,json,math
from pathlib import Path
import shapely as S
from shapely.geometry import LineString,Point,box
O=Path(__file__).resolve().parent;OLD=O.parent/'road-rebuild-v1'
sys.path.insert(0,str(OLD))
from road_geometry import triangulate,extrude,smoothstep
source=(O.parent/'west-exit-shape-v1/prepare_shape.py').read_text()
exec(source[source.index('def curve('):source.index('pts=curve(controls)')])
exec(source[source.index('def level('):source.index('baseline=json')])
local_level=level
west=[(84.95,47.8),(83.2,47.8),(82.2,46.7),(82,45),(81.6,42.5),(78.8,40.3),(75.3,39.8),(73.8,39.8)]
north=[(73.8,85.5),(85,83),(89.8,74),(87.6,66.5),(79.8,61),(80.7,55),(82,53),(82.3,50.5),(82,48.8),(82,45)]
south=[(81.6,42.5),(85,39),(81,33),(83.7,25),(92,18),(106.5,15.5)]
nexit=[(94,58.95),(94,62),(91.6,66),(89.1,70.4)]
main=LineString(curve(north+south[1:]))
end=main.interpolate(main.project(Point(nexit[-1])));nexit[-1]=(end.x,end.y)
nl=LineString(curve(nexit))
routes=[(west,1.64),(north,1.65),(south,1.65),(nexit,1.8)]
for p in [[(81,33),(78,29),(73.8,27)],[(83,66),(78,67),(73.8,68)]]:
 q=main.interpolate(main.project(Point(p[0])));p[0]=(q.x,q.y);routes.append((p,1.5))
road=S.union_all([LineString(curve(p)).buffer(w/2,cap_style='flat',join_style='round') for p,w in routes])
road=road.intersection(box(73.8,10,110,90))
assert road.geom_type=='Polygon','Road network must be connected'
def level(x,y):
 p=Point(x,y);d=nl.distance(p);t=nl.project(p)/nl.length
 nz=.095+(1.33-.095)*(1-smoothstep(t))
 shoulder=(nz-.095)*(1-smoothstep(max(0,d-.9)/5))
 return max(.045,local_level(x,y),.095+shoulder)
baseline=json.loads((OLD/'baseline-geometry.json').read_text());DX=-6.697882438088101
exclude=[]
for o in baseline:
 if (o['id']=='EOPEN_S' and 'coping' in o['name']) or (o['id']=='ESKY' and 'plinth' in o['name']):
  b=o['bounds'];exclude.append(box(b[0][0]-DX-.04,b[1][0]-.04,b[0][1]-DX+.04,b[1][1]+.04))
ground=S.union_all([box(73.8,35,95.5,59),nl.buffer(6)]).difference(S.union_all(exclude)).difference(road)
D={'registration_x':DX,'uncertainty':'Outer route positions inherited and inferred; connected geometry is not surveyed alignment.'}
for name,domain in [('road',road),('ground',ground)]:
 v,f,_=triangulate(domain,.4)
 def height(x,y):
  if name=='road':
   z=level(x,y)
   if x<75:z=.045+(z-.045)*smoothstep((x-73.8)/1.2)
   return z
  return max(.008,local_level(x,y)-.025,(level(x,y)-.095)+.008)
 vv,ff=extrude([(x,y,height(x,y)) for x,y in v],f,bottom=-.09)
 D[name]={'vertices':vv,'faces':ff}
(O/'shape.json').write_text(json.dumps(D))
print('Connected road domain prepared')
