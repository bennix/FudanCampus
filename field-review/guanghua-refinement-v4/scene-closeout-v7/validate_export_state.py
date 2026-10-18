"""Exercise export state restoration in a disposable scene; never load a model."""
import hashlib
import json
import math
import struct
import sys
from pathlib import Path
from types import SimpleNamespace

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import export_visible_glb as helper

TEST_GLB = OUT / 'temporary-export-state-test.glb'
assert not TEST_GLB.exists(), 'Do not overwrite an existing test file'
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
view_layer = bpy.context.view_layer


def material(name, color):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    value.use_nodes = True
    value.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (*color, 1)
    return value


def snapshot():
    objects = {}
    for obj in scene.objects:
        objects[obj.name] = dict(
            type=obj.type, data=obj.data.name if obj.data else None,
            matrix=[list(row) for row in obj.matrix_world],
            hide=obj.hide_get(), hide_render=obj.hide_render,
            hide_viewport=obj.hide_viewport, selected=obj.select_get(),
            properties=dict(obj.items()),
            materials=[m.name if m else None for m in obj.data.materials] if obj.data else [],
            body=obj.data.body if obj.type == 'FONT' else None)
    return dict(objects=objects, meshes=sorted(bpy.data.meshes.keys()),
                datablock_objects=sorted(bpy.data.objects.keys()),
                active=view_layer.objects.active.name if view_layer.objects.active else None)


def bounds(obj):
    points = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    return [[min(point[axis] for point in points) for axis in range(3)],
            [max(point[axis] for point in points) for axis in range(3)]]


for index, name in enumerate(['visible_mesh', 'viewport_hidden_mesh', 'render_hidden_mesh']):
    bpy.ops.mesh.primitive_cube_add(size=.2, location=(index, 0, 0))
    obj = bpy.context.object
    obj.name = name
    obj['feature_id'] = name
    obj.data.materials.append(material(name + '_material', (.2, .3, .4)))
    obj.hide_render = name == 'render_hidden_mesh'

font_path = Path('C:/Windows/Fonts/simhei.ttf')
assert font_path.is_file(), 'The verification font must be available'
font = bpy.data.fonts.load(str(font_path))
text_specs = [
    ('WB1__text__光华楼广场自行车库', '光华楼广场自行车库', 'WB1'),
    ('WB2__text__光华楼广场自行车库', '光华楼广场自行车库', 'WB2'),
    ('SIGN__text__FUDAN', 'FUDAN', 'SIGN')]
source_texts = {}
for index, (name, body, feature) in enumerate(text_specs):
    curve = bpy.data.curves.new(name + '_curve', 'FONT')
    curve.body = body
    curve.font = font
    curve.resolution_u = 2
    curve.render_resolution_u = 2
    curve.extrude = .005
    curve.materials.append(material(feature + '_material', (.3 + index * .2, .5, .1)))
    obj = bpy.data.objects.new(name, curve)
    scene.collection.objects.link(obj)
    obj.location = (index * 3, 2, .3 + index * .1)
    obj.rotation_euler = (math.pi / 2, 0, index * .13)
    obj.scale = (.2 + index * .02,) * 3
    obj['feature_id'] = feature
    obj['verification_marker'] = 'disposable-scene-only'
    source_texts[name] = obj

view_layer.update()
for obj in view_layer.objects:
    obj.select_set(False)
hidden = bpy.data.objects['viewport_hidden_mesh']
hidden.hide_set(True)
source_texts[text_specs[1][0]].hide_set(True)
bpy.data.objects['visible_mesh'].select_set(True)
source_texts[text_specs[0][0]].select_set(True)
view_layer.objects.active = hidden
baseline = snapshot()
assert baseline['objects']['viewport_hidden_mesh']['hide']
assert not baseline['objects']['viewport_hidden_mesh']['selected']
assert baseline['objects'][text_specs[0][0]]['selected']
expected_bounds = {name: bounds(obj) for name, obj in source_texts.items()}
captured = []
real_export = bpy.ops.export_scene.gltf


