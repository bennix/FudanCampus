import bpy,bmesh,json
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'west-entry-v3/west-entry-aligned-v3.blend'))
for ob in bpy.context.scene.objects:
 if ob.type!='MESH' or ob.get('feature_id')!='CONTEXT_GUANGHUA':continue
 if not any(t in ob.name for t in ['light stone','rose grey']):continue
 bm=bmesh.new();bm.from_mesh(ob.data);unseen=set(bm.verts);rs=[]
 while unseen:
  todo=[unseen.pop()];vs=set(todo)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);vs.add(q);todo.append(q)
  ps=[ob.matrix_world@v.co for v in vs];lo=[min(p[k] for p in ps) for k in range(3)];hi=[max(p[k] for p in ps) for k in range(3)]
  if lo[1]<121:rs.append(dict(lo=lo,hi=hi,n=len(vs)))
 print(ob.name,'MATRIX',str(list(ob.matrix_world)),'SOUTH_COMPONENTS',json.dumps(rs),flush=True)
 bm.free()
