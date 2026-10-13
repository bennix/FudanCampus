import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for name in ['stage04-curve-repair.blend','forecourt-refined-v4.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(O/name));before=all_digests()
 ob=bpy.data.objects['EPATH continuous union surface'];ob.data.materials.clear();ob.data.materials.append(clean_path_material());uv(ob,4)
 ob['finish_repair']='Inherited pink-path texture had visible repeated black wedges; replaced with even-seed constant-width stone joints'
 assert all_digests()==before
 bpy.ops.wm.save_as_mainfile(filepath=str(O/name))
 if name.startswith('stage04'):
  for k,n in [('top','V4 straight path overhead'),('4496','V4 approximate photo4496'),('junction','V4 flat path crossing diagnostic')]:render('stage04-after-'+k+'.png',bpy.data.objects[n],k!='4496',width=1400,samples=24)
 else:render('stage05-after-overall.png',bpy.data.objects['FINAL overall'],width=1600,samples=32)
report=json.loads((O/'stage04-validation.json').read_text(encoding='utf-8'));report['inherited_texture_black_wedges_confirmed']=True;report['independent_path_texture_replaced']=True;report['finish_change_geometry_unchanged']=True
save_report('stage04',report)
print('PATH_FINISH_REPAIRED',flush=True)
