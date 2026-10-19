"""Validate module membership, published files, hashes and local geometry bounds."""
import json, struct, hashlib
from pathlib import Path
from asset_protection import verify_protected_sources
root = Path(__file__).resolve().parents[1]
public = root / 'web/public'
m = json.loads((public / 'campus-manifest.json').read_text(encoding='utf-8'))
verify_protected_sources()
ids = {'3','5','7','14','16','17','20','27','42','51','55','56','65'}
assert {b['id'] for b in m['buildings']} == ids

def read(asset):
    asset_path = public / asset['url']
    data = asset_path.read_bytes()
    if asset_path.name.endswith('.parts.json'):
        descriptor = json.loads(data)
        parts = []
        for part in descriptor['parts']:
            chunk = (asset_path.parent / part['url']).read_bytes()
            assert len(chunk) == part['bytes'] and hashlib.sha256(chunk).hexdigest() == part['sha256']
            parts.append(chunk)
        data = b''.join(parts)
        assert hashlib.sha256(data).hexdigest() == descriptor['sha256']
    assert len(data) == asset['bytes']
    assert hashlib.sha256(data).hexdigest()[:12] == asset['revision']
    magic,version,size = struct.unpack_from('<III',data)
    assert magic == 0x46546c67 and version == 2 and size == len(data)
    length,kind = struct.unpack_from('<II',data,12)
    assert kind == 0x4e4f534a
    return json.loads(data[20:20+length])
for asset in m['shared']:
    gltf = read(asset)
    for node in gltf['nodes']:
        extras = node.get('extras',{})
        node_id = str(extras.get('building_id',extras.get('landmark_id','')))
        assert node_id not in ids or (asset['url'] == 'models/shared/03.glb' and node_id in {'3', '5'}) or (asset['url'] in {'models/shared/02.glb', 'models/shared/02-teaching4.glb'} and node_id == '7')  # Hidden legacy north blocks
blend_optional = {'3', '5', '7'}
for b in m['buildings']:
    assert b['id'] in blend_optional or (root / b.get('editableSource', f"assets/buildings/{b['id']}.blend")).exists()
    gltf = read(b); read(b['overview'])
    tagged = [n.get('extras',{}) for n in gltf['nodes'] if 'mesh' in n]
    assert tagged and all(str(n.get('building_id',n.get('landmark_id',''))) == b['id'] for n in tagged)
    assert b['rotation'] == [0,0,0]
    assert all(a <= c for a,c in zip(b['bounds']['min'],b['bounds']['max']))
print(f'PASS: {len(ids)} building modules, shared membership, GLB structure, hashes and protected sources')
print('Initial model bytes:',sum(a['bytes'] for a in m['shared'])+sum(a['overview']['bytes'] for a in m['buildings']))
