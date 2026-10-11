"""Exchange the two long elevations of v13; keep both end elevations in place."""
import ast
import bpy
import json
import math
import shutil
import sys
from pathlib import Path
from mathutils import Matrix, Vector

O = Path(__file__).resolve().parent
R = O.parents[2]
V13 = O.parent / 'hanbing-final-v13'
WEB = R / 'web/public/hanbing-final-v14'
WEB.mkdir(exist_ok=True)
sys.path.insert(0, str(V13))
from geometry import Builder

bpy.ops.wm.open_mainfile(filepath=str(V13 / 'FudanCampus-campus-hanbing-final-v13.blend'))
scene = bpy.context.scene
coll = bpy.data.collections['Hanbing_42_Final_v13']
anchor = bpy.data.objects['HB42_V13_BASE_HB42_FS5_01_MainWallMass'].matrix_world.copy()
reflection = anchor @ Matrix.Diagonal((1, -1, 1, 1)) @ anchor.inverted()
turn = anchor @ Matrix.Rotation(math.pi, 4, 'Z') @ anchor.inverted()
changed = []

def bounds(o):
    points = [anchor.inverted() @ o.matrix_world @ Vector(v) for v in o.bound_box]
    return [(min(p[k] for p in points), max(p[k] for p in points)) for k in range(3)]

for o in coll.objects:
    if o.type != 'MESH':
        continue
    n = o.name
    bb = bounds(o)
    # Short-elevation components and fittings retain their world-space placement.
    if o.get('facade') in ('N', 'S') or any(s in n for s in ('OV6_N_', 'OV6_S_')):
        continue
    if n.startswith(('HB42_V13_N_', 'HB42_V13_S_', 'HB42_V13_North_')):
        continue
    if 'EndProjection' in n or 'UnifiedRoof' in n:
        continue
    is_entry = n.startswith(('HB42_V13_W_', 'HB42_V13_WestPlaque_')) or ('lettering' in o.get('role', '') and bb[1][0] > 5)
    is_long_side = bb[1][0] > 3.5 or bb[1][1] < -3.5
    is_host = 'MainWallMass' in n or 'ClerestoryWallZone' in n
    if is_entry:
        # A rigid half-turn keeps lettering readable and plaque/column relationships intact.
        o.matrix_world = turn @ o.matrix_world
    elif is_long_side or is_host:
        # Bake the reflection with corrected winding, preserving UV loop correspondence.
        local_reflection = o.matrix_world.inverted() @ reflection @ o.matrix_world
        o.data = o.data.copy()
        o.data.transform(local_reflection)
        o.data.flip_normals()
        o.data.update()
    else:
        continue
    o['placement_revision'] = 'v14 long elevations exchanged'
    changed.append(n)

# Keep the existing outer road junction; extend the flat entrance apron on the new side.
apron = bpy.data.objects['HB42_CONTEXT_GradedApron']
apron.data = apron.data.copy()
for v in apron.data.vertices:
    if abs(v.co.z - .018) < .0001:
        if abs(v.co.y + 7) < .001:
            v.co.y = -9
        elif abs(v.co.y - 9) < .001:
            v.co.y = 7
apron.data.update()
scene['hanbing_placement_revision'] = 'v14: long elevations exchanged; end elevations fixed'
camera = scene.camera
camera.location = anchor @ Vector((57, -74, 73))
camera.rotation_euler = (anchor @ Vector((0, -4, 2)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 48
scene.render.resolution_x = 1800
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.film_transparent = False
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(O / 'campus-aerial-v14.png')
bpy.context.preferences.filepaths.save_version = 0
bpy.context.view_layer.update()
door = bpy.data.objects['HB42_V13_Component_W_06_F1_door']
door_bounds = bounds(door)
assert door_bounds[1][1] < -5.8, door_bounds
assert sum(bool(o.get('component_type')) for o in coll.objects) == 118
bpy.ops.wm.save_as_mainfile(filepath=str(O / 'FudanCampus-campus-hanbing-v14.blend'))

# Reuse the existing material batching/export code without rerunning v13 construction.
tree = ast.parse((V13 / 'deliver.py').read_text(encoding='utf8'))
for node in tree.body:
    if isinstance(node, ast.FunctionDef) and node.name in ('web_batches', 'export', 'analyze'):
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(V13 / 'deliver.py'), 'exec'))
import struct
hbweb, batch = web_batches(coll)
export(WEB / 'hanbing-only.glb', hbweb)
campusmesh = [o for o in scene.objects if o.type == 'MESH' and not o.hide_render and o.name not in coll.objects and o.name not in batch.objects]
export(WEB / 'campus.glb', campusmesh + hbweb)
stats = {'hanbing': analyze(WEB / 'hanbing-only.glb'), 'campus': analyze(WEB / 'campus.glb')}
(WEB / 'statistics.json').write_text(json.dumps(stats, indent=2), encoding='utf8')
shutil.copy2(V13 / 'buildings.json', WEB / 'buildings.json')
(O / 'change-summary.json').write_text(json.dumps({'changed_objects': changed, 'door_local_bounds': door_bounds, 'end_elevations_retained': True, 'web_assets': str(WEB)}, indent=2), encoding='utf8')
print('V14_SAVED_AND_EXPORTED', len(changed), flush=True)
# Native objects already contain the final appearance; suppress export-only duplicates.
for o in batch.objects:
    o.hide_render = True
bpy.ops.render.render(write_still=True)
print('V14_AERIAL_COMPLETE', flush=True)
