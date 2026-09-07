import bpy
import addon_utils
addon_utils.enable('blender_mcp',default_set=False)
def start():
 try:
  bpy.ops.blendermcp.start_server()
  for screen in bpy.data.screens:
   for area in screen.areas:
    if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
 except Exception as e:print(e)
 return None
bpy.app.timers.register(start,first_interval=2)
