"""Read-only equivalent compressed-production GLB reimport audit."""
import bpy,json,hashlib,math,time
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reference=read(O/'decoded-reimport-reference.json')
production=Path(reference['compressed_production']);decoded=Path(reference['decoded_qa_file'])
assert sha(production)==reference['production_sha256']
assert sha(decoded)==reference['decoded_sha256']
started=time.time();bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(decoded))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
lo=[math.inf]*3;hi=[-math.inf]*3;nonfinite=0;triangles=0
for o in meshes:
 o.data.calc_loop_triangles();triangles+=len(o.data.loop_triangles)
 for v in o.data.vertices:
  q=o.matrix_world@v.co
  for i in range(3):
   if not math.isfinite(q[i]):nonfinite+=1
   lo[i]=min(lo[i],q[i]);hi[i]=max(hi[i],q[i])
texts=[]
for expected in reference['texts']:
 matches=[o for o in bpy.context.scene.objects if o.get('text_content')==expected['body'] and o.get('feature_id')==expected['feature']]
 assert len(matches)==1,(expected['name'],[o.name for o in matches])
 o=matches[0];geometry=[o] if o.type=='MESH' else [c for c in o.children_recursive if c.type=='MESH']
 assert geometry,expected['name'];p=[g.matrix_world@v.co for g in geometry for v in g.data.vertices]
 b={'min':[min(q[i] for q in p) for i in range(3)],'max':[max(q[i] for q in p) for i in range(3)]}
 error=max(abs(b[k][i]-expected['bounds_blender'][k][i]) for k in ['min','max'] for i in range(3))
 assert error<.002,(expected['name'],error)
 texts.append({'name':o.name,'body':expected['body'],'feature':expected['feature'],'bounds_blender':b,'maximum_decode_reimport_bound_error':error,'triangles':sum(len(g.data.loop_triangles) for g in geometry)})
assert nonfinite==0
assert triangles==reference['triangles'],(triangles,reference['triangles'])
bounds={'min':lo,'max':hi}
bound_error=max(abs(bounds[k][i]-reference['bounds_blender'][k][i]) for k in ['min','max'] for i in range(3))
assert bound_error<.002,bound_error
assert sha(production)==reference['production_sha256'],'Production asset modified during QA'
result={'pass':True,'method':reference['method'],'production_sha256':reference['production_sha256'],'source_sha256':reference['source_sha256'],
 'temporary_derivative_is_not_a_production_asset':True,'blender_version':bpy.app.version_string,'mesh_objects':len(meshes),'triangles_all_lod_levels':triangles,'nonfinite':nonfinite,
 'bounds_blender':bounds,'maximum_global_decode_reimport_bound_error':bound_error,'texts':texts,'seconds':round(time.time()-started,2),'production_asset_unchanged':True}
(O/'decoded-reimport-check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('PRODUCTION_GLB_EQUIVALENT_REIMPORT_PASS',len(meshes),triangles,len(texts),flush=True)
