"""Build one modular building in Blender and export GLB + manifest entry. Usage:
  blender -b --python scripts/bake_modular_building.py -- 5
"""
import json
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

S = 0.8
records = {r['id']: r for r in json.loads((ROOT / 'references/buildings.json').read_text(encoding='utf-8'))}


def xy(px, py):
    return ((px - 1200) * S, (1000 - py) * S)


def mat(name, color, rough=0.75):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    return m


def mesh(name, v, f, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


argv = sys.argv[sys.argv.index('--') + 1 :] if '--' in sys.argv else []
if len(argv) != 1:
    raise SystemExit('Expected: blender -b --python scripts/bake_modular_building.py -- <building_id>')
bid = argv[0]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

r = records[bid]
x, y = xy(r['x'], r['y'])
col = bpy.context.scene.collection

if bid == '3':
    from north_gym_geometry import build_north_gym

    build_north_gym(x, y, mat, mesh, col, bpy)
elif bid == '5':
    from north_canteen_geometry import build_north_canteen

    build_north_canteen(x, y, mat, mesh, col, bpy)
elif bid == '7':
    from north_warehouse_geometry import build_north_warehouse

    build_north_warehouse(x, y, mat, mesh, col, bpy)
else:
    raise SystemExit(f'No bake recipe for building {bid}')

blend_path = ROOT / f'assets/buildings/{bid}.blend'
blend_path.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

from export_modular import export_modular

export_modular(bid)
print('BAKE_COMPLETE', bid)
