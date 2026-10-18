"""Resume inspection and renders from the finished checkpoint; never save or rebuild it."""
import bpy
import hashlib
import json
import math
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

O = Path(__file__).resolve().parent
INFO = json.loads((O / 'build-info.json').read_text())
BASE = O.parent / 'forecourt-v1' / 'forecourt-entry-v1.blend'
CHECKPOINT = O / 'forecourt-complete-v2.blend'
ASSETS = [BASE, CHECKPOINT, O / 'forecourt-complete-v2.glb', O / 'poet-donkey.glb']


def sha(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def digest(ob):
    vertices = np.empty(len(ob.data.vertices) * 3, np.float32)
    ob.data.vertices.foreach_get('co', vertices)
    return hashlib.sha256(vertices.tobytes() + str(list(ob.matrix_world)).encode()).hexdigest()


def bounds(points):
    return {'min': [min(p[i] for p in points) for i in range(3)],
            'max': [max(p[i] for p in points) for i in range(3)]}


original = {p.name: sha(p) for p in ASSETS}
assert original[BASE.name] == INFO['baseline_sha256']
bpy.ops.wm.open_mainfile(filepath=str(CHECKPOINT))
s = bpy.context.scene
assert all(digest(bpy.data.objects[name]) == expected for name, expected in INFO['protected'].items())
root = bpy.data.objects['POET_DONKEY photo placed landmark']
plate = bpy.data.objects['POET_DONKEY inset nameplate']
text = bpy.data.objects['POET_DONKEY 驢背詩思']
assert plate.type == text.type == 'MESH'
assert plate.get('feature_id') == text.get('feature_id') == 'POET_DONKEY'
assert root.get('label') == '驴背诗思'
local_from_world = root.matrix_world.inverted()
deps = bpy.context.evaluated_depsgraph_get()


def local_mesh(ob):
    evaluated = ob.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    transform = local_from_world @ evaluated.matrix_world
    points = [transform @ v.co for v in mesh.vertices]
    faces = [tuple(p.vertices) for p in mesh.polygons]
    evaluated.to_mesh_clear()
    return points, faces


plate_points, _ = local_mesh(plate)
text_points, _ = local_mesh(text)
pb, tb = bounds(plate_points), bounds(text_points)
assert all(math.isfinite(c) for p in plate_points + text_points for c in p)
assert pb['min'][0] < tb['min'][0] < tb['max'][0] < pb['max'][0]
assert pb['min'][2] < tb['min'][2] < tb['max'][2] < pb['max'][2]
assert tb['max'][1] < pb['min'][1], (pb, tb)
assert abs((pb['min'][1] + pb['max'][1]) / 2 + 1.055) < 1e-5

# Every evaluated pedestal vertex stays behind the back of the plate.
stone_objects = [ob for ob in s.objects if ob.type == 'MESH' and
                 ob.name.startswith(('POET_DONKEY base core', 'POET_DONKEY rough ashlar',
                                     'POET_DONKEY side ashlar', 'POET_DONKEY dressed coping'))]
stone_points, stone_faces = [], []
for ob in stone_objects:
    points, faces = local_mesh(ob)
    offset = len(stone_points)
    stone_points.extend(points)
    stone_faces.extend(tuple(i + offset for i in face) for face in faces)
stone_front = min(p.y for p in stone_points)
clearance = stone_front - pb['max'][1]
assert clearance > 0, clearance
stone_tree = BVHTree.FromPolygons(stone_points, stone_faces)
support_distances = []
for x in np.linspace(pb['min'][0] + .035, pb['max'][0] - .035, 9):
    for z in np.linspace(pb['min'][2] + .035, pb['max'][2] - .035, 5):
        hit, normal, face, distance = stone_tree.ray_cast(Vector((x, pb['max'][1], z)), Vector((0, 1, 0)), .3)
        assert hit is not None, (x, z)
        support_distances.append(distance)


def read_glb(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    length, kind = struct.unpack_from('<I4s', raw, 12)
    assert kind == b'JSON'
    data = json.loads(raw[20:20 + length])
    assert all('bufferView' in im for im in data.get('images', []))
    world = {}

    def visit(index, parent):
        node = data['nodes'][index]
        if 'matrix' in node:
            a = node['matrix']
            local = Matrix([[a[c * 4 + r] for c in range(4)] for r in range(4)])
        else:
            q = node.get('rotation', [0, 0, 0, 1])
            local = Matrix.LocRotScale(Vector(node.get('translation', [0, 0, 0])),
                                      Quaternion((q[3], q[0], q[1], q[2])),
                                      Vector(node.get('scale', [1, 1, 1])))
        world[index] = parent @ local
        for child in node.get('children', []):
            visit(child, world[index])

    for index in data['scenes'][data.get('scene', 0)]['nodes']:
        visit(index, Matrix.Identity(4))
    exported = {}
    for index, node in enumerate(data['nodes']):
        if node.get('name') not in (plate.name, text.name):
            continue
        assert node.get('extras', {}).get('feature_id') == 'POET_DONKEY'
        points = []
        for primitive in data['meshes'][node['mesh']]['primitives']:
            accessor = data['accessors'][primitive['attributes']['POSITION']]
            for x in (accessor['min'][0], accessor['max'][0]):
                for y in (accessor['min'][1], accessor['max'][1]):
                    for z in (accessor['min'][2], accessor['max'][2]):
                        p = world[index] @ Vector((x, y, z))
                        points.append(local_from_world @ Vector((p.x, -p.z, p.y)))
        exported[node['name']] = bounds(points)
    assert set(exported) == {plate.name, text.name}
    for name, expected in ((plate.name, pb), (text.name, tb)):
        assert max(abs(exported[name][side][i] - expected[side][i])
                   for side in ('min', 'max') for i in range(3)) < .002, (name, exported[name], expected)
    return {'bytes': len(raw), 'embedded_images': len(data.get('images', [])),
            'plaque_and_inscription_match_checkpoint': True}


exports = {path.name: read_glb(path) for path in ASSETS[2:]}
report = {
    'reviewed_at_utc': datetime.now(timezone.utc).isoformat(),
    'mode': 'resume finished checkpoint; inspect and render only',
    'source_asset_sha256': original,
    'checkpoint_reopened': True,
    'protected_geometry_matches_build_info': True,
    'protected_object_count': len(INFO['protected']),
    'inscription': '驢背詩思',
    'inscription_is_exportable_mesh': True,
    'inscription_inside_plate': True,
    'inscription_in_front_of_plate_model_units': pb['min'][1] - tb['max'][1],
    'plate_bounds_in_landmark_coordinates': pb,
    'inscription_bounds_in_landmark_coordinates': tb,
    'rough_stone_clearance_lower_bound_model_units': clearance,
    'pedestal_support_rays': len(support_distances),
    'pedestal_support_distance_range_model_units': [min(support_distances), max(support_distances)],
    'exports': exports,
    'render_complete': False,
}
(O / 'final-review-validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print('RESUMED_CHECKPOINT_AND_PLAQUE_VERIFIED', json.dumps({
    'stone_clearance': clearance, 'support_rays': len(support_distances),
    'text_front_gap': report['inscription_in_front_of_plate_model_units']}), flush=True)

