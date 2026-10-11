import bpy,math,json
from pathlib import Path
O=Path(__file__).resolve().parent
for file in ['scene-closeout-v7/guanghua-unified-closeout-v7.blend','closeout-final/guanghua-closeout-final.blend']:
 bpy.ops.wm.open_mainfile(filepath=str(O.parent/file));o=bpy.data.objects['East hedge ESKY__planted-shrubs__leaf-green'];me=o.data
 for p in me.polygons:
  if len(p.vertices)==3:
   a,b,c=p.vertices
   if b==a+1 and c==a+8:
    print('SAMPLE',file,list(p.vertices),[list(me.vertices[a+j].co) for j in range(9)],'area',p.area,'bounds',list(o.dimensions),'mat',p.material_index,flush=True);break
 print('AREAS',min(p.area for p in me.polygons),max(p.area for p in me.polygons),'BOUNDS',list(o.matrix_world),flush=True)
