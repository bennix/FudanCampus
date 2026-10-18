"""Consolidate the latest native scene without reimporting superseded branch geometry.

Run with the project's Blender 4.4.3: blender -b --python <this file>.
This creates a new candidate baseline; it does not claim visual closeout.
"""
from pathlib import Path
import hashlib
import json
import sys

import bpy
import numpy as np
from mathutils import Vector

OUTDIR = Path(__file__).resolve().parent
REVIEW = OUTDIR.parent
ROOT = REVIEW.parents[1]
sys.path.insert(0, str(REVIEW / 'scene-unified-v5'))
from scene_fingerprints import sha, snapshot, write, plain, props, material_signature


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def other_objects():
    result = {}
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            continue
        row = dict(type=obj.type, matrix=plain(obj.matrix_world), properties=props(obj),
                   hide_render=obj.hide_render, hide_viewport=obj.hide_viewport,
                   hide_set=obj.hide_get())
        if obj.type == 'CAMERA':
            row['camera'] = {k: plain(getattr(obj.data, k)) for k in
                             ('type', 'lens', 'ortho_scale', 'clip_start', 'clip_end',
                              'sensor_width', 'sensor_height', 'shift_x', 'shift_y')}
        elif obj.type == 'LIGHT':
            row['light'] = {k: plain(getattr(obj.data, k)) for k in
                            ('type', 'energy', 'color', 'use_shadow')}
        result[obj.name] = row
    return result


def lettering():
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rows = {}
    for obj in bpy.context.scene.objects:
        if obj.type != 'FONT':
            continue
        mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
        try:
            assert mesh.vertices and mesh.polygons, ('Empty font evaluation', obj.name)
            vertex = np.empty(len(mesh.vertices) * 3, np.float32)
            mesh.vertices.foreach_get('co', vertex)
            assert np.isfinite(vertex).all(), obj.name
            indices = np.empty(len(mesh.loops), np.int32)
            mesh.loops.foreach_get('vertex_index', indices)
            points = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
            font = obj.data.font
            packed = getattr(font, 'packed_file', None)
            fontpath = Path(bpy.path.abspath(font.filepath)) if font.filepath else None
            font_hash = (hashlib.sha256(packed.data).hexdigest() if packed else
                         sha(fontpath) if fontpath and fontpath.is_file() else None)
            rows[obj.name] = dict(
                body=obj.data.body, feature_id=obj.get('feature_id'),
                vertices=len(mesh.vertices), polygons=len(mesh.polygons),
                evaluated_geometry_sha256=hashlib.sha256(vertex.tobytes() + indices.tobytes()).hexdigest(),
                world_bounds=[[min(p[i] for p in points) for i in range(3)],
                              [max(p[i] for p in points) for i in range(3)]],
                matrix=plain(obj.matrix_world), visible=not obj.hide_render,
                typography={k: plain(getattr(obj.data, k)) for k in
                            ('size', 'align_x', 'align_y', 'space_character', 'space_word',
                             'extrude', 'bevel_depth', 'resolution_u')},
                material_signatures=[material_signature(m) for m in mesh.materials],
                font_name=font.name, font_sha256=font_hash, font_packed=bool(packed),
                properties=props(obj))
        finally:
            bpy.data.meshes.remove(mesh)
    assert len(rows) == 3, rows.keys()
    for feature in ('WB1', 'WB2'):
        selected = [r for r in rows.values() if r['feature_id'] == feature]
        assert len(selected) == 1 and selected[0]['body'] == '光华楼广场自行车库'
        assert selected[0]['font_sha256'] and selected[0]['visible']
    assert any(r['feature_id'] == 'SIGN' and r['body'] == 'FUDAN' and r['visible']
               for r in rows.values())
    return rows


def metrics():
    triangles = 0
    tree_triangles = 0
    unique = set()
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        mesh = obj.data
        if mesh.as_pointer() not in unique:
            vertex = np.empty(len(mesh.vertices) * 3, np.float32)
            mesh.vertices.foreach_get('co', vertex)
            assert np.isfinite(vertex).all(), obj.name
            unique.add(mesh.as_pointer())
        if obj.hide_render:
            continue
        loops = np.empty(len(mesh.polygons), np.int32)
        mesh.polygons.foreach_get('loop_total', loops)
        count = int(np.maximum(loops - 2, 0).sum())
        triangles += count
        if obj.get('feature_id') == 'TREE_CANOPY_V6':
            tree_triangles += count
    return dict(visible_mesh_triangles_before_export=triangles,
                visible_v6_tree_triangles=tree_triangles,
                unique_meshes_with_finite_coordinates=len(unique),
                triangles_scope='Native visible mesh estimate before modifiers/font tessellation; not browser rendered triangles')


audit = read(REVIEW / 'scene-unified-v5/source-audit.json')
v5 = read(REVIEW / 'scene-unified-v5/version-manifest.json')
v6 = read(REVIEW / 'tree-canopy-v6/version-manifest.json')
expected_v5 = read(REVIEW / 'scene-unified-v5/expected-unified-snapshot.json')
expected_v6 = read(REVIEW / 'tree-canopy-v6/expected-snapshot.json')
validation_v5 = read(REVIEW / 'scene-unified-v5/validation.json')
assert all(not conflicts for conflicts in audit['object_conflicts'].values())
sources = dict(audit['sources'])
sources['unified_v5'] = dict(path=v5['scene'], sha256=v5['scene_sha256'])
sources['latest_tree_canopy_v6'] = dict(path=v6['scene'], sha256=v6['scene_sha256'])
for row in sources.values():
    assert sha(row['path']) == row['sha256'], ('Source changed', row['path'])

