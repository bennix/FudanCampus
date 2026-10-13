"""Fixed cameras, two diagnostic batches and one formal batch with provenance."""
import bpy,sys,json,time
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;R=O.parent
sys.path.insert(0,str(O));from assemble import camera,read
sys.path.insert(0,str(R/'scene-unified-v5'));from scene_fingerprints import sha,write,plain
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
batch=args[0] if args else 'diagnostic1'
source=R/'scene-closeout-v7/guanghua-unified-closeout-v7.blend' if batch=='canopy-before' else O/('guanghua-closeout-structure.blend' if batch=='diagnostic1' else 'guanghua-closeout-final.blend')
views=[('overall','FINAL landscape',None,False),('top','Closeout overhead',None,False),
 ('west-platform','GV3 west platform photo 4390',4390,False),('east-understory','GV3 east understory photo 4582',4582,False),
 ('east-exit','SHAPE exit approximate',4568,False),('south-walk','V6 south photo4597',4597,False),
 ('west-planter','P5 approximate IMG_4464',4464,False),('east-planter','P5 approximate IMG_4485',4485,False),
 ('planter-top','P5 paired planters overhead',None,True),('plinth-junction','P5 left wall plinth connection',4464,True),
 ('garage-wb1','Closeout west garage',4416,False),('garage-wb2','Closeout east garage',4424,False),
 ('corridor-junction','A plaza junction low',4493,False),('plaque-front','Closeout plaque front',4468,False),
 ('plaque-oblique','Closeout plaque oblique',4468,False),('fudan','Closeout FUDAN',4603,False),
 ('pergola-seat','Closeout pergola seat',4547,False),('skylight-opening','Closeout skylight opening',4357,True),
 ('east-road-top','Closeout east road overhead',None,True),('east-road-side','Closeout east road side',None,True),
 ('mouth-w-n','Closeout mouth WOPEN',4453,True),('mouth-w-s','Closeout mouth WOPEN_S',4357,True),
 ('mouth-e-n','Closeout mouth EOPEN',4505,True),('mouth-e-s','Closeout mouth EOPEN_S',4492,True),
 ('leaf-detail','Closeout leaf detail',4582,False),('flower-detail','Closeout flower detail',4464,False),
 ('sculpture-side','Closeout sculpture side',4467,False),
 ('foyer-detail','Closeout foyer detail',4485,False),
 ('pergola-structure','Closeout pergola structure',4547,True)]
def configure():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=40 if batch=='final' else 12;s.cycles.use_denoising=True
 s.cycles.use_adaptive_sampling=batch=='final';s.cycles.adaptive_threshold=.035;s.cycles.adaptive_min_samples=8
 s.cycles.device='CPU';s.render.threads_mode='FIXED';s.render.threads=8
 s.render.resolution_x=1800 if batch=='final' else 900;s.render.resolution_y=round(s.render.resolution_x*.75);s.render.resolution_percentage=100
 s.render.film_transparent=False;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.view_settings.exposure=.65
 # Use a supported backend only when an actual compute device is present.
 try:
  prefs=bpy.context.preferences.addons['cycles'].preferences
  for mode in ['OPTIX','CUDA','ONEAPI','HIP']:
   try:
    prefs.compute_device_type=mode;prefs.get_devices();gpu=[d for d in prefs.devices if d.type==mode]
    if gpu:
     for d in prefs.devices:d.use=d.type==mode
     s.cycles.device='GPU';break
   except Exception:continue
 except Exception:pass
 return s
