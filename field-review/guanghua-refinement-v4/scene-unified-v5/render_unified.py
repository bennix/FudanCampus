"""Every delivery view reopens the same validated unified scene. Never saves rendering changes."""
import bpy,sys,json,time
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O))
from scene_fingerprints import sha,write
M=json.loads((O/'version-manifest.json').read_text(encoding='utf-8'))
V=json.loads((O/'validation.json').read_text(encoding='utf-8'))
OUT=Path(M['scene']);assert sha(OUT)==M['scene_sha256']==V['scene_sha256']
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
diagnostic='diagnostic' in args
views=[('overall','FINAL landscape',1800,.75,40),('top','UNIFIED full scene overhead',1800,.75,28),
       ('entry-planters','P5 paired planters overhead',1800,.42,32),('east-straight-path','A approximate IMG4492',1800,.75,32),
       ('entry-material-detail','P5 approximate IMG_4464',1800,.75,32)]
records=[]
for key,name,width,ratio,samples in views:
    # The exact saved scene is the content source of each individual image.
    bpy.ops.wm.open_mainfile(filepath=str(OUT));S=bpy.context.scene
    if key=='top':
        data=bpy.data.cameras.new(name);cam=bpy.data.objects.new(name,data);S.collection.objects.link(cam)
        cam.location=(10,58,280);cam.rotation_euler=(Vector((10,58,0))-cam.location).to_track_quat('-Z','Y').to_euler()
        data.type='ORTHO';data.ortho_scale=280;data.clip_end=2000
    else:cam=bpy.data.objects[name]
    S.camera=cam;S.render.engine='CYCLES';S.cycles.device='CPU';S.cycles.samples=8 if diagnostic else samples
    S.cycles.use_denoising=True;S.render.threads_mode='FIXED';S.render.threads=8
    S.render.resolution_x=900 if diagnostic else width;S.render.resolution_y=round(S.render.resolution_x*ratio);S.render.resolution_percentage=100
    S.render.image_settings.file_format='PNG';S.render.film_transparent=False
    S.view_settings.view_transform='AgX';S.view_settings.exposure=.65
    filename=('diagnostic-' if diagnostic else '')+key+'.png';S.render.filepath=str(O/filename)
    start=time.time();bpy.ops.render.render(write_still=True)
    records.append({'view':key,'image':filename,'model':str(OUT),'model_sha256':M['scene_sha256'],
     'camera':name,'camera_matrix':[list(r) for r in cam.matrix_world],'camera_type':cam.data.type,
     'lens':cam.data.lens,'ortho_scale':cam.data.ortho_scale,'width':S.render.resolution_x,'height':S.render.resolution_y,
     'samples':S.cycles.samples,'exposure':.65,'visibility_policy':'Exact checkpoint visibility; no scene meshes hidden for rendering',
     'seconds':round(time.time()-start,1),'image_sha256':sha(O/filename)})
    write(O/('diagnostic-render-manifest.json' if diagnostic else 'render-manifest.json'),records)
    print('RENDER_DONE',key,records[-1]['seconds'],flush=True)
assert sha(OUT)==M['scene_sha256']
if not diagnostic:
    M['status']='validated and rendered; visual review pending';M['render_manifest']='render-manifest.json';write(O/'version-manifest.json',M)
print('RENDERS_COMPLETE',len(records),flush=True)
