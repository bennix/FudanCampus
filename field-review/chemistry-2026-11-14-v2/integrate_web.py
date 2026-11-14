"""Integrate only building 55, using the previously saved production backup."""
from pathlib import Path
import json,hashlib,shutil,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];PUB=ROOT/'web/public'
sys.path.insert(0,str(ROOT/'scripts'))
from asset_protection import verify_protected_sources
verify_protected_sources()
stats=json.loads((HERE/'statistics.json').read_text(encoding='utf8'))
manifest=json.loads((PUB/'campus-manifest.json').read_text(encoding='utf8'))
backup=json.loads((HERE/'web-integration-backup/web/public/campus-manifest.json').read_text(encoding='utf8'))
for key in ['shared','buildings']:
    assert [a for a in manifest[key] if not(key=='buildings' and a['id']=='55')]==[a for a in backup[key] if not(key=='buildings' and a['id']=='55')], 'Unexpected concurrent non-target manifest edit'
current55=next(a for a in manifest['buildings'] if a['id']=='55')
original55=next(a for a in backup['buildings'] if a['id']=='55')
for key in ['position','rotation','orientationBaked','url','labelPosition']:assert current55[key]==original55[key]
payload=(HERE/'55-candidate.glb').read_bytes()
assert hashlib.sha256(payload).hexdigest()==stats['glb_sha256']
for src,dst in [('55-candidate.glb','web/public/models/buildings/55.glb'),
                ('55-candidate.blend','assets/buildings/55.blend')]:shutil.copy2(HERE/src,ROOT/dst)
# Keep the legacy overview URL current too, although the manifest uses full mode.
shutil.copy2(HERE/'55-candidate.glb',PUB/'models/overview/55.glb')
source=HERE/'source';source.mkdir(exist_ok=True)
shutil.copy2(ROOT/'scripts/chemistry_geometry.py',source/'chemistry_geometry.py')
a=next(a for a in manifest['buildings'] if a['id']=='55')
a.update(bytes=len(payload),revision=stats['glb_sha256'][:12],
         source='Photo refinement 2026-11-14: H footprint, west recess, raised centre, white roof, complete facades, three tiled porticos; user brick color #D46B57; dimensions inferred')
a['overview']={k:a[k] for k in ['url','bytes','revision']};a['overviewMode']='full'
lo=stats['bounds_blender']['min'];hi=stats['bounds_blender']['max']
a['bounds']={'min':[lo[0],lo[2],-hi[1]],'max':[hi[0],hi[2],-lo[1]]}
assert [b for b in manifest['buildings'] if b['id']!='55']==[b for b in backup['buildings'] if b['id']!='55']
(PUB/'campus-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('INTEGRATED_55',a['revision'],'position/rotation/label unchanged; old source and runtime assets backed up')