repairs = {}
for name in ('west-entry-v3', 'vegetation-v2'):
    row = read(REVIEW / 'garage-text-export' / (name + '.json'))
    assert sha(ROOT / row['source']) == row['source_sha256']
    assert sha(ROOT / row['target']) == row['after_sha256']
    repairs[name] = dict(source=row['source'], source_sha256=row['source_sha256'],
                         target=row['target'], target_sha256=row['after_sha256'],
                         source_unchanged=True, corrected_export_unchanged=True,
                         text_meshes=len(row['added_text_meshes']))

print('SOURCE_HASHES_PASSED', flush=True)
bpy.ops.wm.open_mainfile(filepath=v6['scene'])
actual = snapshot()
assert actual == expected_v6, 'Latest scene differs from its saved full mesh snapshot'
removed = set(v6['removed_tree_objects'])
protected = {n: row for n, row in expected_v5.items() if n not in removed}
assert len(protected) == 1794
assert all(actual.get(n) == row for n, row in protected.items())
assert not removed.intersection(actual)
assert len([o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get('feature_id') == 'E_WALK']) == 200
planter_names = [n for n, owner in v5['object_owners'].items() if owner == 'planters']
assert len(planter_names) == 4 and all(actual[n] == expected_v5[n] for n in planter_names)
labels = lettering()
other = other_objects()
stats = metrics()
features = sorted(set(o.get('feature_id') for o in bpy.context.scene.objects if o.get('feature_id')))
print('CONTENT_AUDIT_PASSED', len(actual), 'meshes;', len(labels), 'editable labels', flush=True)

scene = bpy.context.scene
scene['active_checkpoint'] = 'Guanghua unified closeout v7 candidate: three-way unified v5 + latest tree-canopy v6; editable labels retained'
scene['unified_version'] = 'guanghua-unified-closeout-v7'
scene['closeout_status'] = 'Unified baseline only; remaining visual/model/web tasks are listed in closeout-plan.md'
scene['closeout_visual_acceptance'] = False
scene['closeout_parent_sha256'] = v6['scene_sha256']
scene['closeout_export_helper'] = 'scripts/export_visible_glb.py: export_visible_glb; include evaluated FONT meshes'
scene['closeout_source_manifest'] = 'version-manifest.json'
bpy.ops.file.pack_all()
bpy.context.preferences.filepaths.save_version = 0
target = OUTDIR / 'guanghua-unified-closeout-v7.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(target), compress=True)
target_hash = sha(target)

bpy.ops.wm.open_mainfile(filepath=str(target))
reopened = snapshot()
assert reopened == actual, 'Saved scene changed mesh content'
assert other_objects() == other, 'Saved scene changed cameras/lights/other objects'
assert lettering() == labels, 'Saved scene changed editable or evaluated lettering'
for row in sources.values():
    assert sha(row['path']) == row['sha256'], ('Source overwritten', row['path'])
assert sha(target) == target_hash

manifest = dict(version='guanghua-unified-closeout-v7', date='2026-10-01',
                status='unified candidate baseline assembled and reopened; visual closeout remains planned',
                scene=str(target), scene_sha256=target_hash, bytes=target.stat().st_size,
                sources=sources, mesh_objects=len(actual),
                merge_method='Use already merged v5 plus latest v6 descendant; reconcile via complete content fingerprints, retain native fonts, do not append whole old branches or import old GLBs',
                branch_conflicts=audit['object_conflicts'],
                existing_text_export_repairs=repairs,
                export_helper=str(ROOT / 'scripts/export_visible_glb.py'),
                export_helper_sha256=sha(ROOT / 'scripts/export_visible_glb.py'),
                web_assets_updated=False, unified_glb_exported=False, user_visual_acceptance=False,
                remaining_scope='closeout-plan.md', metrics=stats,
                historical_visual_evidence=dict(
                    source_scene=v6['scene'], source_sha256=v6['scene_sha256'],
                    render_manifest=str(REVIEW / 'tree-canopy-v6/final-render-manifest.json'),
                    note='Existing v6 views are inherited evidence; they are not renders of v7. All mesh, font, camera and light content is unchanged by this consolidation.'),
                limits=['Native content consolidation only; visual/model/web closeout has not been completed',
                        'Photo cameras, absolute scale, additional trees and unseen geometry retain inferred/unknown status',
                        'No new full-scene collision certification or browser performance result'])
validation = dict(checkpoint_reopens=True, scene_sha256=target_hash,
                  all_six_native_source_hashes_unchanged=True,
                  mesh_objects=len(actual), exact_v6_mesh_snapshot_preserved=True,
                  v5_protected_non_tree_meshes_preserved=len(protected),
                  four_planter_material_objects_preserved=True,
                  east_path_solids_preserved=200,
                  inherited_junction_check=dict(samples=validation_v5['plaza_interface_samples'],
                      maximum_stone_face_step=validation_v5['maximum_stone_face_step'],
                      provenance='All 200 path solids and four audited adjacent meshes exactly match v5; no new geometric junction change'),
                  editable_lettering=labels, evaluated_text_meshes_nonempty=True,
                  original_cameras_lights_and_other_objects_preserved=True,
                  required_feature_ids=features, metrics=stats,
                  old_corrected_text_exports_preserved=repairs,
                  web_and_final_visual_acceptance_pending=True)
write(OUTDIR / 'version-manifest.json', manifest)
write(OUTDIR / 'validation.json', validation)
print('UNIFIED_CLOSEOUT_BASELINE_VALIDATED', target_hash, stats, flush=True)
