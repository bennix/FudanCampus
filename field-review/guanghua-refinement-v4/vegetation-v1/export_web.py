"""Standalone GLB export with supported base colours; native source untouched."""
import bpy
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'vegetation-v1.blend'))
fixed=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 p=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
 if not p or not p.inputs['Base Color'].is_linked or any(n.type=='TEX_IMAGE' for n in m.node_tree.nodes):continue
 for link in list(p.inputs['Base Color'].links):m.node_tree.links.remove(link)
 p.inputs['Base Color'].default_value=m.diffuse_color;fixed.append(m.name)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
 if o.type=='MESH' and not o.hide_render:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'vegetation-v1.glb'),export_format='GLB',use_selection=True,export_extras=True)
print('WEB_COLOR_FIXED',len(fixed))
