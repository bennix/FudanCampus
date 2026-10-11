import bpy,json,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import sha,write
M=json.loads((O/'version-manifest.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=M['scene']);o=bpy.data.objects['V6 south photo4597'];o.location=(59,14.5,1.75);o.rotation_euler=(Vector((-20,14.5,3.4))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=M['scene'],compress=True)
M['scene_sha256']=sha(M['scene']);M['scene_bytes']=Path(M['scene']).stat().st_size;write(O/'version-manifest.json',M)
print('SOUTH_CAMERA_UPDATED',M['scene_sha256'],flush=True)
