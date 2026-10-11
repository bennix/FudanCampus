import bpy
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'stage01-east.blend'))
s=bpy.context.scene
d=bpy.data.cameras.new('Comparison only');c=bpy.data.objects.new('Comparison only',d);s.collection.objects.link(c)
dx=-6.697882438088101
c.location=(88.2+dx,47.8,3.82);c.rotation_euler=(Vector((77+dx,44.5,2.2))-c.location).to_track_quat('-Z','Y').to_euler();d.lens=24;d.clip_end=1000
s.camera=c;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1100;s.render.resolution_y=825;s.render.resolution_percentage=100
s.render.filepath=str(O/'view-03/before-exit.png');bpy.ops.render.render(write_still=True)
