import bpy, bmesh, json
from pathlib import Path
from mathutils import Vector

O = Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'diagnostic-west-entry.blend'))
rows = []
for ob in bpy.context.scene.objects:
    if ob.type != 'MESH':
        continue
    if not (ob.name.startswith(('W_ENTRY recessed', 'WPATH')) or ob.get('feature_id') in ('GROUND', 'WOPEN') or ob.name == 'V2 leaves WOPEN'):
        continue
    points = [ob.matrix_world @ v.co for v in ob.data.vertices]
    bm = bmesh.new(); bm.from_mesh(ob.data)
    row = dict(name=ob.name, parent=ob.parent.name if ob.parent else None,
               bounds=[[min(p[k] for p in points) for k in range(3)], [max(p[k] for p in points) for k in range(3)]],
               boundary_edges=sum(e.is_boundary for e in bm.edges),
               nonmanifold_edges=sum(not e.is_manifold for e in bm.edges), volume=bm.calc_volume(signed=True))
    bm.free()
    if ob.name.startswith(('WPATH', 'W_ENTRY recessed')):
        row['join_vertices'] = [list(p) for p in points if 74.9 < p.y < 75.1]
        row['north_vertices'] = [list(p) for p in points if p.y > 74.4]
    rows.append(row)
(O/'alignment-inspection.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2), flush=True)
