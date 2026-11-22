"""Run in Blender: validate connected solid bodies and requested removals."""
import bpy, json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets/map-traced-neighbourhood.blend'))
report={}
for bid in ('46','51'):
 bodies=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith(bid) and str(o.get('building_id',''))==bid]
 assert len(bodies)==1,(bid,[o.name for o in bodies])
 obj=bodies[0];adj=[[] for _ in obj.data.vertices]
 for edge in obj.data.edges:
  a,b=edge.vertices;adj[a].append(b);adj[b].append(a)
 unseen=set(range(len(adj)));components=0
 while unseen:
  components+=1;todo=[unseen.pop()]
  while todo:
   for v in adj[todo.pop()]:
    if v in unseen:unseen.remove(v);todo.append(v)
 assert components==1,(bid,components)
 probes=[(145,68),(192,59)] if bid=='46' else [(190,184),(195,210)]
 for x,y in probes:
  hit,*_=obj.ray_cast(Vector(((x-176)*.48,(107-y)*.48,40)),Vector((0,0,-1)))
  assert hit,(bid,'gap at junction',x,y)
 report[bid]={'solid_components':components,'junction_probes':probes,'passed':True}
assert not any('东入口树' in o.name or o.name.startswith('入口花坛') for o in bpy.context.scene.objects)
report['removed']=['old placeholder entrance trees','old straight red/yellow strip']
report['entrance_planting']='new photo-based planting authorized by latest user correction'
bpy.context.view_layer.update()
a=Vector(((192-176)*.48,(107-208)*.48,0));b=Vector(((196-176)*.48,(107-233)*.48,0))
u=(b-a).normalized();normal=Vector((-u.y,u.x,0));offsets=[]
letters=[o for o in bpy.context.scene.objects if o.name.startswith('综合楼 · ')]
assert len(letters)==3
for letter in letters:
 offsets.extend((letter.matrix_world@v.co-a).dot(normal) for v in letter.data.vertices)
 probe=letter.location+Vector((0,0,.2))
 hit,point,*_=obj.ray_cast(probe+normal,-normal)
 assert hit and abs((point-a).dot(normal))<.03,'Sign is hidden behind another wall volume'
assert min(offsets)>=-.001 and max(offsets)<=.035,(min(offsets),max(offsets))
report['office_sign_wall_distance_m']=[min(offsets),max(offsets)]
(root/'output/map-joint-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False))
