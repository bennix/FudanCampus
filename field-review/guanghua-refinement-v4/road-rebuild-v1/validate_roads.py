"""Independent checks on serialized output, including ports and protected files."""
import sys,json,hashlib
from pathlib import Path
from collections import Counter
import numpy as np
import shapely as S
from shapely.geometry import shape,Point
from road_geometry import topology,check_solid,clean
O=Path(__file__).resolve().parent;R=O.parents[2];B=O/sys.argv[-1]
D=json.loads((B/'mesh-payload.json').read_text());features=json.loads((B/'domains.geojson').read_text())['features']
domains={f['properties']['kind']:shape(f['geometry']) for f in features}
results={}
for kind in ['road','terrain']:
    d=D[kind];n=len(d['vertices'])//2;vertices=d['vertices'][:n];faces=d['faces'][:d['top_faces']]
    canonical=S.segmentize(clean(domains[kind]),.25*.95)
    r,b=topology(vertices,faces,canonical);r['solid']=check_solid(d['vertices'],d['faces'])
    r['precision_grid_boundary_change']=canonical.hausdorff_distance(domains[kind])
    assert r['precision_grid_boundary_change']<2e-5
    assert all(r[k]==0 for k in ['nonmanifold_edges','degenerate_or_reversed_faces','duplicate_faces','internal_open_edges']),(kind,r)
    assert r['coverage_error_area']<1e-5 and abs(r['overlap_area'])<1e-5
    assert r['solid']['open_edges']==r['solid']['nonmanifold_edges']==0 and r['solid']['signed_volume']>0
    assert np.isfinite(np.asarray(d['vertices'])).all()
    results[kind]=r
assert results['road']['components']==1
old=json.loads((O/'protected-files.json').read_text())
assert all(hashlib.sha256((R/p).read_bytes()).hexdigest()==h for p,h in old.items())
results['protected_files_checked']=len(old)
results['road_terrain_overlap_area']=domains['road'].intersection(domains['terrain']).area
residual=domains['road'].intersection(domains['terrain'])
results['road_terrain_overlap_outside_precision_band']=residual.difference(domains['road'].boundary.buffer(2e-5)).area
assert results['road_terrain_overlap_area']<domains['road'].length*2e-5
assert results['road_terrain_overlap_outside_precision_band']<1e-10
results['ports']=json.loads((B/'geometry-validation.json').read_text())
results['status']='serialized_geometry_checks_passed; site profile is not accepted'
(B/'independent-validation.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
print('INDEPENDENT_VALIDATION_PASSED',len(old),'protected files')
