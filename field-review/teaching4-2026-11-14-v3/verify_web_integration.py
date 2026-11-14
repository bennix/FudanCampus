"""Check the exact candidate is the model the runtime LOD manifest serves."""
from pathlib import Path
import hashlib
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PUB=ROOT/'web/public'
stats=json.loads((HERE/'statistics.json').read_text(encoding='utf-8'))
manifest=json.loads((PUB/'campus-manifest.json').read_text(encoding='utf-8'))
asset=next(a for a in manifest['buildings'] if a['id']=='17')
assert hashlib.sha256((PUB/asset['url']).read_bytes()).hexdigest()==stats['glb_sha256'], 'Web still serves old 17 GLB'
lod=json.loads((PUB/'campus-lod.json').read_text(encoding='utf-8'))
runtime=next(a for a in lod['assets'] if a['id']=='buildings-17')
assert runtime['sourceRevision']==stats['glb_sha256'][:12], 'Runtime LOD still uses old source'
assert runtime['tiers'][2]['revision']==asset['revision']
assert runtime['position']==asset['position']
for tier in runtime['tiers']:
    data=(PUB/tier['url']).read_bytes()
    assert hashlib.sha256(data).hexdigest()[:12]==tier['revision']
    assert len(data)==tier['bytes']
assert (ROOT/'assets/buildings/17.blend').read_bytes()==(HERE/'17-candidate.blend').read_bytes()
print('PASS: webpage canonical model, 3 LOD references and editable blend match teaching4 candidate',asset['revision'])
