import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(O/'stage04-curve-repair.blend'));s=bpy.context.scene;before=all_digests()
cams={'top':bpy.data.objects['V4 ENTRY overhead'],'4485':bpy.data.objects['V4 approximate photo4485'],
 '4464':camera('V4 approximate photo4464',(-42,88.5,2.2),(-48,111,2.8),lens=27),
 'overall':bpy.data.objects['FINAL overall']}
render('stage05-before-4485.png',cams['4485'],width=1000,samples=12)
def plaza_pattern(x,y,rng):
 broad=(np.mod(x,6)<.18)|(np.mod(y,6)<.18)
 seam=(np.mod(x,1.2)<.009)|(np.mod(y,1.5)<.009)
 tile=.006*np.sin(np.floor(x/1.2)*17+np.floor(y/1.5)*11)
 return tile+.067*broad-.045*seam
mat=texture_material('V4 calibrated plaza granite',(.46,.447,.421),(12,12),plaza_pattern,1536)
mat['source_photos']=[4485,4464];mat['dimensions']='推定：大分格6，板缝1.2×1.5，浅带0.18；非现场测量'
targets=[bpy.data.objects['FORECOURT photo grid plaza']]
targets += [o for o in s.objects if o.type=='MESH' and o.get('feature_id')=='BUILDING_ENTRY' and any(t in o.name for t in ['upper platform','sloping ramp','upper landing wing','platform apron'])]
for ob in targets:
 oldslots=list(ob.data.materials)
 if ob.name=='FORECOURT photo grid plaza':ob.data.materials.clear();ob.data.materials.append(mat);slot=0
 else:ob.data.materials.append(mat);slot=len(ob.data.materials)-1
 for p in ob.data.polygons:
  if p.normal.z>.25:p.material_index=slot
 layer=ob.data.uv_layers.active
 for p in ob.data.polygons:
  if p.material_index!=slot:continue
  for li in p.loop_indices:
   q=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co;layer.data[li].uv=((q.x-20)/12,(q.y-100)/12)
 ob['paving_calibration']='4485 relative rectangular panel / large bay ratio; all modules inferred'
 ob['dimension_status']='推定 / photo proportion estimate; not measured'
for ob in s.objects:
 if ob.name.startswith('E_ENTRY') and any(t in ob.name for t in ['fluted bowl','rounded coping','pedestal core']):
  ob['dimension_status']='推定 / photo proportion estimate; not measured';ob['source_photos']=[4491]
assert all_digests()==before,'Paving stage unexpectedly changed geometry'
s['active_checkpoint']='v4 final: building access, east urn foot, separated straight path, curve union, plaza grid'
s['dimension_status']='All unmeasured dimensions 推定';s.camera=cams['4485']
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
bpy.ops.wm.save_as_mainfile(filepath=str(O/'forecourt-refined-v4.blend'))
save_report('stage05',dict(all_mesh_geometry_unchanged=True,material_targets=[o.name for o in targets],independent_material=True,estimated_large_bay=6,estimated_minor_panel=[1.2,1.5],estimated_band_width=.18,phase_origin=[20,100],views=['top','4485','4464','overall']))
for k,cam in cams.items():render('stage05-after-'+k+'.png',cam,k=='top',width=1600,samples=32,ratio=.42 if k=='top' else .75)
print('STAGE05_COMPLETE',flush=True)
