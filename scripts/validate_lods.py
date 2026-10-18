"""Verify LOD integrity, source freshness, transforms and initial payload budget."""
import json, hashlib, struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'web/public'
m=json.loads((root/'campus-manifest.json').read_text())
lod=json.loads((root/'campus-lod.json').read_text())
sources={category+'-'+a['id']:a for category in ['shared','buildings'] for a in m[category]}
assert {a.get('sourceId',a['id']) for a in lod['assets']}==set(sources)
for a in lod['assets']:
 s=sources[a.get('sourceId',a['id'])]
 assert a['sourceRevision']==s['revision'],f"Stale LOD {a['id']}; run scripts/build_lods.py"
 assert a['position']==s.get('position',[0,0,0])
 assert all(low<=high for low,high in zip(a['bounds']['min'],a['bounds']['max']))
 assert len(a['tiers'])==3
 for t in a['tiers']:
  b=(root/t['url']).read_bytes()
  assert len(b)==t['bytes'] and hashlib.sha256(b).hexdigest()[:12]==t['revision']
  magic,version,size=struct.unpack_from('<III',b);assert magic==0x46546c67 and version==2 and size==len(b)
  n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n])
  triangles=sum(sum(g['accessors'][p['indices']]['count']//3 for p in g['meshes'][node['mesh']]['primitives'])*g['accessors'][next(iter(node['extensions']['EXT_mesh_gpu_instancing']['attributes'].values()))]['count'] if 'EXT_mesh_gpu_instancing' in node.get('extensions',{}) else sum(g['accessors'][p['indices']]['count']//3 for p in g['meshes'][node['mesh']]['primitives']) for node in g['nodes'] if 'mesh' in node)
  assert triangles==t['triangles'] and triangles>0
  if a['id']=='shared-05':
   assert not any('Canopy' in n.get('name','') for n in g['nodes']), 'Old polygon canopy must be removed'
  if a['id'].startswith('campus-tree-'):
   assert all(m.get('alphaMode')=='MASK' for m in g['materials']), 'Leaf silhouettes require alpha cutouts'
  if a['id']=='shared-guanghua-landscape':
   assert not any(n.get('extras',{}).get('tree_group')=='V6 East spreading 01' for n in g['nodes']), 'Duplicate cherry in landscape'
   assert any(n.get('extras',{}).get('feature_id')=='LAWN' for n in g['nodes']), 'Lawn surface missing'
   assert any(n.get('extras',{}).get('campusVegetation') for n in g['nodes']), 'Vegetation missing'
 if a['id'].startswith('landscape-tree-'):
  assert a['tiers'][2]['triangles']>a['tiers'][0]['triangles'], 'Tree near detail must exceed far tier'
 if a['id']=='guanghua-cherry':
  assert a['tiers'][2]['triangles']==709192, 'Original cherry flower and branch detail must be retained'
 assert a['tiers'][0]['triangles']<=a['tiers'][1]['triangles']
 # Export triangulation can differ from canonical source; architectural surfaces must survive.
 if a['id'].startswith('buildings-'):
  assert a['tiers'][0]['triangles']>=a['tiers'][2]['triangles']*.85, f"Architectural detail destroyed: {a['id']}"
initial=sum(a['tiers'][0]['bytes'] for a in lod['assets'])
triangles=sum(a['tiers'][0]['triangles'] for a in lod['assets'])
assert initial<45_000_000 and triangles<2_500_000,(initial,triangles)
print(f"PASS: {len(lod['assets'])} assets, 3 LOD tiers, current source hashes, positions and GLB metadata")
print(f'Overview payload: {initial:,} bytes; {triangles:,} triangles')
