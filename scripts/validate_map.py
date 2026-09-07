"""Ensure every semantic building exported by Blender has exactly one web label."""
import json, struct, math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
source=json.loads((root/'references/buildings.json').read_text())
data=json.loads((root/'web/public/buildings.json').read_text())
labels=[b for b in data['buildings'] if b['category']=='building']
with (root/'web/public/campus.glb').open('rb') as f:
 magic,version,size=struct.unpack('<4sII',f.read(12));length,kind=struct.unpack('<II',f.read(8));gltf=json.loads(f.read(length))
assert magic==b'glTF' and version==2
assert size==(root/'web/public/campus.glb').stat().st_size
ids=[b['id'] for b in labels]
assert len(ids)==len(set(ids)), 'Duplicate building labels'
assert set(ids)=={b['id'] for b in source}, 'Source/label coverage mismatch'
exported={n.get('extras',{}).get('building_id') for n in gltf['nodes']}-{None}
assert exported==set(ids), f'Export/label mismatch: {exported^set(ids)}'
for b in labels:
 r=next(r for r in source if r['id']==b['id'])
 assert b['name']==r['name']
 assert all(math.isfinite(v) for v in b['position'])
 assert abs(b['position'][0]-(r['x']-1200)*.8)<1e-6
 assert abs(b['position'][2]+(1000-r['y'])*.8)<1e-6
 assert b['position'][1]>r.get('height',r['floors']*3.25)
print(f'PASS: {len(ids)} unique buildings, 100% GLB-to-label coverage, valid map coordinate conversion.')
print(f'Landmarks: {len(data["buildings"])-len(ids)}; meshes: {len(gltf["meshes"])}')
