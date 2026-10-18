import bpy,sys,math
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import snapshot,write,sha
T=O/'guanghua-closeout-final.blend';bpy.ops.wm.open_mainfile(filepath=str(T));bpy.context.preferences.filepaths.save_version=0
font=[]
for o in bpy.context.scene.objects:
 if o.type=='FONT' and o.get('feature_id') in {'WB1','WB2'}:
  p=[o.matrix_world@Vector(q) for q in o.bound_box];width=max(q.y for q in p)-min(q.y for q in p)
  o.scale.x*=5.12/width;bpy.context.view_layer.update();p=[o.matrix_world@Vector(q) for q in o.bound_box]
  width=max(q.y for q in p)-min(q.y for q in p);assert abs(width-5.12)<.0001
  font.append(dict(name=o.name,body=o.data.body,width=width))
 # Diagnostic2 showed the flattened fan center was far from tilted blade planes,
 # creating stretched triangular ribbons. Restore the center to the actual oval.
 if o.type=='MESH' and o.get('closeout_task')=='C08' and o.get('feature_id')=='GARDEN_VEGETATION_V3':
  me=o.data
  for p in me.polygons:
   if len(p.vertices)!=3:continue
   a,b,c=p.vertices
   if b!=a+1 or c!=a+8 or p.index+7>=len(me.polygons):continue
   faces=list(me.polygons[p.index:p.index+8])
   if all(len(f.vertices)==3 and f.vertices[2]==c and f.vertices[0]==a+j for j,f in enumerate(faces)):
    # Average opposite tips preserves the blade's own orientation and location.
    me.vertices[c].co=(me.vertices[a].co+me.vertices[a+4].co)*.5
  me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'font-repair-validation.json',dict(fonts=font,source_sha256=sha(T),reason='World-axis glyph width corrected; leaf fan center restored to blade plane'))
write(O/'final-snapshot.json',snapshot());print('DIAGNOSTIC_FAILURES_REPAIRED',font,flush=True)
