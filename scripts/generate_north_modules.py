#!/usr/bin/env python3
"""Generate GLB modules for buildings 3, 5, 7 (same data as generate_north_modules.ps1)."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'web' / 'public'


def campus_xy(record):
    x = (record['x'] - 1200) * 0.8
    y = (1000 - record['y']) * 0.8
    return x, y


def box_corners(dx, dy, z, width, depth, height):
    hw, hd, hh = width / 2, depth / 2, height / 2
    return [
        (dx - hw, dy - hd, z - hh),
        (dx + hw, dy - hd, z - hh),
        (dx - hw, dy + hd, z - hh),
        (dx + hw, dy + hd, z - hh),
        (dx - hw, dy - hd, z + hh),
        (dx + hw, dy - hd, z + hh),
        (dx - hw, dy + hd, z + hh),
        (dx + hw, dy + hd, z + hh),
    ]


def add_box(buffers, mat, dx, dy, z, width, depth, height):
    vs, fs = buffers.setdefault(mat, ([], []))
    n = len(vs)
    vs.extend(box_corners(dx, dy, z, width, depth, height))
    fs.extend([tuple(n + i for i in f) for f in [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]])


def three_local(v):
    return (v[0], v[2], -v[1])


def bounds_from_verts(vertices):
    pts = [three_local(v) for v in vertices]
    mins = [min(p[i] for p in pts) for i in range(3)]
    maxs = [max(p[i] for p in pts) for i in range(3)]
    return {'min': mins, 'max': maxs}


def write_glb(path, bid, bname, mat_keys, mat_colors, buffers):
    nodes, meshes_out, accessors, buffer_views = [], [], [], []
    bin_blob = bytearray()
    mesh_index = 0
    acc_index = 0
    for mat_name, (vertices, indices) in buffers.items():
        if not indices:
            continue
        mat_idx = mat_keys.index(mat_name)
        pos = bytearray()
        for v in vertices:
            tx, ty, tz = three_local(v)
            pos.extend(struct.pack('<fff', tx, ty, tz))
        idx = bytearray()
        for i in indices:
            idx.extend(struct.pack('<H', i))
        pos_off = len(bin_blob)
        bin_blob.extend(pos)
        while len(bin_blob) % 4:
            bin_blob.append(0)
        idx_off = len(bin_blob)
        bin_blob.extend(idx)
        while len(bin_blob) % 4:
            bin_blob.append(0)
        pos_view = len(buffer_views)
        buffer_views.append({'buffer': 0, 'byteOffset': pos_off, 'byteLength': len(pos)})
        idx_view = len(buffer_views)
        buffer_views.append({'buffer': 0, 'byteOffset': idx_off, 'byteLength': len(idx), 'target': 34963})
        pos_pts = [three_local(v) for v in vertices]
        pos_acc = acc_index
        acc_index += 1
        accessors.append(
            {
                'bufferView': pos_view,
                'componentType': 5126,
                'count': len(vertices),
                'type': 'VEC3',
                'min': [min(p[i] for p in pos_pts) for i in range(3)],
                'max': [max(p[i] for p in pos_pts) for i in range(3)],
            }
        )
        idx_acc = acc_index
        acc_index += 1
        accessors.append({'bufferView': idx_view, 'componentType': 5123, 'count': len(indices), 'type': 'SCALAR'})
        meshes_out.append({'primitives': [{'attributes': {'POSITION': pos_acc}, 'indices': idx_acc, 'material': mat_idx}]})
        nodes.append({'name': f'{bname} · {mat_name}', 'mesh': mesh_index, 'extras': {'building_id': bid, 'building_name': bname}})
        mesh_index += 1
    gltf = {
        'asset': {'version': '2.0', 'generator': 'generate_north_modules.py'},
        'scene': 0,
        'scenes': [{'nodes': list(range(len(nodes)))}],
        'nodes': nodes,
        'meshes': meshes_out,
        'materials': [
            {
                'name': f'North {bid} {k}',
                'pbrMetallicRoughness': {
                    'baseColorFactor': [*mat_colors[k], 1.0],
                    'metallicFactor': 0.05,
                    'roughnessFactor': 0.35 if k == 'glass' else 0.72,
                },
            }
            for k in mat_keys
        ],
        'accessors': accessors,
        'bufferViews': buffer_views,
        'buffers': [{'byteLength': len(bin_blob)}],
    }
    json_bytes = json.dumps(gltf, separators=(',', ':')).encode('utf-8')
    while len(json_bytes) % 4:
        json_bytes += b' '
    total = 12 + 8 + len(json_bytes) + 8 + len(bin_blob)
    out = bytearray()
    out.extend(struct.pack('<III', 0x46546C67, 2, total))
    out.extend(struct.pack('<II', len(json_bytes), 0x4E4F534A))
    out.extend(json_bytes)
    out.extend(struct.pack('<II', len(bin_blob), 0x004E4942))
    out.extend(bin_blob)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(out)
    return bytes(out)


specs = json.loads((ROOT / 'scripts/north_buildings_specs.json').read_text(encoding='utf-8'))
records = {r['id']: r for r in json.loads((ROOT / 'references/buildings.json').read_text(encoding='utf-8'))}
labels = {r['id']: r for r in json.loads((PUBLIC / 'buildings.json').read_text(encoding='utf-8'))['buildings']}
manifest = json.loads((PUBLIC / 'campus-manifest.json').read_text(encoding='utf-8'))

for bid in ('3', '5', '7'):
    spec = specs[bid]
    cx, cy = campus_xy(records[bid])
    label = labels[bid]
    mat_keys = list(spec['materials'].keys())
    for kind, box_key in (('detail', 'boxes'), ('overview', 'overview_boxes')):
        buffers = {}
        for box in spec[box_key]:
            add_box(buffers, box['m'], box['dx'], box['dy'], box['z'], box['width'], box['depth'], box['height'])
        rel = f'models/buildings/{bid}.glb' if kind == 'detail' else f'models/overview/{bid}.glb'
        data = write_glb(PUBLIC / rel, bid, spec['name'], mat_keys, spec['materials'], buffers)
        rev = hashlib.sha256(data).hexdigest()[:12]
        if kind == 'detail':
            all_v = [v for vs, _ in buffers.values() for v in vs]
            entry = {
                'id': bid,
                'name': spec['name'],
                'url': rel,
                'revision': rev,
                'bytes': len(data),
                'position': [cx, 0, -cy],
                'rotation': [0, 0, 0],
                'orientationBaked': True,
                'bounds': bounds_from_verts(all_v),
                'labelPosition': label['position'],
                'loadDistance': 240,
            }
        else:
            entry['overview'] = {'url': rel, 'revision': rev, 'bytes': len(data)}
    manifest['buildings'] = [b for b in manifest['buildings'] if b['id'] != bid] + [entry]

manifest['buildings'].sort(key=lambda b: int(b['id']))
(PUBLIC / 'campus-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Generated north modules 3, 5, 7')
