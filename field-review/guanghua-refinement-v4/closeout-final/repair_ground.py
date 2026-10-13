"""Replace only C04 solids after actual native/GLB opening probes found a cover."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read,make,solid
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import snapshot,sha,write,plain
T=O/'guanghua-closeout-final.blend';bpy.ops.wm.open_mainfile(filepath=str(T));bpy.context.preferences.filepaths.save_version=0
before=snapshot();pack=read(O/'road-pack.json');changed=[]
for role in ['road','ground']:
 name='C04 continuous '+role;old=bpy.data.objects[name];mat=old.data.materials[0];props={k:old[k] for k in old.keys()};bpy.data.objects.remove(old,do_unlink=True)
 row=pack[role];o=make(name,row['vertices'],row['faces'],mat,'EPATH','C04',role)
 for k,v in props.items():o[k]=v
 o['opening_protection']='Both east stair mouths subtracted from actual original coping footprints; interiors preserved'
 check=solid(o);assert not check['nonmanifold'] and not check['zero_area'] and check['volume']>0;changed.append(name)
after=snapshot();assert all(after.get(n)==h for n,h in before.items() if n not in changed)
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'final-snapshot.json',after);bpy.ops.wm.open_mainfile(filepath=str(T));assert snapshot()==after
write(O/'opening-ground-repair.json',dict(source_sha256=sha(T),changed=changed,reason='Production GLB ray found new ground covering the northeast EOPEN stair mouth',hardscape_guard='Original four stair mouths and all other meshes preserved'))
print('OPENING_GROUND_REPAIR_REOPENED',flush=True)
