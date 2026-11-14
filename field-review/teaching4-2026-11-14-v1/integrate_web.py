"""Promote this reviewed candidate into the local campus; backup before any write."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
PUBLIC=ROOT/'web/public'
sys.path.insert(0,str(ROOT/'scripts'))
from asset_protection import verify_protected_sources
verify_protected_sources()
stats=json.loads((HERE/'statistics.json').read_text(encoding='utf-8'))
payload=(HERE/'17-candidate.glb').read_bytes()
assert hashlib.sha256(payload).hexdigest()==stats['glb_sha256']
manifest=json.loads((PUBLIC/'campus-manifest.json').read_text(encoding='utf-8'))
before_other={k:[a for a in manifest[k] if not (k=='buildings' and a['id']=='17')] for k in ['shared','buildings']}
paths=['assets/buildings/17.blend','scripts/teaching4_geometry.py','web/public/models/buildings/17.glb',
       'web/public/campus-manifest.json','web/public/campus-lod.json','web/public/buildings.json',
       'web/public/models/lod/buildings-17-far.glb','web/public/models/lod/buildings-17-medium.glb',
       'web/public/walk-collision.bin','web/public/walk-collision.json','web/public/walk-interiors.json',
       'field-review/campus-photo-integration/walk-roofs.json']
backup=HERE/'web-integration-backup'
for relative in paths:
    src=ROOT/relative
    dst=backup/relative
    if src.exists() and not dst.exists():
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(src,dst)
for src,dst in [('17-candidate.blend','assets/buildings/17.blend'),
                ('17-candidate.glb','web/public/models/buildings/17.glb'),
                ('source/teaching4_geometry.py','scripts/teaching4_geometry.py')]:
    shutil.copy2(HERE/src,ROOT/dst)
asset=next(a for a in manifest['buildings'] if a['id']=='17')
revision=stats['glb_sha256'][:12]
asset.update(bytes=len(payload),revision=revision,
    source='Six user reference files (five photographs and annotated map); photo-refined 2026-11-14; dimensions inferred')
asset['overview']={'url':asset['url'],'bytes':len(payload),'revision':revision}
asset['overviewMode']='full'
lo=stats['bounds_blender']['min'];hi=stats['bounds_blender']['max']
asset['bounds']={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]}
asset['labelPosition'][1]=max(22,hi[2]+.4)
after_other={k:[a for a in manifest[k] if not (k=='buildings' and a['id']=='17')] for k in ['shared','buildings']}
assert before_other==after_other
(PUBLIC/'campus-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
labels=json.loads((PUBLIC/'buildings.json').read_text(encoding='utf-8'))
for label in labels['buildings']:
    if label['id']=='17':
        label['position']=asset['labelPosition']
        label['source']='user photographs; photo-refined 2026-11-14; approximate dimensions'
(PUBLIC/'buildings.json').write_text(json.dumps(labels,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('INTEGRATED_17',revision,'; backup:',backup)
