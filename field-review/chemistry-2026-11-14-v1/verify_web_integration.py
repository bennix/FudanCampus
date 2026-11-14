"""Verify the runtime assets are current and all other modules stayed unchanged."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PUB=ROOT/'web/public'
def read(p):return json.loads(p.read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
m=read(PUB/'campus-manifest.json');old=read(HERE/'web-integration-backup/web/public/campus-manifest.json')
for key in ['shared','buildings']:
    assert [a for a in m[key] if not(key=='buildings' and a['id']=='55')]==[a for a in old[key] if not(key=='buildings' and a['id']=='55')]
    for a in m[key]:
        if key=='buildings' and a['id']=='55':continue
        if not a['url'].endswith('.parts.json'):assert sha(PUB/a['url'])[:12]==a['revision']
a=next(a for a in m['buildings'] if a['id']=='55');b=next(a for a in old['buildings'] if a['id']=='55')
for key in ['position','rotation','orientationBaked','url','labelPosition']:assert a[key]==b[key]
stats=read(HERE/'statistics.json');assert sha(PUB/a['url'])==stats['glb_sha256']
assert sha(ROOT/'assets/buildings/55.blend')==sha(HERE/'55-candidate.blend')
lod=read(PUB/'campus-lod.json');before=read(HERE/'web-integration-backup/web/public/campus-lod.json')
assert sorted([a for a in lod['assets'] if a['id']!='buildings-55'],key=lambda a:a['id'])==sorted([a for a in before['assets'] if a['id']!='buildings-55'],key=lambda a:a['id'])
for asset in lod['assets']:
    for t in asset['tiers']:
        assert sha(PUB/t['url'])[:12]==t['revision'];assert (PUB/t['url']).stat().st_size==t['bytes']
runtime=next(a for a in lod['assets'] if a['id']=='buildings-55')
assert runtime['sourceRevision']==a['revision'];assert runtime['tiers'][2]['revision']==a['revision']
print('PASS: 55 source, manifest, 3 LOD tiers and hashes agree; all other manifest entries and LOD assets unchanged')

import struct
from collections import Counter
def outside_triangles(path):
    result=Counter()
    for t in struct.iter_unpack('<9f',path.read_bytes()):
        # Includes both original oversized east portico and new deeper wings.
        inside=all(-131.5<=t[i]<=-58 and -.2<=t[i+1]<=15 and -181<=t[i+2]<=-140.5 for i in [0,3,6])
        if not inside:result[t]+=1
    return result
assert outside_triangles(PUB/'walk-collision.bin')==outside_triangles(HERE/'web-integration-backup/web/public/walk-collision.bin'), 'Collision outside chemistry area changed'
print('PASS: collision changes confined to chemistry footprint and porticos')
