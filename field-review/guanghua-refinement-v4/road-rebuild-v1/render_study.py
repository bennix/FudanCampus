"""Read-only review rendering of a previously saved study. Never resave model."""
import bpy,json,hashlib,sys
from pathlib import Path
O=Path(__file__).resolve().parent;batch=O/sys.argv[-1];target=batch/'west-exit-study.blend'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before_hash=sha(target)
bpy.ops.wm.open_mainfile(filepath=str(target));s=bpy.context.scene
neutral=bpy.data.materials.new('ROAD_QA_render_only');neutral.use_nodes=True
neutral.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.62,.62,.62,1)
for name,cam,clay in [('after-top-neutral','ROAD_SAMPLE_TOP',True),('after-exit-neutral','V4 east-exit',True),('after-exit-textured','V4 east-exit',False),('after-side-neutral','ROAD_SAMPLE_SIDE',True)]:
    path=batch/(name+'.png')
    if path.exists():raise RuntimeError('Review image already exists; use a new batch')
    restore=[]
    if clay:
        for o in bpy.data.objects:
            if o.type=='MESH' and o.get('feature_id')=='EPATH' and 'terrain' not in o.name:
                restore.append((o,list(o.data.materials)))
                for i in range(len(o.data.materials)):o.data.materials[i]=neutral
    s.camera=bpy.data.objects[cam];s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    for o,mats in restore:
        for i,m in enumerate(mats):o.data.materials[i]=m
assert sha(target)==before_hash
manifest={'model_sha256':before_hash,'base_sha256':sha(O.parent/'stage01-east.blend'),'batch':batch.name,'status':'diagnostic_visual_pending','build_script_sha256':sha(O/'build_roads_blender.py'),'render_script_sha256':sha(Path(__file__)),'configuration_sha256':sha(O/'road-generation-config.json'),'payload_sha256':sha(batch/'mesh-payload.json'),'cameras':{name:{'matrix':[list(r) for r in bpy.data.objects[name].matrix_world],'lens':bpy.data.objects[name].data.lens,'ortho_scale':bpy.data.objects[name].data.ortho_scale} for name in ['ROAD_SAMPLE_TOP','ROAD_SAMPLE_SIDE','V4 east-exit']}}
(batch/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('READ_ONLY_RENDER_DONE')
