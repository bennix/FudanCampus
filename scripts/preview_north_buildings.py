"""Open Blender, build north buildings 3/5/7 from specs, save a preview .blend.

Interactive (opens Blender UI):
  "D:\\blender\\blender.exe" --python scripts/preview_north_buildings.py

Headless save only:
  "D:\\blender\\blender.exe" -b --python scripts/preview_north_buildings.py
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
    p.inputs['Emission Color'].default_value = (*color, 1)
    p.inputs['Emission Strength'].default_value = 0.15
    p.inputs['Roughness'].default_value = rough
    return m


def mesh(name, v, f, m):
    me = bpy.data.meshes.new(name)
    me.from_pydata(v, [], f)
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


from north_buildings_common import build_north_detail

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

for bid in ('3', '5', '7'):
    r = records[bid]
    x, y = xy(r['x'], r['y'])
    build_north_detail(bid, x, y, mat, mesh, bpy.context.scene.collection, bpy)

out = ROOT / 'output' / 'preview_north_3_5_7.blend'
out.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(out))
print('Saved', out)

if not bpy.app.background:
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.shading.type = 'MATERIAL'
                space.shading.color_type = 'MATERIAL'
                space.clip_end = 5000
                break
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.view3d.view_all(center=True)
    print('Viewport: Material Preview. 3=blue, 5=orange, 7=green')
