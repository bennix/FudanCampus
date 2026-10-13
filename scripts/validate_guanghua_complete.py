"""Focused assembly regression checks; reads accepted files without changing them."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'field-review/guanghua-complete-v3'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'guanghua-complete-v3.blend'))
s=bpy.context.scene;report=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
current=next(o for o in s.objects if o.get('feature_id')=='LAWN' and o.type=='MESH')
sourcepath=ROOT/'field-review/guanghua-lawn-shape-v2/guanghua-lawn-shape-v2.blend'
with bpy.data.libraries.load(str(sourcepath),link=False) as (src,dst):dst.objects=src.objects
source=next(o for o in dst.objects if o.get('feature_id')=='LAWN' and o.type=='MESH')
assert len(current.data.vertices)==len(source.data.vertices)
deviation=max((a.co-b.co).length for a,b in zip(current.data.vertices,source.data.vertices));assert deviation<1e-7,deviation
assert all(abs(a-b)<1e-6 for a,b in zip(current.scale,(1,1,1)))
report['lawn_local_vertex_max_deviation_m']=deviation
for o in dst.objects:bpy.data.objects.remove(o,do_unlink=True)
assembly=json.loads((OUT/'assembly.json').read_text());dx=assembly['east_translation_x']
dep=bpy.context.evaluated_depsgraph_get();hits=[]
for fid,x,y in [('WOPEN',-32,81),('WOPEN_S',-32,48),('EOPEN',79+dx,78),('EOPEN_S',78+dx,49.5)]:
 hit,loc,n,idx,obj,m=s.ray_cast(dep,Vector((x,y,5)),Vector((0,0,-1)))
 assert hit and obj.get('feature_id')==fid,(fid,obj.name if obj else None)
 assert -.95<loc.z<-.4,(fid,loc.z)
 hits.append(dict(id=fid,visible_tread_z=loc.z,object=obj.name))
for fid,y in [('WB1',48),('WB2',70)]:
 hit,loc,n,idx,obj,m=s.ray_cast(dep,Vector((-77,y,1)),Vector((0,0,-1)))
 assert hit and obj.get('feature_id')==fid and -.8<loc.z<-.2,(fid,obj.name if obj else None,loc.z)
 hits.append(dict(id=fid,visible_apron_z=loc.z,object=obj.name))
report['entry_surface_ray_checks']=hits
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in report['baselines_unchanged'].items())
required=set(report['required_21_ids']);assert required<={o.get('feature_id') for o in s.objects}
report['final_camera_count']=len([o for o in s.objects if o.type=='CAMERA' and o.name.startswith('FINAL ')])
report['packed_image_count']=sum(bool(im.packed_file) for im in bpy.data.images)
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('ASSEMBLY_VALIDATED',len(hits),'visible entry surfaces; lawn vertices unchanged; protected hashes unchanged')
