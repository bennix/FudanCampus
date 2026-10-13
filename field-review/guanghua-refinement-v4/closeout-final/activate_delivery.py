"""Activate only a fully verified local delivery; never writes the v7 baseline."""
from pathlib import Path
import hashlib,json

O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
source=O/'guanghua-closeout-final.blend'
digest=hashlib.sha256(source.read_bytes()).hexdigest()
validation=read(O/'delivery-validation.json')
assert validation['internal_delivery_ready'] is True,validation['gates']
assert validation['source_sha256']==digest
assert all(validation['gates'].values())
assert validation['user_visual_acceptance'] is False
pointer=O.parent/'current-scene.json'
previous=read(pointer)
current={
 'version':'guanghua-closeout-final', 'date':'2026-10-01',
 'status':'Internal verification complete; user visual review pending; draw-call target tracked separately',
 'scene':str(source), 'scene_sha256':digest,
 'manifest':str(O/'version-manifest.json'), 'review':str(O/'review.html'),
 'review_type':'html','brief':str(O/'README.md'),
 'plan':previous['plan'],'validation':str(O/'delivery-validation.json'),
 'user_visual_acceptance':False,'web_assets_updated':True,
 'baseline_preserved':str(O.parent/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'),
 'instruction':'以本收官模型和同源审阅页作为当前入口；保留 v7 原件及既有其它校园资产。未知和推定见 uncertainty.md，用户视觉认可尚未登记。',
}
pointer.write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('CURRENT_SCENE_ACTIVATED',digest)
