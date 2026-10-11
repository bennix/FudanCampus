"""Fixed review cameras for complete checkpoint; no geometry edits."""
import bpy,sys,json,math
from mathutils import Vector
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'field-review/guanghua-complete-v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'guanghua-complete-v3.blend'));s=bpy.context.scene
diagnostic='--diagnostic' in sys.argv
extras='--extra' in sys.argv
repair='--repair-cameras' in sys.argv
for name,loc,target in [('west south stair',(-23,39,8),(-32,48,-.1)),('east north stair',(81,69,8),(72.3,78,-.1))]:
 if 'FINAL '+name not in bpy.data.objects:
  d=bpy.data.cameras.new('FINAL '+name);o=bpy.data.objects.new('FINAL '+name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=15
for o in s.objects:
 if o.type=='CAMERA' and o.name.startswith('FINAL ') and o.data.type=='ORTHO' and not o.get('safe_ortho_standoff'):
  o.location+=o.rotation_euler.to_quaternion()@Vector((0,0,100));o['safe_ortho_standoff']=True
if extras or repair:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'guanghua-complete-v3.blend'))
names=['stairs-west-south','stairs-east-north'] if extras else ['overall','plan'] if diagnostic else ['overall','landscape','plan','south-garage','north-garage','stairs-west','stairs-east','pergola','ding','fudan','flower','stairs-west-south','stairs-east-north']
if repair:names=['stairs-east','fudan','pergola','flower']
s.render.threads_mode='FIXED';s.render.threads=12;s.cycles.use_denoising=True
for name in names:
 for o in bpy.data.objects:
  if o.get('feature_id')=='CONTEXT_GUANGHUA':o.hide_render=name not in ['overall']
  if o.get('feature_id')=='VEGETATION' and 'tree-canopies' in o.name:o.hide_render=name=='plan'
 s.camera=bpy.data.objects['FINAL '+{'stairs-west':'west stair','stairs-east':'east stair','stairs-west-south':'west south stair','stairs-east-north':'east north stair','south-garage':'south garage','north-garage':'north garage'}.get(name,name)]
 s.cycles.samples=16 if diagnostic else 64
 width=900 if diagnostic else 2400 if name in ['overall','landscape','plan'] else 1500
 s.render.resolution_x=width;s.render.resolution_y=round(width*(.70 if name in ['overall','landscape'] else .78));s.render.resolution_percentage=100
 s.render.filepath=str(OUT/(('diagnostic-' if diagnostic else 'after-')+name+'.png'));bpy.ops.render.render(write_still=True)
print('RENDER_BATCH_COMPLETE',flush=True)