if '--inspect-only' not in sys.argv:
    def camera(name, location, target, scale):
        data = bpy.data.cameras.new(name)
        ob = bpy.data.objects.new(name, data)
        s.collection.objects.link(ob)
        ob.location = root.matrix_world @ Vector(location)
        focus = root.matrix_world @ Vector(target)
        ob.rotation_euler = (focus - ob.location).to_track_quat('-Z', 'Y').to_euler()
        data.type = 'ORTHO'
        data.ortho_scale = scale
        data.clip_end = 1500
        return ob

    front = camera('REVIEW ONLY plaque front', (0, -5, .47), (0, -1.055, .47), 1.65)
    oblique = camera('REVIEW ONLY plaque oblique', (2.3, -4.6, 1.55), (0, -.95, .48), 2.45)
    batch = [('final-plaque-front', front, (1600, 1000)),
             ('final-plaque-oblique', oblique, (1600, 1000)),
             ('final-statue', bpy.data.objects[INFO['cameras']['statue']], (1800, 1350))]
    s.render.engine = 'CYCLES'
    s.cycles.samples = 64
    s.cycles.use_denoising = True
    s.render.resolution_percentage = 100
    outputs = []
    for name, cam, resolution in batch:
        s.camera = cam
        s.render.resolution_x, s.render.resolution_y = resolution
        s.render.filepath = str(O / (name + '.png'))
        bpy.ops.render.render(write_still=True)
        outputs.append({'path': name + '.png', 'resolution': resolution, 'samples': 64,
                        'camera': cam.name, 'sha256': sha(O / (name + '.png'))})
        report['renders'] = outputs
        (O / 'final-review-validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
    report['render_complete'] = True

assert {p.name: sha(p) for p in ASSETS} == original
report['all_source_assets_unchanged'] = True
(O / 'final-review-validation.json').write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
print('RESUMED_FINAL_REVIEW_COMPLETE', flush=True)
