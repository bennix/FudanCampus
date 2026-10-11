import bpy,json,hashlib
from pathlib import Path
O=Path(__file__).resolve().parent;info=json.loads((O/'build-info.json').read_text());base=O.parent/'forecourt-v1/forecourt-entry-v1.blend'
def west():
 result={}
 for ob in bpy.context.scene.objects:
  if ob.type!='MESH' or ob.get('feature_id')!='FURNITURE':continue
  pts=[]
  for v in ob.data.vertices:
   p=ob.matrix_world@v.co
   if -32<p.x<-21 and 87.7<p.y<90.3:pts.append(tuple(round(c,6) for c in p))
  if pts:result[ob.name]=sorted(pts)
 return result
bpy.ops.wm.open_mainfile(filepath=str(base));old=west()
bpy.ops.wm.open_mainfile(filepath=str(O/'forecourt-complete-v2.blend'));assert old==west()
plaque=bpy.data.objects['POET_DONKEY inset nameplate']
assert abs(plaque.location.y+sum(v.co.y for v in plaque.data.vertices)/len(plaque.data.vertices)+1.055)<1e-5
assert hashlib.sha256(base.read_bytes()).hexdigest()==info['baseline_sha256']
v=json.loads((O/'validation.json').read_text());v['west_urn_world_vertices_unchanged']=True;v['final_checkpoint_after_plaque_reopened']=True
(O/'validation.json').write_text(json.dumps(v,indent=2));print('FINAL_REOPEN_AND_WEST_URNS_OK')
