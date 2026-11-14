"""Verify actual exported PNG color and unchanged geometry against round 1."""
from pathlib import Path
from PIL import Image
import io,json,struct,statistics
HERE=Path(__file__).resolve().parent
def read(path):
    data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+size]),data[28+size:]
g,bin=read(HERE/'55-candidate.glb')
old,oldbin=read(HERE/'web-integration-backup/web/public/models/buildings/55.glb')
for key in ['nodes','meshes','accessors']:
    assert g[key]==old[key], 'Geometry structure changed: '+key
for a in g['accessors']:
    index=a['bufferView'];v=g['bufferViews'][index];w=old['bufferViews'][index]
    # Embedded PNG size may relocate the later geometry buffer views.
    assert {k:v for k,v in v.items() if k!='byteOffset'}=={k:v for k,v in w.items() if k!='byteOffset'}
    start=v.get('byteOffset',0);oldstart=w.get('byteOffset',0);length=v['byteLength']
    assert bin[start:start+length]==oldbin[oldstart:oldstart+length], 'Geometry buffer changed'
m=next(m for m in g['materials'] if m['name']=='Chemistry deep red brick')
pbr=m['pbrMetallicRoughness']
assert pbr.get('baseColorFactor',[1,1,1,1])==[1,1,1,1], 'Texture multiplied by a dark factor'
i=g['textures'][pbr['baseColorTexture']['index']]['source']
v=g['bufferViews'][g['images'][i]['bufferView']];start=v.get('byteOffset',0)
im=Image.open(io.BytesIO(bin[start:start+v['byteLength']])).convert('RGB')
pixels=list(im.getdata());target=(212,107,87)
brick=[p for p in pixels if max(abs(a-b) for a,b in zip(p,target))<=3]
assert len(brick)/len(pixels)>.90, 'Most texture pixels do not match #D46B57'
median=tuple(round(statistics.median(p[i] for p in brick)) for i in range(3))
assert median==target, ('Brick median differs from requested sRGB',median)
print('PASS: exported brick median #D46B57; >90% brick pixels within 3/255; neutral baseColorFactor; all geometry buffers unchanged')
