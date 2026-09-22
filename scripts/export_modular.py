"""Export eight editable building scenes and shared district GLBs from the master scene."""
import bpy
import json
import hashlib
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'web/public'
IDS = ['14', '16', '20', '27', '51', '55', '56', '65']

def export_modular(only_bid=None):
    records = {r['id']: r for r in json.loads((ROOT / 'references/buildings.json').read_text())}
    labels = {r['id']: r for r in json.loads((PUBLIC / 'buildings.json').read_text())['buildings']}
    original = bpy.context.scene
    manifest = {'version': 1, 'coordinates': 'Three.js Y-up; south +Z', 'shared': [], 'buildings': []}
    meshes = [o for o in original.objects if o.type == 'MESH']
    def identity(o):
        return str(o.get('building_id', o.get('landmark_id', '')))
    def save(objects, relative, origin=(0,0,0), blend=None):
        scene = bpy.data.scenes.new('Asset export')
        bpy.context.window.scene = scene
        copies = []
        for obj in objects:
            copy = obj.copy(); copy.data = obj.data.copy()
            scene.collection.objects.link(copy)
            copy.matrix_world = obj.matrix_world.copy()
            copy.location -= Vector(origin)
            copies.append(copy)
        bpy.context.window.scene = scene
        bpy.context.view_layer.update()
        path = PUBLIC / relative; path.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_active_scene=True,
                                  export_cameras=False, export_lights=False, export_extras=True)
        if blend:
            blend.parent.mkdir(parents=True, exist_ok=True)
            bpy.data.libraries.write(str(blend), {scene}, path_remap='RELATIVE', fake_user=True)
        bpy.context.window.scene = original
        for obj in copies:
            data = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.meshes.remove(data)
        bpy.data.scenes.remove(scene)
        return {'url': relative, 'revision': hashlib.sha256(path.read_bytes()).hexdigest()[:12], 'bytes': path.stat().st_size}
    if only_bid:
        manifest = json.loads((PUBLIC / 'campus-manifest.json').read_text())
    for bid in ([only_bid] if only_bid else IDS):
        objects = [o for o in meshes if identity(o) == bid]
        if not objects: raise RuntimeError('Missing building ' + bid)
        r = records.get(bid, {'x':1150,'y':992})
        x,y = (r['x']-1200)*.8, (1000-r['y'])*.8
        asset = save(objects, f'models/buildings/{bid}.glb', (x,y,0), None if only_bid else ROOT / f'assets/buildings/{bid}.blend')
        corners = [o.matrix_world @ Vector(c) for o in objects for c in o.bound_box]
        low = [min(v[i] for v in corners) for i in range(3)]
        high = [max(v[i] for v in corners) for i in range(3)]
        # Simplified overview per material group, retaining the building silhouette.
        proxies = []
        for obj in objects:
            # Material groups already contain entire wings; use a decimated copy for faithful silhouettes.
            copy = obj.copy(); copy.data = obj.data.copy(); original.collection.objects.link(copy)
            modifier = copy.modifiers.new('Overview simplification', 'DECIMATE'); modifier.ratio = .025
            bpy.context.view_layer.objects.active = copy
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            proxies.append(copy)
        overview = save(proxies, f'models/overview/{bid}.glb', (x,y,0))
        for obj in proxies:
            data = obj.data; bpy.data.objects.remove(obj, do_unlink=True); bpy.data.meshes.remove(data)
        manifest['buildings'] = [entry for entry in manifest['buildings'] if entry['id'] != bid]
        manifest['buildings'].append({'id':bid, 'name':labels[bid]['name'], **asset,
            'overview':overview, 'position':[x,0,-y], 'rotation':[0,0,0],
            'orientationBaked': True, 'bounds':{'min':[low[0]-x,low[2],y-high[1]],'max':[high[0]-x,high[2],y-low[1]]},
            'labelPosition':labels[bid]['position'], 'loadDistance':240})
    for collection in ([] if only_bid else original.collection.children):
        objects = [o for o in collection.all_objects if o.type == 'MESH' and identity(o) not in IDS]
        if objects:
            key = collection.name[:2]
            manifest['shared'].append({'id':key,'name':collection.name, **save(objects,f'models/shared/{key}.glb')})
    manifest['buildings'].sort(key=lambda entry: int(entry['id']))
    (PUBLIC / 'campus-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('MODULAR_EXPORT_COMPLETE',len(manifest['buildings']),len(manifest['shared']))

if __name__ == '__main__':
    import sys
    args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if args:
        if len(args) != 2 or args[0] != '--building' or args[1] not in IDS:
            raise ValueError('Expected -- --building ID (14,16,20,27,51,55,56,65)')
        bid = args[1]
        manifest = json.loads((PUBLIC / 'campus-manifest.json').read_text())
        entry = next(item for item in manifest['buildings'] if item['id'] == bid)
        x,z,minus_y = entry['position']
        for obj in bpy.context.scene.objects:
            if obj.type == 'MESH':
                obj.location += Vector((x,-minus_y,z))
                obj['building_id'] = bid
        bpy.context.view_layer.update()
        export_modular(bid)
    else:
        export_modular()

