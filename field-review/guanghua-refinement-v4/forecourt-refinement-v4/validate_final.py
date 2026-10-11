import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
lock=json.loads((O/'baseline-lock.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(BASE))
def remaining_building(ob,exclude):
 bm=bmesh.new();bm.from_mesh(ob.data);unseen=set(bm.verts);kept=set()
 while unseen:
  todo=[unseen.pop()];vs=set(todo)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);vs.add(q);todo.append(q)
  ps=[ob.matrix_world@v.co for v in vs]
  if not exclude or not (max(p.z for p in ps)<3.46 and min(p.y for p in ps)<121):kept|=vs
 vert=sorted(tuple(ob.matrix_world@v.co) for v in kept)
 face=sorted(tuple(sorted(tuple(ob.matrix_world@v.co) for v in f.verts)) for f in bm.faces if all(v in kept for v in f.verts))
 bm.free();return hashlib.sha256(repr((vert,face)).encode()).hexdigest()
building={o.name:remaining_building(o,True) for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id')=='CONTEXT_GUANGHUA'}
fixed={o.name:digest(o) for o in bpy.context.scene.objects if o.type=='MESH' and (o.get('feature_id') in ['LAWN','LAWN_EDGE','WPATH','WOPEN','W_ENTRY'] or o.name.startswith('W_ENTRY'))}
stages=['stage00-v3-copy.blend','stage01-building-entry.blend','stage02-east-urn.blend','stage03-straight-path.blend','stage04-curve-repair.blend','forecourt-refined-v4.blend']
reopens=[]
for name in stages:
 bpy.ops.wm.open_mainfile(filepath=str(O/name))
 present={o.get('feature_id') for o in bpy.context.scene.objects if o.get('feature_id')}
 assert set(lock['required_ids'])<=present,(name,set(lock['required_ids'])-present)
 assert all(bpy.data.objects.get(n) and digest(bpy.data.objects[n])==h for n,h in fixed.items()),name
 if not name.startswith('stage00'):
  assert all(remaining_building(bpy.data.objects[n],False)==h for n,h in building.items()),('building',name)
 reopens.append(dict(file=name,reopens=True,original_feature_ids_retained=True,protected_lawn_and_west_meshes=len(fixed),protected_geometry_unchanged=True,building_body_unchanged=True,sha256=sha(O/name)))
# The final scene stays editable with fixed camera views and explicit metadata.
new=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id') in ['BUILDING_ENTRY','E_WALK'] or o.name=='EPATH continuous union surface']
assert all(math.isfinite(c) for o in new for v in o.data.vertices for c in v.co)
assert all(o.get('dimension_status') for o in new)
curve=solid_check(bpy.data.objects['EPATH continuous union surface'])
contact=[]
for side in ['east','west']:
 wall=bpy.data.objects['BENTRY '+side+' outer retaining wall'];cap=bpy.data.objects['BENTRY '+side+' outer coping']
 contact += [solid_check(wall),solid_check(cap),solid_check(bpy.data.objects['BENTRY '+side+' curved planter wall']),solid_check(bpy.data.objects['BENTRY '+side+' curved coping'])]
for i in range(2):assert bpy.data.objects[f'E_ENTRY {i} fluted bowl'].data!=bpy.data.objects[f'W_ENTRY {i} fluted bowl'].data
assert sha(BASE)==lock['source_sha256']
report=dict(source_sha256=lock['source_sha256'],source_unchanged=True,checkpoints=reopens,protected_building_body_topology_and_vertices_unchanged=True,protected_lawn_and_west_meshes=len(fixed),new_or_repaired_finite_meshes=len(new),new_geometry_dimensions_labeled_inferred=True,continuous_retaining_wall_solids=contact,curve_solid=curve,photos=[4464,4485,4491,4492,4496],limits=['No measured dimensions or solved camera calibration','Building context is the protected older proportion model','Decorative foliage and inherited soil-fill meshes not audited as architectural solids','No exhaustive all-pairs scene intersection certification'])
(O/'final-validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('FINAL_REOPEN_PROTECTION_VALIDATED',flush=True)
