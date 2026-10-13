import bpy,sys,json,time
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import sha,write
M=json.loads((O/'version-manifest.json').read_text(encoding='utf-8'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
batch=args[0] if args else 'diagnostic1';final=batch=='final';diagnostic=not final
views=[('overall','FINAL landscape'),('top','V6 overhead'),('west-platform','GV3 west platform photo 4390'),('east-understory','GV3 east understory photo 4582'),('east-exit','SHAPE exit approximate'),('south-walk','V6 south photo4597'),('south-elevation','V6 south crown elevation')]
if batch=='diagnostic1':jobs=[('before-west-platform',M['source'],views[2][1]),('before-east-understory',M['source'],views[3][1]),('before-south-walk',M['source'],views[5][1])]+[(k,M['scene'],c) for k,c in [views[0],views[2],views[3],views[5],views[6]]]
elif batch=='diagnostic2':jobs=[('before-south-walk',M['source'],views[5][1])]+[(k,M['scene'],c) for k,c in [views[0],views[1],views[2],views[3],views[5],views[6]]]
else:jobs=[(k,M['scene'],c) for k,c in [views[2],views[3],views[5],views[6],views[0],views[1],views[4]]]
records=[]
for key,model,name in jobs:
    bpy.ops.wm.open_mainfile(filepath=model);S=bpy.context.scene
    if name not in bpy.data.objects:
        d=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,d);S.collection.objects.link(cam)
        if name=='V6 overhead':cam.location=(10,58,280);target=(10,58,0);d.type='ORTHO';d.ortho_scale=280
        elif name=='V6 south photo4597':cam.location=(59,14.5,1.75);target=(-20,14.5,3.4);d.lens=29
        else:raise ValueError(name)
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();d.clip_end=2500
    else:cam=bpy.data.objects[name]
    S.camera=cam;S.render.engine='CYCLES';S.cycles.samples=12 if diagnostic else (40 if key in ['overall','west-platform','east-understory','south-walk'] else 32);S.cycles.use_denoising=True;S.cycles.device='CPU'
    S.render.threads_mode='FIXED';S.render.threads=8;S.render.resolution_x=900 if diagnostic else 1600;S.render.resolution_y=round(S.render.resolution_x*.75);S.render.resolution_percentage=100
    S.render.film_transparent=False;S.view_settings.view_transform='AgX';S.view_settings.exposure=.65;S.render.image_settings.file_format='PNG'
    filename=f'{batch}-{key}.png' if diagnostic else f'{key}.png';S.render.filepath=str(O/filename);t=time.time();bpy.ops.render.render(write_still=True)
    records.append(dict(view=key,image=filename,model=model,model_sha256=sha(model),camera=name,camera_matrix=[list(r) for r in cam.matrix_world],lens=cam.data.lens,type=cam.data.type,ortho_scale=cam.data.ortho_scale,resolution=[S.render.resolution_x,S.render.resolution_y],samples=S.cycles.samples,exposure=.65,seconds=round(time.time()-t,1),visibility='All checkpoint mesh visibility retained; no hidden content overrides',image_sha256=sha(O/filename)))
    write(O/f'{batch}-render-manifest.json',records);print('RENDER_DONE',batch,key,records[-1]['seconds'],flush=True)
assert sha(M['scene'])==M['scene_sha256'];assert sha(M['source'])==M['source_sha256'];print('BATCH_COMPLETE',batch,len(records),flush=True)