def supplement():
 if (O/'camera-overrides.json').exists():
  for name,row in read(O/'camera-overrides.json').items():
   c=camera(name,row['location'],row['target'],lens=row['lens']);c.rotation_euler.rotate_axis('Z',row['roll'])
 camera('Closeout overhead',(10,58,280),(10,58,0),scale=280)
 camera('Closeout east road overhead',(82,54,100),(82,54,0),scale=82)
 road_target=Vector((79,48,1.2));road_direction=(Vector((103,29,13))-road_target).normalized()
 camera('Closeout east road side',road_target+road_direction*180,road_target,scale=44)
 camera('Closeout west garage',(-85,48,2.3),(-74.5,48,.7),lens=32)
 camera('Closeout east garage',(-85,70,2.3),(-74.5,70,.7),lens=32)
 plaque=bpy.data.objects['POET_DONKEY inset nameplate'];c=sum((plaque.matrix_world@v.co for v in plaque.data.vertices),Vector())/len(plaque.data.vertices)
 # Front is sculpture local -Y rotated about Z; original plaque rotation retained.
 front=plaque.matrix_world.to_3x3()@Vector((0,-1,0));front.normalize()
 camera('Closeout plaque front',c+front*2.5,c,lens=48,scale=1.7)
 camera('Closeout plaque oblique',c+front*2.3+Vector((1.3,-.2,.7)),c,lens=48)
 camera('Closeout FUDAN',(26.0,-1.2,2.0),(26.0,9.7,1.15),lens=32)
 camera('Closeout pergola seat',(101.0,30.5,2.2),(96.5,36.8,.8),lens=32)
 camera('Closeout skylight opening',(-39,41.2,3.8),(-33,47.2,.6),lens=30)
 for fid in ['WOPEN','WOPEN_S','EOPEN','EOPEN_S']:
  ob=bpy.data.objects[fid+'__tread__FIN_granite'];pts=[ob.matrix_world@Vector(p) for p in ob.bound_box];lo=Vector(tuple(min(p[i] for p in pts) for i in range(3)));hi=Vector(tuple(max(p[i] for p in pts) for i in range(3)));center=(lo+hi)/2
  camera('Closeout mouth '+fid,center+Vector((-4.4,6.7,4.6)),center+Vector((0,0,.5)),lens=36)
 camera('Closeout leaf detail',(83.8,60.3,2.6),(81.41,62.90,.9),lens=55)
 camera('Closeout flower detail',(-58.6,94.5,4.2),(-53.6,99.52,1.7),lens=55)
 camera('Closeout foyer detail',(20,108,4.2),(20,126,5.0),lens=38)
 camera('Closeout pergola structure',(121,4,17),(93,27,2),scale=38)
 landmark=bpy.data.objects['POET_DONKEY base core 1'];pp=[landmark.matrix_world@Vector(p) for p in landmark.bound_box];lc=sum(pp,Vector())/8
 camera('Closeout sculpture side',lc+Vector((5.5,-4.5,3.0)),lc+Vector((0,0,2.0)),lens=42)
records=[]
manifest=O/f'{batch}-render-manifest.json'
if manifest.exists():records=[r for r in read(manifest) if r['source_sha256']==sha(source)]
if batch=='diagnostic1':
 selected=[views[i] for i in [6,7,8,9,4,18,19,2]]
 jobs=[('before-'+k,R/'scene-closeout-v7/guanghua-unified-closeout-v7.blend',c,p,h) for k,c,p,h in [selected[0],selected[4]]]+[(k,source,c,p,h) for k,c,p,h in selected]
elif batch=='diagnostic2':jobs=[(k,source,c,p,h) for k,c,p,h in [views[i] for i in [2,3,5,6,7,10,11,13,14,15,16,17]]]
elif batch=='canopy-before':jobs=[(k,source,c,p,h) for k,c,p,h in [views[i] for i in [2,3,4,5]]]
else:jobs=[(k,source,c,p,h) for k,c,p,h in views]
if len(args)>1:
 wanted=set(args[1:])
 if batch!='diagnostic1':jobs=[(k,source,c,p,h) for k,c,p,h in views if k in wanted]
 else:jobs=[j for j in jobs if j[0] in wanted]
last=None
for key,model,cname,photo,stone in jobs:
 if model!=last:bpy.ops.wm.open_mainfile(filepath=str(model));supplement();last=model
 s=configure();c=bpy.data.objects[cname];s.camera=c;hidden=[]
 if stone:
  for o in s.objects:
   if o.type!='MESH' or o.hide_render:continue
   n=o.name.lower()
   if o.get('feature_id') in {'GARDEN_VEGETATION_V3','TREE_CANOPY_V6','VEGETATION','VEGETATION_V2'} or o.get('closeout_role')=='vegetation' or any(w in n for w in ['planting','leaves','red flowers','planted-shrubs','hedge']):hidden.append(o);o.hide_render=True
 if key=='planter-top':s.render.resolution_y=round(s.render.resolution_x*.4)
 image=O/f'{batch}-{key}.png';s.render.filepath=str(image);t=time.time()
 print('RENDER_START',batch,key,s.cycles.device,flush=True);bpy.ops.render.render(write_still=True)
 for o in hidden:o.hide_render=False
 row=dict(view=key,image=image.name,source=str(model),source_sha256=sha(model),camera=cname,camera_matrix=plain(c.matrix_world),lens=c.data.lens,
 camera_type=c.data.type,ortho_scale=c.data.ortho_scale,primary_photo=photo,pose_confidence='approximate; photo anchors require review',
 resolution=[s.render.resolution_x,s.render.resolution_y],samples=s.cycles.samples,adaptive_sampling=s.cycles.use_adaptive_sampling,adaptive_threshold=s.cycles.adaptive_threshold,compute_device=s.cycles.device,exposure=s.view_settings.exposure,seconds=round(time.time()-t,2),
 hidden_objects=[o.name for o in hidden],image_sha256=sha(image))
 records=[r for r in records if r['view']!=key];records.append(row);write(manifest,records);print('RENDER_DONE',key,row['seconds'],flush=True)
print('BATCH_COMPLETE',batch,len(records),flush=True)
