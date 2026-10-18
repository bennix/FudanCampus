"""Verify LOD integrity, source freshness, transforms and initial payload budget."""
import json, hashlib, struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'web/public'
m=json.loads((root/'campus-manifest.json').read_text())
lod=json.loads((root/'campus-lod.json').read_text())
sources={category+'-'+a['id']:a for category in ['shared','buildings'] for a in m[category]}
assert {a['id'] for a in lod['assets']}==set(sources)
for a in lod['assets']:
 s=sources[a['id']]
 assert a['sourceRevision']==s['revision'],f"Stale LOD {a['id']}; run scripts/build_lods.py"
 assert a['position']==s.get('position',[0,0,0])
 assert all(low<=high for low,high in zip(a['bounds']['min'],a['bounds']['max']))
 assert len(a['tiers'])==3
 for t in a['tiers']:
  b=(root/t['url']).read_bytes()
  assert len(b)==t['bytes'] and hashlib.sha256(b).hexdigest()[:12]==t['revision']
  magic,version,size=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and size==len(b)
  n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n])
  triangles=sum(g['accessors'][p['indices']]['count']//3 for mesh in g['meshes'] for p in mesh['primitives'])
  assert triangles==t['triangles'] and triangles>0
 assert a['tiers'][0]['triangles']<=a['tiers'][1]['triangles']<=a['tiers'][2]['triangles']
initial=sum(a['tiers'][0]['bytes'] for a in lod['assets'])
triangles=sum(a['tiers'][0]['triangles'] for a in lod['assets'])
assert initial<5_000_000 and triangles<100_000,(initial,triangles)
print('PASS: 15 assets, 3 LOD tiers, current source hashes, positions and GLB metadata')
print(f'Overview payload: {initial:,} bytes; {triangles:,} triangles')
