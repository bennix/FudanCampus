import bpy, json
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(O.parent/'forecourt-v2/forecourt-complete-v2.blend'))
rows=[]
for ob in bpy.context.scene.objects:
 if ob.type!='MESH': continue
 bb=[ob.matrix_world@Vector(v) for v in ob.bound_box]
 lo=[min(v[i] for v in bb) for i in range(3)]; hi=[max(v[i] for v in bb) for i in range(3)]
 if hi[0]<-85 or lo[0]>-19 or hi[1]<70 or lo[1]>100: continue
 fid=ob.get('feature_id')
 if fid in ['FURNITURE','VEGETATION_V2','GROUND','EDGE_PATHS','WPATH','WOPEN','WOPEN_S','LAWN','FORECOURT','LAWN_EDGE']:
  row=dict(name=ob.name,fid=fid,bounds=[lo,hi],vertices=len(ob.data.vertices),materials=[m.name for m in ob.data.materials])
  if fid in ['FURNITURE','VEGETATION_V2']:
   points=[ob.matrix_world@v.co for v in ob.data.vertices if -33<(ob.matrix_world@v.co).x<-20 and 87<(ob.matrix_world@v.co).y<91 and (ob.matrix_world@v.co).z<3]
   if points: row['urn_region']={'vertices':len(points),'bounds':[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]]}
  if fid=='EDGE_PATHS' and 'edge-walk' in ob.name:
   row['western_end_vertices']=[list(ob.matrix_world@v.co) for v in ob.data.vertices if (ob.matrix_world@v.co).x<0 and (ob.matrix_world@v.co).y>70]
  rows.append(row)
(O/'inventory.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps([r for r in rows if r.get('urn_region') or r['fid'] in ['WPATH','WOPEN','WOPEN_S','EDGE_PATHS','FORECOURT']],ensure_ascii=False),flush=True)
s=bpy.context.scene
camdata=bpy.data.cameras.new('WEST ENTRY before');cam=bpy.data.objects.new('WEST ENTRY before',camdata);s.collection.objects.link(cam)
cam.location=(-26.3,107,29);target=Vector((-26.3,78,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=36
s.camera=cam;s.render.resolution_x=1100;s.render.resolution_y=900;s.render.resolution_percentage=100;s.cycles.samples=12;s.render.filepath=str(O/'before-west-oblique.png');bpy.ops.render.render(write_still=True)