def inspect_temporary_texts():
    records = []
    for name, original in source_texts.items():
        copy = bpy.data.objects.get(name)
        assert copy is not None and copy.type == 'MESH'
        assert original.name == name + '__editable_export_source'
        assert copy.data.vertices and copy.data.polygons
        assert max(abs(a - b) for actual, expected in zip(copy.matrix_world, original.matrix_world)
                   for a, b in zip(actual, expected)) < 1e-6
        assert list(copy.data.materials) == list(original.data.materials)
        assert dict(copy.items()) == dict(original.items())
        assert max(abs(a - b) for actual, expected in zip(bounds(copy), expected_bounds[name])
                   for a, b in zip(actual, expected)) < .001
        assert copy.select_get() and not copy.hide_get()
        records.append(dict(name=name, feature_id=copy['feature_id'],
                            vertices=len(copy.data.vertices), polygons=len(copy.data.polygons)))
    captured.append(records)


def normal_export(**options):
    inspect_temporary_texts()
    return real_export(**options)


def failed_export(**options):
    inspect_temporary_texts()
    raise RuntimeError('Injected GLB export failure')


def set_export(operation):
    helper.bpy = SimpleNamespace(context=bpy.context, data=bpy.data,
                                ops=SimpleNamespace(object=bpy.ops.object,
                                                    export_scene=SimpleNamespace(gltf=operation)))


report = dict(disposable_scene=True, user_models_loaded=False,
              helper_sha256=hashlib.sha256((ROOT / 'scripts/export_visible_glb.py').read_bytes()).hexdigest())
try:
    set_export(normal_export)
    records = helper.export_visible_glb(TEST_GLB)
    assert len(records) == 3 and {r['name'] for r in records} == set(source_texts)
    assert snapshot() == baseline, 'Successful export changed scene state'
    report['normal_export_restores_state'] = True
    report['normal_text_meshes'] = captured[-1]

    set_export(failed_export)
    try:
        helper.export_visible_glb(TEST_GLB)
        raise AssertionError('Injected failure did not propagate')
    except RuntimeError as error:
        assert str(error) == 'Injected GLB export failure'
    assert snapshot() == baseline, 'Failed export changed scene state'
    report['injected_export_failure_restores_state'] = True

    # Fail after earlier text resources have already been registered. This
    # exercises partial preparation cleanup as well as the export error path.
    last_text = source_texts[text_specs[-1][0]]
    original_body = last_text.data.body
    last_text.data.body = ''
    view_layer.update()
    empty_baseline = snapshot()
    try:
        helper.export_visible_glb(TEST_GLB)
        raise AssertionError('Empty lettering did not fail')
    except ValueError as error:
        assert str(error) == 'Empty lettering: ' + text_specs[-1][0]
    assert snapshot() == empty_baseline, 'Partial preparation failure changed scene state'
    last_text.data.body = original_body
    view_layer.update()
    assert snapshot() == baseline
    report['partial_text_preparation_failure_restores_state'] = True
    report['no_temporary_objects_or_meshes_after_each_call'] = True
    report['original_selections_and_hidden_active_object_restored'] = True

    raw = TEST_GLB.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    document = json.loads(raw[20:20 + length])
    nodes = {node['name']: node for node in document['nodes'] if 'mesh' in node}
    assert set(nodes) == set(source_texts) | {'visible_mesh', 'viewport_hidden_mesh'}
    for name, source in source_texts.items():
        assert nodes[name]['extras'] == dict(source.items())
        mesh = document['meshes'][nodes[name]['mesh']]
        assert all(document['accessors'][p['attributes']['POSITION']]['count'] > 0
                   for p in mesh['primitives'])
    report['glb_has_exact_expected_mesh_nodes_and_text_metadata'] = True
    report['glb_bytes'] = len(raw)

    # Reimport only the small synthetic export, after restoration checks finish.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(TEST_GLB))
    reimported = []
    for name, _body, feature in text_specs:
        obj = bpy.data.objects[name]
        assert obj.type == 'MESH' and obj.data.polygons
        assert obj['feature_id'] == feature
        assert max(abs(a - b) for actual, expected in zip(bounds(obj), expected_bounds[name])
                   for a, b in zip(actual, expected)) < .001
        reimported.append(dict(name=name, feature_id=feature, vertices=len(obj.data.vertices)))
    report['three_texts_reimport_as_nonempty_meshes_at_source_bounds'] = reimported
    report['passed'] = True
    (OUT / 'export-state-validation.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('EXPORT_STATE_VALIDATION_PASSED', json.dumps(report, ensure_ascii=False), flush=True)
finally:
    helper.bpy = bpy
    if TEST_GLB.exists():
        TEST_GLB.unlink()
