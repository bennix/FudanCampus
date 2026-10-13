import sys, json
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build as B
bpy.ops.wm.open_mainfile(filepath=str(B.OUT))
ob=bpy.data.objects['LAWN | satellite-fixed concave north edge']
B.snap_cut_planes(ob)
check=B.C.solid_check(ob)
report=json.loads((B.O/'validation.json').read_text(encoding='utf-8'))
report['local_cleanup_checks']=[check if c['name']==ob.name else c for c in report['local_cleanup_checks']]
report['geometry_numeric_tolerance']=1e-5
after=B.snapshots()
assert all(after.get(n)==h for n,h in report['protected_fingerprints'].items())
bpy.ops.wm.save_as_mainfile(filepath=str(B.OUT))
(B.O/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('PRECISION_FINISH_OK',flush=True)
