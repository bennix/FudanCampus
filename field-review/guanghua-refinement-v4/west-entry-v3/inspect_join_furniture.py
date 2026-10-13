import bpy,json
from pathlib import Path
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O/'west-entry-aligned-v3.blend'))
rows=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH':continue
 if ob.get('feature_id') in ('WPATH','W_ENTRY','GROUND','FORECOURT','LAWN','LAWN_EDGE'):continue
 points=[ob.matrix_world@v.co for v in ob.data.vertices]
 ids=[i for i,p in enumerate(points) if -47<p.x<-40 and 74<p.y<80 and 0<p.z<2]
 if not ids:continue
 chosen=[points[i] for i in ids]
 rows.append(dict(name=ob.name,fid=ob.get('feature_id'),count=len(ids),bounds=[[min(p[k] for p in chosen) for k in range(3)],[max(p[k] for p in chosen) for k in range(3)]],materials=[m.name for m in ob.data.materials]))
print(json.dumps(rows,ensure_ascii=False,indent=2),flush=True)
