"""Read-only geometric acceptance checks; run against a loaded blend."""
import bpy
import json
import math
from mathutils import Vector

objects = [o for o in bpy.data.objects if o.type == 'MESH']
checks = {}
checks['only_building_17'] = all(str(o.get('building_id')) == '17' for o in objects)
checks['side_door_present'] = any('side entrance door' in o.name for o in objects)
checks['side_canopy_present'] = any('side canopy ribs' in o.name for o in objects)
checks['balcony_return_glazing'] = any('balcony return glazing' in o.name for o in objects)
checks['recessed_entry'] = any('entry recess floor' in o.name for o in objects)
checks['finite_vertices'] = all(math.isfinite(v) for o in objects for p in o.data.vertices for v in p.co)
checks['no_degenerate_faces'] = all(p.area > 1e-10 for o in objects for p in o.data.polygons)
triangles = sum(len(p.vertices)-2 for o in objects for p in o.data.polygons)
checks['triangle_budget_180000'] = 0 < triangles <= 180000
shaft = [o for o in objects if o.name == 'T4 rear stair tower']
checks['rear_tower_above_roof'] = bool(shaft) and max((shaft[0].matrix_world @ Vector(c)).z for c in shaft[0].bound_box) > 21
checks['chinese_lettering_mesh'] = any('lettering' in o.name and len(o.data.vertices) > 100 for o in objects)
print('GEOMETRY_CHECKS', json.dumps({'checks': checks, 'triangles': triangles}, ensure_ascii=False))
assert all(checks.values()), 'Failed acceptance checks: ' + ', '.join(k for k,v in checks.items() if not v)
