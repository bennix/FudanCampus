"""Repair the two standalone exports; preserve source files and existing meshes."""
import hashlib
import json
import struct
import sys
from pathlib import Path
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from export_visible_glb import export_visible_glb

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / 'field-review/guanghua-refinement-v4'
OUT = REVIEW / 'garage-text-export'
OUT.mkdir(exist_ok=True)
TARGETS = [('west-entry-v3', 'west-entry-aligned-v3', True),
           ('vegetation-v2', 'vegetation-v2', False)]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_glb(path):
    raw = path.read_bytes()
    assert struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw))
    length, kind = struct.unpack_from('<II', raw, 12)
    assert kind == 0x4E4F534A
    doc = json.loads(raw[20:20 + length])
    start = 20 + length
    blen, bkind = struct.unpack_from('<II', raw, start)
    assert bkind == 0x004E4942
    return doc, raw[start + 8:start + 8 + blen]


def mesh_content(doc, binary):
    result = {}
    for node in doc['nodes']:
        if 'mesh' not in node:
            continue
        mesh = doc['meshes'][node['mesh']]
        parts = []
        for primitive in mesh['primitives']:
            hashes = {}
            attrs = dict(primitive['attributes'])
            if 'indices' in primitive:
                attrs['indices'] = primitive['indices']
            for key, index in attrs.items():
                accessor = doc['accessors'][index]
                view = doc['bufferViews'][accessor['bufferView']]
                data = binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']]
                hashes[key] = [accessor['count'], accessor['type'], accessor['componentType'],
                               hashlib.sha256(data).hexdigest()]
            mat = doc['materials'][primitive['material']] if 'material' in primitive else None
            parts.append(dict(attributes=hashes, material=mat, mode=primitive.get('mode', 4)))
        transform = {k: node[k] for k in ('translation', 'rotation', 'scale', 'matrix') if k in node}
        result[node['name']] = dict(primitives=parts, transform=transform, extras=node.get('extras'))
    return result


for directory, stem, apply in TARGETS:
    source = REVIEW / directory / (stem + '.blend')
    target = source.with_suffix('.glb')
    source_hash = sha(source)
    before_hash, before_size = sha(target), target.stat().st_size
    before_doc, before_bin = read_glb(target)
    before_meshes = mesh_content(before_doc, before_bin)
    bpy.ops.wm.open_mainfile(filepath=str(source))
    fonts = [o for o in bpy.context.scene.objects if o.type == 'FONT' and not o.hide_render]
    assert {'WB1', 'WB2', 'SIGN'} <= {o.get('feature_id') for o in fonts}
    expected_bounds = {}
    from mathutils import Vector
    for obj in fonts:
        points = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
        expected_bounds[obj.name] = [[min(p[i] for p in points) for i in range(3)],
                                     [max(p[i] for p in points) for i in range(3)]]
    temporary = target.with_name(stem + '.text-repair.glb')
    texts = export_visible_glb(temporary, export_apply=apply)
    after_doc, after_bin = read_glb(temporary)
    after_meshes = mesh_content(after_doc, after_bin)
    assert before_meshes.keys() <= after_meshes.keys(), 'Existing mesh omitted'
    assert all(after_meshes[name] == content for name, content in before_meshes.items()), 'Existing mesh changed'
    assert set(after_meshes) - set(before_meshes) == {t['name'] for t in texts} - set(before_meshes)
    def image_content(doc, binary):
        result = {}
        for image in doc.get('images', []):
            view = doc['bufferViews'][image['bufferView']]
            start = view.get('byteOffset', 0)
            result[image.get('name')] = hashlib.sha256(binary[start:start + view['byteLength']]).hexdigest()
        return result
    assert image_content(before_doc, before_bin) == image_content(after_doc, after_bin), 'Embedded textures changed'
    assert all('bufferView' in im for im in after_doc.get('images', []))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(temporary))
    for text in texts:
        obj = bpy.data.objects.get(text['name'])
        assert obj and obj.type == 'MESH' and len(obj.data.polygons)
        assert obj.get('feature_id') == text['feature_id']
        points = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
        bounds = [[min(p[i] for p in points) for i in range(3)],
                  [max(p[i] for p in points) for i in range(3)]]
        assert max(abs(a - b) for row, expected in zip(bounds, expected_bounds[obj.name])
                   for a, b in zip(row, expected)) < .001, 'Lettering moved'
        text['reimport_bounds_blender'] = bounds
    assert sha(source) == source_hash
    temporary.replace(target)
    report = dict(source=str(source.relative_to(ROOT)), source_sha256=source_hash,
                  source_unchanged=True, target=str(target.relative_to(ROOT)),
                  before_sha256=before_hash, after_sha256=sha(target),
                  before_bytes=before_size, after_bytes=target.stat().st_size,
                  preserved_meshes=len(before_meshes), added_text_meshes=texts,
                  existing_mesh_geometry_materials_transforms_metadata_unchanged=True,
                  embedded_images=len(after_doc.get('images', [])), glb_reimport_ok=True)
    (OUT / (directory + '.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('TEXT_EXPORT_REPAIRED', directory, len(texts), flush=True)
