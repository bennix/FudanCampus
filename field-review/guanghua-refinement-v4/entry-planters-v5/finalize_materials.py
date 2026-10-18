"""Close the iteration using the stable latest model and foliage materials only.

Latest user direction supersedes the unfinished geometric study. Never imports
geometry-pack.json or overwrites the accepted v4 source.
"""
import sys,json,math,hashlib
from pathlib import Path
import bpy,numpy as np
O=Path(__file__).resolve().parent
sys.path.insert(0,str(O))
from build_mass import BASE,digest,sha,camera,render,check

def geometry_hash(ob):
    a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
    return hashlib.sha256(a.tobytes()+str([tuple(p.vertices) for p in ob.data.polygons]).encode()+str(list(ob.matrix_world)).encode()).hexdigest()

def foliage(kind):
    n=1024;rng=np.random.default_rng(93055 if kind=='red' else 93056)
    base=np.array((.052,.012,.019) if kind=='red' else (.042,.085,.012))
    tone=np.array((.19,.052,.072) if kind=='red' else (.18,.29,.036))
    rgba=np.ones((n,n,4),np.float32);rgba[:,:,:3]=base
    h=np.full((n,n),.18,np.float32)
    # Periodic overlapping small leaves, with edge shadows, raised centre veins,
    # orientation and tone variation. Texture is packed into the checkpoint.
    for _ in range(2300):
        cx,cy=rng.uniform(0,n,2);length=rng.uniform(15,34);width=length*rng.uniform(.38,.65);a=rng.uniform(0,math.tau)
        radius=int(math.ceil(length))+2
        yy,xx=np.mgrid[-radius:radius+1,-radius:radius+1]
        u=xx*math.cos(a)+yy*math.sin(a);v=-xx*math.sin(a)+yy*math.cos(a)
        ell=(u/length)**2+(v/width)**2
        mask=ell<1
        idsY=(np.round(cy).astype(int)+yy[mask])%n;idsX=(np.round(cx).astype(int)+xx[mask])%n
        edge=np.sqrt(np.clip(1-ell[mask],0,1));vein=np.exp(-np.abs(v[mask])/1.1)*.085
        light=.60+.55*edge+.12*u[mask]/length
        color=tone*rng.uniform(.64,1.35)
        leaf=color[None,:]*light[:,None]+vein[:,None]*np.array([.48,.42,.18])
        rgba[idsY,idsX,:3]=np.clip(leaf,.003,.70)
        h[idsY,idsX]=.24+.51*edge+vein
    for label,pixels,color_space in [('albedo',rgba,'Non-Color'),('height',np.dstack((h,h,h,np.ones_like(h))),'Non-Color')]:
        im=bpy.data.images.new('P5 '+kind+' shrub '+label,width=n,height=n)
        im.colorspace_settings.name=color_space
        im.pixels.foreach_set(pixels.astype(np.float32).ravel())
        assert max(im.pixels[0:2000])>.02
        im.filepath_raw=str(O/('foliage-'+kind+'-'+label+'.png'));im.file_format='PNG';im.save();im.pack()
    mat=bpy.data.materials.new('P5 layered '+kind+' shrub foliage');mat.use_nodes=True
    nt=mat.node_tree;bs=nt.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.87
    bs.inputs['Specular IOR Level'].default_value=.22
    uv=nt.nodes.new('ShaderNodeTexCoord');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=1/1.45
    nt.links.new(uv.outputs['UV'],scale.inputs[0])
    for label in ('albedo','height'):
        tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images['P5 '+kind+' shrub '+label];tx.extension='REPEAT';tx.interpolation='Linear';nt.links.new(scale.outputs[0],tx.inputs['Vector'])
        if label=='albedo':nt.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
        else:
            bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.64;bump.inputs['Distance'].default_value=.034
            nt.links.new(tx.outputs['Color'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    mat.diffuse_color=(*tone,1);mat['source']='Photographic palette from IMG_4464/4485; synthesized leaf texture, species and leaf scale inferred'
    return mat

bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
before={o.name:digest(o) for o in s.objects if o.type=='MESH'}
before_geo={o.name:geometry_hash(o) for o in s.objects if o.type=='MESH'}
source_sha=sha(BASE)
targets={f'BENTRY {side} {suffix}':kind for side in ('west','east') for suffix,kind in [('burgundy planting','red'),('clipped green planting','green')]}
materials={k:foliage(k) for k in ('red','green')}
for name,kind in targets.items():
    ob=bpy.data.objects[name];ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(materials[kind])
    ob['p5_scope']='Material finish only, per latest user direction; geometry retained from v4'
    ob['p5_palette_refs']=[4464,4485];ob['p5_foliage_scale']='Inferred visual density, not measured'
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets)
assert all(geometry_hash(bpy.data.objects[n])==h for n,h in before_geo.items())
geometric_same=[]
for name in targets:
    geometric_same.append(dict(object=name,vertices=len(bpy.data.objects[name].data.vertices),faces=len(bpy.data.objects[name].data.polygons),material=bpy.data.objects[name].data.materials[0].name))
camdata=json.loads((O/'cameras.json').read_text())
cams={}
for key,d in camdata.items():
    ob=camera(d['name'],d['location'],(0,0,0),d['ortho_scale'] if d['type']=='ORTHO' else None,d['lens'])
    ob.rotation_euler=d['rotation'];cams[key]=ob
s['active_checkpoint']='v5 reviewable foliage material finish'
s['p5_scope']='Latest user instruction: finish reviewable version using foliage materials; no further geometry refinement'
s.camera=cams['4464'];s.render.resolution_x=1500;s.render.resolution_y=1125
FINAL=O/'entry-planters-review-v5.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(FINAL))
report=dict(scope='Material finish on stable v4 geometry; unfinished geometric study not applied',source=str(BASE),source_sha256=source_sha,protected_meshes=len(before)-len(targets),protected_geometry_uv_materials_unchanged=True,modified_objects=geometric_same,all_geometry_retained=True,textures_packed=True,dimensions='No measured dimensions added; v4 geometry and elevations remain inferred',views=[])
(O/'final-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CHECKPOINT_SAVED',str(FINAL),flush=True)
for key,stone,top,ratio in [('4464',False,False,.75),('pair-top',False,True,.34),('4485',False,False,.75),('west-top',False,True,.75),('east-top',False,True,.75),('west-junction',True,False,.75),('east-junction',True,False,.75)]:
    if not(stone and (O/('after-'+key+'.png')).exists()):render('after-'+key+'.png',cams[key],stone=stone,top=top,width=1500,samples=20,ratio=ratio)
    report['views'].append(key)
    (O/'final-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(FINAL))
assert all(digest(bpy.data.objects[n])==h for n,h in before.items() if n not in targets)
assert all(geometry_hash(bpy.data.objects[n])==h for n,h in before_geo.items())
assert sha(BASE)==source_sha
for name in targets:
    ob=bpy.data.objects[name];assert ob.data.materials[0].name=='P5 layered '+targets[name]+' shrub foliage'
assert all(bpy.data.images['P5 '+kind+' shrub '+label].packed_file for kind in ('red','green') for label in ('albedo','height'))
report.update(checkpoint_reopened=True,source_unchanged=True,final_sha256=sha(FINAL),render_complete=True)
(O/'final-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REVIEWABLE_VERSION_COMPLETE',flush=True)
