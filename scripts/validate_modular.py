"""Validate module membership, published files, hashes and local geometry bounds."""
import json, struct, hashlib
from pathlib import Path
root = Path(__file__).resolve().parents[1]
public = root / 'web/public'
m = json.loads((public / 'campus-manifest.json').read_text())
ids = {'14','16','20','27','51','55','56','65'}
assert {b['id'] for b in m['buildings']} == ids

def read(asset):
    data = (public / asset['url']).read_bytes()
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
        assert str(extras.get('building_id',extras.get('landmark_id',''))) not in ids
for b in m['buildings']:
    assert (root / f"assets/buildings/{b['id']}.blend").exists()
    gltf = read(b); read(b['overview'])
    tagged = [n.get('extras',{}) for n in gltf['nodes'] if 'mesh' in n]
    assert tagged and all(str(n.get('building_id',n.get('landmark_id',''))) == b['id'] for n in tagged)
    assert b['rotation'] == [0,0,0]
    assert all(a <= c for a,c in zip(b['bounds']['min'],b['bounds']['max']))
print('PASS: 8 building modules, shared membership, GLB structure, hashes and sources')
print('Initial model bytes:',sum(a['bytes'] for a in m['shared'])+sum(a['overview']['bytes'] for a in m['buildings']))
