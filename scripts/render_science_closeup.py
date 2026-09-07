import bpy
from mathutils import Vector
cam=bpy.data.objects['05 Yifu science photo detail']
cam.location=(-190,153.4,8)
cam.rotation_euler=(Vector((-208,198.4,14))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.lens=26
bpy.ops.wm.save_as_mainfile(filepath='/Users/zhipingxu/FudanCampus/output/FudanCampus.blend')
s=bpy.context.scene;s.camera=cam;s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.filepath='/Users/zhipingxu/FudanCampus/output/yifu_science_detail.png'
bpy.ops.render.render(write_still=True)
