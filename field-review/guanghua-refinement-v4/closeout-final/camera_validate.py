"""Actual Blender projection of the one reliable four-anchor relative fit."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import camera,read
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,write
T=O/'guanghua-closeout-final.blend';bpy.ops.wm.open_mainfile(filepath=str(T));s=bpy.context.scene;s.render.resolution_x=1800;s.render.resolution_y=1350;s.render.resolution_percentage=100
rows=[]
for name,row in read(O/'camera-overrides.json').items():
 c=camera(name,row['location'],row['target'],lens=row['lens']);c.rotation_euler.rotate_axis('Z',row['roll']);bpy.context.view_layer.update();anchors=[]
 for a in row.get('anchors',[]):
  q=world_to_camera_view(s,c,Vector(a['world']));model=[q.x,1-q.y];error=[abs(v-t) for v,t in zip(model,a['photo_normalized'])];anchors.append(dict(world=a['world'],photo_normalized=a['photo_normalized'],model_normalized=model,error=error))
 maximum=max((max(a['error']) for a in anchors),default=None)
 if maximum is not None:assert maximum<=.05,(name,maximum)
 rows.append(dict(camera=name,primary_photo=row['primary_photo'],source_sha256=sha(T),anchors=anchors,max_axis_error=maximum,confidence=row['confidence']))
write(O/'camera-validation.json',dict(source_sha256=sha(T),fits=rows,unmatched_policy='Other fixed photographs are approximate manual views; hardscape relationships reviewed individually. Canopy coverage is not certified from a mismatched photographic pose.',absolute_scale='inferred, not surveyed'))
print('ACTUAL_CAMERA_ANCHORS',rows[0]['max_axis_error'],flush=True)
