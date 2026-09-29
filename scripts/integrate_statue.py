"""Patch landmark 58 in the existing master without rebuilding other buildings."""
import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
scene=bpy.context.scene
for obj in list(scene.objects):
    if obj.get('landmark_id')=='58' or obj.name.startswith(('Statue plinth','Statue abstract body','Statue head')):
        bpy.data.objects.remove(obj,do_unlink=True)
with bpy.data.libraries.load(str(ROOT/'assets/landmarks/58.blend'),link=False) as (source,target):
    target.objects=list(source.objects)
collection=bpy.data.collections.new('58 Photo reference statue');scene.collection.children.link(collection)
for obj in target.objects:
    if obj and obj.type=='MESH':
        collection.objects.link(obj);obj.location.x-=40;obj.location.y+=66.4
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/FudanCampus.blend'))
print('INTEGRATED_STATUE',sum(o.get('landmark_id')=='58' for o in scene.objects))
