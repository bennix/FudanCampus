"""Union roof projections, preserving open courtyards as polygon holes (requires shapely)."""
import json
from pathlib import Path
from shapely.geometry import Polygon
from shapely.ops import unary_union
R=Path(__file__).resolve().parents[1]
triangles=json.loads((R/'field-review/campus-photo-integration/walk-roofs.json').read_text())
u=unary_union([Polygon(t) for t in triangles]).buffer(.06).simplify(.025,preserve_topology=True)
polys=list(u.geoms) if hasattr(u,'geoms') else [u]
result=[]
for p in polys:
 if p.area<.3:continue
 result.append({'bounds':list(p.bounds),'rings':[list(p.exterior.coords)]+[list(h.coords) for h in p.interiors]})
(R/'web/public/walk-interiors.json').write_text(json.dumps(result,separators=(',',':'))+'\n')
print('SEALED_INTERIORS',len(result),'holes',sum(len(p['rings'])-1 for p in result))
