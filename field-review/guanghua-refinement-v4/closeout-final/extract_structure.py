import bpy,json
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'))
o=bpy.data.objects['EPATH continuous union surface'];o.data.calc_loop_triangles()
tri=[]
for t in o.data.loop_triangles:
 p=[o.matrix_world@o.data.vertices[i].co for i in t.vertices]
 if (p[1]-p[0]).cross(p[2]-p[0]).z>1e-7:tri.append([list(v) for v in p])
hard=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or o.hide_render:continue
 if o.get('feature_id') in {'ETERR','ESKY','EOPEN_S','EOPEN'} and any(k in o.name for k in ['support','flight','plinth','coping','floor','bottom','sloping']):
  p=[o.matrix_world@Vector(v) for v in o.bound_box]
  hard.append(dict(name=o.name,bounds=[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]]))
(O/'road-source.json').write_text(json.dumps(dict(triangles=tri,hard=hard)),encoding='utf-8')
