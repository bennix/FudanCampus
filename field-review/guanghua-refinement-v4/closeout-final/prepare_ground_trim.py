"""Prepare exact footprint cutter from the actual C04 upward surface."""
import json,sys,hashlib,argparse
from pathlib import Path
import shapely as S
from shapely.geometry import Polygon
O=Path(__file__).resolve().parent
r=json.loads((O/'native-audit-geometry.json').read_text(encoding='utf-8'))
old,new=r['ground'];v=new['vertices']
domain=S.union_all([Polygon([v[i][:2] for i in f['vertices']]) for f in new['faces'] if f['normal'][2]>.00001]).buffer(0)
assert domain.is_valid and not domain.is_empty
# Remove only collinear tessellation vertices, keeping actual float32 boundaries.
clean=domain.simplify(1e-8,preserve_topology=True)
assert domain.symmetric_difference(clean).area<1e-6
# Float32 native Boolean vertices need a tiny conservative cut at the new border.
# This is below the 1e-4 interface tolerance; original exterior vertices are guarded.
parser=argparse.ArgumentParser();parser.add_argument('--padding',type=float,default=0.0);args=parser.parse_args();padding=args.padding
assert 0<=padding<=.00002
if padding:clean=clean.buffer(padding,quad_segs=1,join_style='mitre').simplify(1e-8,preserve_topology=True)
vertices=[];faces=[];lookup={}
def vi(p):
 k=(float(p[0]),float(p[1]))
 if k not in lookup:lookup[k]=len(vertices);vertices.append(k)
 return lookup[k]
for t in S.constrained_delaunay_triangles(clean).geoms:
 q=list(t.exterior.coords)[:3];ids=tuple(vi(p) for p in q)
 if (q[1][0]-q[0][0])*(q[2][1]-q[0][1])-(q[1][1]-q[0][1])*(q[2][0]-q[0][0])<0:ids=(ids[0],ids[2],ids[1])
 faces.append(ids)
sys.path.insert(0,str(O.parent/'road-rebuild-v1'));from road_geometry import extrude,check_solid
vv,ff=extrude([(x,y,10) for x,y in vertices],faces,bottom=-10)
check=check_solid(vv,ff);assert check['nonmanifold_edges']==0 and check['open_edges']==0 and check['signed_volume']>0
original=S.union_all([Polygon([old['vertices'][i][:2] for i in f['vertices']]) for f in old['faces'] if f['normal'][2]>.99 and abs(old['vertices'][f['vertices'][0]][2]+.005)<1e-5]).buffer(0)
protected=[]
for fi,f in enumerate(old['faces']):
 points=[old['vertices'][i] for i in f['vertices']]
 # Every existing loop outside the removed domain must retain position and UV.
 for j,p in enumerate(points):
  if not clean.buffer(.000001).covers(S.Point(p[0],p[1])):
   protected.append(dict(position=p,material=f['material'],uv=f['uv'][j] if f['uv'] else None,source_face=fi))
source_sha=hashlib.sha256((O/'guanghua-closeout-final.blend').read_bytes()).hexdigest()
pack=dict(source_sha256=source_sha,extracted_geometry_sha256=r['source_sha256'],vertices=vv,faces=ff,top_domain_geojson=S.to_geojson(domain),cut_domain_geojson=S.to_geojson(clean),old_domain_geojson=S.to_geojson(original),expected_remaining_geojson=S.to_geojson(original.difference(clean)),cut_boundary_padding=padding,cut_area=clean.area,old_area=original.area,overlap_removed_area=original.intersection(clean).area,cutter_solid_check=check,protected_existing_loops=protected,method=f'Actual C04 upward-face union; constrained triangulation; 3D closed difference cutter with {padding:g} float32 border allowance. No elevation shift.')
(O/'ground-trim-pack.json').write_text(json.dumps(pack,separators=(',',':')),encoding='utf-8')
print('GROUND_TRIM_PREPARED',len(vv),len(ff),pack['overlap_removed_area'],len(protected),flush=True)
