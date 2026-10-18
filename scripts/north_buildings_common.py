"""Procedural meshes for north-campus buildings 3, 5 and 7 (shared JSON spec)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = json.loads((ROOT / 'scripts/north_buildings_specs.json').read_text(encoding='utf-8'))


def build_north_detail(building_id, x, y, mat, mesh, current, bpy):
    spec = SPECS[str(building_id)]
    materials = {}
    for key, color in spec['materials'].items():
        rough = 0.35 if key in ('glass',) else 0.72
        materials[key] = mat(f"North {building_id} {key}", tuple(color), rough)

    buffers = {}

    def b(dx, dy, z, w, d, h, mkey):
        m = materials[mkey]
        vs, fs = buffers.setdefault(m.name, ([], []))
        n = len(vs)
        vs.extend(
            [
                (x + dx + a * w / 2, y + dy + c * d / 2, z + e * h / 2)
                for a, c, e in [
                    (-1, -1, -1),
                    (-1, -1, 1),
                    (-1, 1, -1),
                    (-1, 1, 1),
                    (1, -1, -1),
                    (1, -1, 1),
                    (1, 1, -1),
                    (1, 1, 1),
                ]
            ]
        )
        fs.extend(
            [
                tuple(n + i for i in f)
                for f in [(0, 4, 6, 2), (1, 3, 7, 5), (0, 1, 5, 4), (2, 6, 7, 3), (0, 2, 3, 1), (4, 5, 7, 6)]
            ]
        )

    for box in spec['boxes']:
        b(box['dx'], box['dy'], box['z'], box['width'], box['depth'], box['height'], box['m'])

    label = spec['name']
    for name, (vs, fs) in buffers.items():
        ob = mesh(f'{label} · {name}', vs, fs, bpy.data.materials[name])
        ob['building_id'] = str(building_id)
        ob['building_name'] = label
        ob['source'] = spec['source']
