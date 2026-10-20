"""Reopen the three independent files, validate GLB buffers and semantic detail groups."""
import bpy,json,struct,hashlib,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
expected={'xiyuan':['bridge X bracing','pond water','pavilion','lotus','flag pole'],'yeyaozhen':['curved ceramic facade','round ceramic shop columns','side exterior staircase','叶','学生'],'teaching3':['exposed return stair treads','gallery ceiling grid','central entry stairs','metal sphere sculpture','第三教学楼']}
reports=[]
for key,features in expected.items():
    path=ROOT/f'field-review/{key}-photo-v1';blend=path/f'{key}.blend';glb=path/f'{key}.glb'
    bpy.ops.wm.open_mainfile(filepath=str(blend));meshes=[o for o in bpy.context.scene.objects if o.type=='MESH'];names='|'.join(o.name for o in meshes)
    for feature in features:assert feature in names,(key,feature)
    if key=='teaching3':
        assert 'annex exterior stairs' not in names and 'annex stair rail' not in names, 'User-rejected annex staircase remains'
        sphere=bpy.data.objects['metal sphere sculpture']
        assert max(sphere.dimensions)-min(sphere.dimensions)<1e-5, 'Sculpture must be spherical in all three axes'
        assert abs(sphere.dimensions.x-1.66)<1e-5
    for o in meshes:
        assert all(math.isfinite(c) for v in o.data.vertices for c in v.co),o.name
        assert all(p.area>1e-12 for p in o.data.polygons),(key,o.name,'zero-area polygon')
    raw=glb.read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);assert magic==b'glTF' and version==2 and length==len(raw)
    n=struct.unpack_from('<I',raw,12)[0];g=json.loads(raw[20:20+n]);assert g['buffers'][0]['byteLength']<=len(raw)-28-n
    for view in g.get('bufferViews',[]):assert view.get('byteOffset',0)+view['byteLength']<=g['buffers'][view.get('buffer',0)]['byteLength']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(glb))
    count=len([o for o in bpy.context.scene.objects if o.type=='MESH']);assert count>20
    reports.append({'model':key,'blend_reopened':True,'finite_vertices':True,'no_zero_area_faces':True,'required_features':features,'glb_reimported_meshes':count,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(ROOT/'field-review/campus-photos-2026-10-20/validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
print('PHOTO_STUDIES_VALID',reports)
