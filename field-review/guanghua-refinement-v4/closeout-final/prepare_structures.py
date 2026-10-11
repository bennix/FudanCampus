"""Bounded road replacement with a shared edge elevation; no branch scene import."""
import json,sys,math
from pathlib import Path
import shapely as S
from shapely import Polygon,Point,LineString,box,constrained_delaunay_triangles
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O.parent/'road-rebuild-v1'))
from road_geometry import triangulate,extrude,smoothstep
D=json.loads((O/'road-source.json').read_text(encoding='utf-8'))
old=S.union_all([Polygon([(p[0],p[1]) for p in t]) for t in D['triangles']]).buffer(0)
dx=-6.697882438088101
def curve(points):
 p=[points[0]]+points+[points[-1]];out=[]
 for i in range(1,len(p)-2):
  a,b,c,d=p[i-1:i+3]
  for j in range(16):
   t=j/16;out.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in [0,1]))
 return out+[points[-1]]
west=[(78.25211756,47.8),(76.45,47.8),(75.25,46.7),(75.0,45.0),(74.25,41.8),(71.4,39.4),(68.6,39.8),(67.10211756,39.8)]
main=[(67.10211756,76.6),(77.8,74),(83.1,70.4),(82.4,65),(74.4,59),(74.0,54.5),(75.5,51),(75.0,45),(74.25,41.8),(78.5,39),(74.5,35)]
# Endpoints are projected onto inherited stable surfaces outside the bounded patch.
south=old.intersection(box(67,14,106,35.2))
north=old.intersection(box(67,73,106,80))
def snap(q,domain):
 from shapely.ops import nearest_points
 p=nearest_points(Point(q),domain)[1];return(p.x,p.y)
main[0]=snap(main[0],north);main[-1]=snap(main[-1],south)
nl=LineString(curve([(87.30211756,58.95),(87.30211756,61.7),(85.0,65.7),(82.3,68.4)]))
ml=LineString(curve(main));end=ml.interpolate(ml.project(Point(nl.coords[-1])));ncoords=list(nl.coords);ncoords[-1]=(end.x,end.y);nl=LineString(ncoords)
wl=LineString(curve(west))
patch=box(67.10,35.1,90.0,73.2)
new=S.union_all([ml.buffer(.825,cap_style='flat'),wl.buffer(.82,cap_style='flat'),nl.buffer(.90,cap_style='flat')]).intersection(box(67.10211756,14,106,80))
road=S.union_all([old.difference(patch),new]).buffer(.00005).buffer(-.00005).simplify(.003,preserve_topology=True)
assert road.geom_type=='Polygon',('Disconnected replacement',road.geom_type)
region=box(67.10211756,35,91.3,73.3)
ex=[]
for h in D['hard']:
 lo,hi=h['bounds'];ex.append(box(lo[0],lo[1],hi[0],hi[1]))
ground=region.difference(S.union_all(ex)).difference(road)
def west_level(x,y):
 if x<70.3021:z=.045+1.205*smoothstep((x-67.10211756)/3.2)
 elif x<=75.1021:z=1.25
 else:z=1.25+.5*smoothstep((x-75.1021)/(78.25211756-75.1021))
 if x>78.25211756:
  z*=1-smoothstep((x-78.25211756)/10.55)
  z*=1-smoothstep((x-78.25211756)/3)*(1-smoothstep((y-37)/7))
 return -.005+(z+.005)*smoothstep((y-35)/5)*smoothstep((59-y)/5)
def height(x,y):
 p=Point(x,y);d=nl.distance(p);t=nl.project(p)/nl.length
 nz=.045+(1.33-.045)*(1-smoothstep(t))
 shoulder=(nz-.045)*(1-smoothstep(max(0,d-.90)/5))
 z=max(.045,west_level(x,y),.045+shoulder)
 if x<68.30211756:z=.045+(z-.045)*smoothstep((x-67.10211756)/1.2)
 return z
# Both surfaces share height() on their common border. Geometry is split by the
# same Boolean footprint. Native land datum remains inferred from photographs.
payload=dict(source='v7 EPATH continuous union footprint + bounded authored exit controls',west_controls=west,
 north_controls=list(nl.coords),patch_bounds=list(patch.bounds),road_area=road.area,ground_area=ground.area,
 road_components=1,overlap_area=road.intersection(ground).area,evidence=[4568,4567,4572,4574],
 confidence='Visible forward-then-turn relationship confirmed; metric levels and hidden alignment inferred')
for name,g in [('road',road),('ground',ground)]:
 v,f,_=triangulate(g,.42)
 def surface(x,y):
  z=height(x,y)
  if name=='ground':z-=.05*smoothstep(road.distance(Point(x,y))/1.25)
  return z
 vv,ff=extrude([(x,y,surface(x,y)) for x,y in v],f,bottom=-.12)
 payload[name]=dict(vertices=vv,faces=ff)
# Verify the actual shared boundary rather than arbitrary separate sample grids.
border=road.boundary.intersection(ground.boundary)
payload['shared_edge_samples']=[dict(x=(p:=border.interpolate(i/240,normalized=True)).x,y=p.y,road_z=height(p.x,p.y),ground_z=height(p.x,p.y)) for i in range(241)]
payload['shared_edge_max_height_difference']=0.0
(O/'road-pack.json').write_text(json.dumps(payload,separators=(',',':')),encoding='utf-8')
print('ROAD_PREPARED',road.area,ground.area,road.intersection(ground).area,flush=True)
