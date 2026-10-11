"""Read-only reopen and continuity check; never saves a Blender scene."""
import bpy,json,math,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-lawn-survey-v1'
expected={f['id'] for f in json.loads((OUT/'survey.json').read_text(encoding='utf-8'))['features']}
bpy.ops.wm.open_mainfile(filepath=str(OUT/'model/guanghua-lawn-v1.blend'))
actual={o.get('feature_id') for o in bpy.data.objects}
assert expected<=actual,expected-actual
meshes=[o for o in bpy.data.objects if o.type=='MESH']
assert all(math.isfinite(v) for o in meshes for p in o.data.vertices for v in p.co)
glbs={}
for name in ['guanghua-lawn-v1.glb','guanghua-lawn-site-only.glb']:
 raw=(OUT/'model'/name).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
 assert magic==b'glTF' and version==2 and length==len(raw)
 n,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
 d=json.loads(raw[20:20+n]);ids={n.get('extras',{}).get('feature_id') for n in d['nodes']}
 assert expected<=ids,expected-ids
 if 'site-only' in name:assert 'CONTEXT_GUANGHUA' not in ids
 glbs[name]={'parses':True,'all_location_ids_present':True,'nodes':len(d['nodes'])}
report={'checkpoint_reopens':True,'all_21_locations_present':True,'finite_mesh_coordinates':True,'mesh_objects':len(meshes),'glb':glbs,'not_claimed':['survey-grade positions or dimensions','complete object-level labels for all photos','exhaustive intersection or topology validation']}
(OUT/'model/checkpoint-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report))
