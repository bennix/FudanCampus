"""Independent planar validation of the applied terrain difference."""
import json,hashlib
from pathlib import Path
import shapely as S
from shapely.geometry import Polygon
O=Path(__file__).resolve().parent;p=json.loads((O/'ground-trim-pack.json').read_text());q=json.loads((O/'ground-trim-native-top.json').read_text())
domain=S.from_geojson(p['top_domain_geojson']);old=S.from_geojson(p['old_domain_geojson']);expected=S.from_geojson(p['expected_remaining_geojson'])
actual=S.union_all([Polygon([v[:2] for v in t]) for t in q]).buffer(0)
report=dict(actual_area=actual.area,expected_area=expected.area,duplicate_projected_area=actual.intersection(domain).area,domain_exterior_error_area=actual.symmetric_difference(expected).area,original_holes_or_exterior_filled_area=actual.difference(old).area,source_sha256=p['source_sha256'],final_source_sha256=hashlib.sha256((O/'guanghua-closeout-final.blend').read_bytes()).hexdigest(),checks=['Difference applied to actual new ground projection','Original holes not filled','No remaining duplicate ground area'],tolerance_note='Float32 native vertices; exact source-domain subtraction with small boundary representation error separately reported')
(O/'ground-trim-planar-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report),flush=True)
assert report['duplicate_projected_area']<=1e-6,report
assert report['original_holes_or_exterior_filled_area']<=1e-6,report
assert report['domain_exterior_error_area']<=.001,report
