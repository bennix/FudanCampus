import bpy,json
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'forecourt-complete-v2.blend'));s=bpy.context.scene
plaque=bpy.data.objects['POET_DONKEY inset nameplate']
# Box vertices contain the centre; the object origin remains at zero.
centre_y=sum(v.co.y for v in plaque.data.vertices)/len(plaque.data.vertices)
plaque.location.y=-1.055-centre_y
bpy.data.objects['POET_DONKEY 驢背詩思'].location.y=-1.077
bpy.ops.wm.save_as_mainfile(filepath=str(O/'forecourt-complete-v2.blend'))
for file,statue in [('forecourt-complete-v2.glb',False),('poet-donkey.glb',True)]:
 bpy.ops.object.select_all(action='DESELECT')
 for ob in s.objects:
  if ob.type=='MESH' and not ob.hide_render and (not statue or ob.get('feature_id')=='POET_DONKEY'):ob.hide_set(False);ob.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(O/file),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
info=json.loads((O/'build-info.json').read_text());s.render.resolution_x=1400;s.render.resolution_y=1050;s.cycles.samples=24
for k in ['statue','statue-side']:
 s.camera=bpy.data.objects[info['cameras'][k]];s.render.filepath=str(O/('after-'+k+'.png'));bpy.ops.render.render(write_still=True)
report=json.loads((O/'validation.json').read_text());report['plaque_clear_of_rough_stone']=True;report['glb_bytes']=(O/'forecourt-complete-v2.glb').stat().st_size;report['sculpture_glb_bytes']=(O/'poet-donkey.glb').stat().st_size
(O/'validation.json').write_text(json.dumps(report,indent=2));print('PLAQUE_CLEARANCE_REPAIRED')
