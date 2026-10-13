import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(O/'stage01-building-entry.blend'));s=bpy.context.scene;before=all_digests()
cams={'top':bpy.data.objects['FC entry top'],'4491':camera('V4 approximate photo4491',(71.5,85,2.35),(63.2,76,1.4),lens=27)}
render('stage02-before-4491.png',cams['4491'],width=1000,samples=10)
changed=[];solids=[];details=[]
for i in range(2):
 name=f'E_ENTRY {i} fluted bowl';old=bpy.data.objects[name]
 ps=[old.matrix_world@v.co for v in old.data.vertices];cx=(min(p.x for p in ps)+max(p.x for p in ps))/2;cy=(min(p.y for p in ps)+max(p.y for p in ps))/2
 changed.append(name)
 profile=[(.72,.92),(.74,.947),(.74,.999),(.68,1.04),(.57,1.065),(.48,1.16),(.48,1.25),(.65,1.31),(.87,1.53),(1.10,1.77),(1.15,1.83),(1.10,1.88),(.99,1.85),(.88,1.67),(.66,1.49),(0,1.47)]
 ob=lathe(name+' refined',cx,cy,profile,old.data.materials[0],'E_ENTRY',[4491],.018)
 bpy.data.objects.remove(old,do_unlink=True);ob.name=name;ob['revision']='v4 east foot proportion';solids.append(solid_check(ob))
 cap=bpy.data.objects[f'E_ENTRY {i} rounded coping'];changed.append(cap.name);cap.data=cap.data.copy()
 for v in cap.data.vertices:
  if v.co.z<.86:v.co.z=.835
 for m in cap.modifiers:
  if m.type=='BEVEL':m.width=.026
 uv(cap);solids.append(solid_check(cap))
 core=bpy.data.objects[f'E_ENTRY {i} pedestal core'];changed.append(core.name);core.data=core.data.copy()
 for v in core.data.vertices:
  if v.co.z>.7:v.co.z=.84
 solids.append(solid_check(core))
 details.append(dict(center=[cx,cy],foot_radius=.74,bowl_radius=1.15,foot_to_bowl_diameter_ratio=.74/1.15,coping_thickness=.085,coping_top=.92,bowl_foot_bottom=.92))
 for k in ('fluted bowl','rounded coping','pedestal core'):
  east=bpy.data.objects[f'E_ENTRY {i} {k}'];west=bpy.data.objects[f'W_ENTRY {i} {k}']
  east['dimension_status']='推定 / photo proportion estimate; not measured';east['source_photos']=[4491]
  assert east.data!=west.data,(k,'shared mesh still coupled')
unchanged=verify_unchanged(before,changed)
s.camera=cams['4491'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage02-east-urn.blend'))
save_report('stage02',dict(protected_meshes_unchanged=unchanged,west_urns_unchanged=True,east_shared_data_detached=True,details=details,solids=solids,views=['top','4491']))
for k,cam in cams.items():render('stage02-after-'+k+'.png',cam,k=='top',width=1400,samples=24)
print('STAGE02_COMPLETE',flush=True)
