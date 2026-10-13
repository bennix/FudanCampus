import bpy,sys
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'guanghua-spring-branch-led-v2.blend'));s=bpy.context.scene
s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=True;s.cycles.device='CPU';s.render.threads_mode='FIXED';s.render.threads=8
s.render.resolution_x=1000;s.render.resolution_y=750;s.render.resolution_percentage=100;s.render.film_transparent=False
s.view_settings.view_transform='AgX';s.view_settings.exposure=.65;s.render.image_settings.file_format='PNG'
for key,cam in [('cherry-branch-led-v2','Spring cherry review'),('cherry-photo-angle-v2','Spring cherry photo angle')]:
 s.camera=bpy.data.objects[cam];s.render.filepath=str(O/(key+'.png'));bpy.ops.render.render(write_still=True);print('CHERRY_RENDER_DONE '+key,flush=True)
