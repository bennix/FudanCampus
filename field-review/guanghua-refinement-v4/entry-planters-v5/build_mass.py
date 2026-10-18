import bpy,bmesh,json,math,hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np

O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(ob):
    me=ob.data;a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a)
    h=hashlib.sha256(a.tobytes()+str(list(ob.matrix_world)).encode()+str([tuple(p.vertices) for p in me.polygons]).encode())
    for uv in me.uv_layers:
        a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    h.update(str([m.name if m else None for m in me.materials]).encode())
    h.update(str([(m.name,m.type) for m in ob.modifiers]).encode())
    h.update(str(ob.get('feature_id')).encode())
    return h.hexdigest()
def coll(name):
    c=bpy.data.collections.get(name)
    if not c:c=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(c)
    return c
def metric_uv(ob):
    lay=ob.data.uv_layers.active or ob.data.uv_layers.new(name='P5 stone coordinates')
    for p in ob.data.polygons:
        k=max(range(3),key=lambda k:abs(p.normal[k]));axes=(1,2) if k==0 else (0,2) if k==1 else (0,1)
        for li in p.loop_indices:
            q=ob.data.vertices[ob.data.loops[li].vertex_index].co;lay.data[li].uv=(q[axes[0]],q[axes[1]])
def check(ob,evaluated=False):
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get()) if evaluated else None
    me=ev.to_mesh() if ev else ob.data
    bm=bmesh.new();bm.from_mesh(me)
    row=dict(name=ob.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),zero_area=sum(f.calc_area()<1e-8 for f in bm.faces),volume=bm.calc_volume(signed=True),finite=all(math.isfinite(c) for v in bm.verts for c in v.co),vertices=len(bm.verts),faces=len(bm.faces))
    bm.free()
    if ev:ev.to_mesh_clear()
    return row
def camera(name,loc,target,scale=None,lens=25):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);coll('12_P5 review cameras').objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO' if scale else 'PERSP';data.lens=lens;data.clip_end=1800
    if scale:data.ortho_scale=scale
    ob['camera_confidence']='Manual photo approximation; not calibrated from survey'
    return ob
def render(filename,cam,stone=False,top=False,width=1050,samples=12,ratio=.75):
    s=bpy.context.scene;hidden=[]
    for ob in s.objects:
        if ob.type!='MESH' or ob.hide_render:continue
        n=ob.name.lower()
        if (top and ob.get('feature_id')=='CONTEXT_GUANGHUA') or (stone and (ob.get('p5_role')=='vegetation' or n.startswith('bentry ') and ('planting' in n or 'broad leaves' in n or 'red flowers' in n))) or (top and any(k in n for k in ['leaves','canopy','tree-crown','mound'])):
            hidden.append(ob);ob.hide_render=True
    s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=samples;s.cycles.use_denoising=True
    s.render.resolution_x=width;s.render.resolution_y=round(width*ratio);s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.filepath=str(O/filename)
    bpy.ops.render.render(write_still=True)
    for ob in hidden:ob.hide_render=False
    print('RENDERED',filename,flush=True)

if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
    old_stems=['curved planter wall','curved coping','curved planter soil','burgundy planting','clipped green planting','outer retaining wall','outer coping']
    removed=[o.name for o in s.objects if o.name.startswith('BENTRY ') and any(k in o.name for k in old_stems)]
    relocated=[o.name for o in s.objects if o.name.startswith('BENTRY ') and any(' '+k+' ' in o.name for k in ('inner','outer')) and any(o.name.endswith(k) for k in ('urn','broad leaves','red flowers','soil'))]
    changed=set(removed+relocated)
    lock=dict(source=str(BASE),source_sha256=sha(BASE),changed_old_objects=sorted(changed),removed_old_objects=removed,protected={o.name:digest(o) for o in s.objects if o.type=='MESH' and o.name not in changed},required_ids=sorted({o.get('feature_id') for o in s.objects if o.get('feature_id')}))
    (O/'baseline-lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2),encoding='utf-8')
    cams={
      '4464':camera('P5 approximate IMG_4464',(-45,84,2.20),(-38,114,2.78),lens=22),
      '4485':camera('P5 approximate IMG_4485',(107,90,2.2),(40,111,2.0),lens=24),
      'pair-top':camera('P5 paired planters overhead',(20,111,180),(20,111,0),157),
      'west-top':camera('P5 left planter overhead',(-34.5,108.2,110),(-34.5,108.2,0),44),
      'east-top':camera('P5 right planter overhead',(74.4,108.6,110),(74.4,108.6,0),44),
      'west-junction':camera('P5 left wall plinth connection',(-41.7,94,3.55),(-46.05,100.22,.98),lens=38),
      'east-junction':camera('P5 right wall plinth connection',(81.1,94.4,3.5),(86.0,100.85,1.0),lens=38),
      'stair-side':camera('P5 stepped wall and entrance landing',(-9,99,7.7),(-22.5,114.4,2.6),lens=40),
    }
    (O/'cameras.json').write_text(json.dumps({k:dict(name=c.name,location=list(c.location),rotation=list(c.rotation_euler),type=c.data.type,lens=c.data.lens,ortho_scale=c.data.ortho_scale) for k,c in cams.items()},indent=2),encoding='utf-8')
    if not (O/'before-4464.png').exists():render('before-4464.png',cams['4464'],width=1500,samples=24)
    if not (O/'before-pair-top.png').exists():render('before-pair-top.png',cams['pair-top'],top=True,width=1500,samples=24,ratio=.34)
    if not (O/'before-4485.png').exists():render('before-4485.png',cams['4485'],width=1500,samples=24)
    if not (O/'before-west-junction.png').exists():render('before-west-junction.png',cams['west-junction'],stone=True,width=1500,samples=24)
    for n in removed:bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
    pack=json.loads((O/'geometry-pack.json').read_text(encoding='utf-8'))
    materials={'stone':bpy.data.materials['FC_warm_granite'],'cap':bpy.data.materials['FC_warm_granite'],'soil':bpy.data.materials['FIN_garden_grass'],'green':bpy.data.materials['FIN_hedge']}
    for key,col in [('red',(.145,.035,.054,1)),('yellow',(.25,.34,.065,1))]:
        mat=bpy.data.materials.new('P5 '+key+' shrub tone');mat.diffuse_color=col;mat.use_nodes=True
        node=mat.node_tree.nodes['Principled BSDF'];node.inputs['Base Color'].default_value=col;node.inputs['Roughness'].default_value=.89
        materials[key]=mat
    new=[]
    for row in pack['objects']:
        me=bpy.data.meshes.new(row['name']);me.from_pydata(row['vertices'],[],row['faces']);me.update()
        ob=bpy.data.objects.new(row['name'],me);coll('11_P5 entrance planters').objects.link(ob);me.materials.append(materials[row['material']])
        bm=bmesh.new();bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        bm.to_mesh(me);bm.free();me.update()
        ob['feature_id']='BUILDING_ENTRY';ob['p5_role']=row['role'];ob['p5_side']=row['side'];ob['source_photos']=[4464,4480] if row['side']=='west' else [4485,4480]
        ob['geometry_confidence']='Visible component relationship confirmed; footprint/scale/backside inferred'
        ob['dimension_status']='Scene units only; no surveyed dimension claim'
        for p in me.polygons:
            p.use_smooth=row['role']=='vegetation'
        metric_uv(ob);new.append(ob)
    translations=[]
    oldcenter={'west':{'inner':(-47.25,100),'outer':(-52.75,100)},'east':{'inner':(87.25,100),'outer':(92.75,100)}}
    for side in ('west','east'):
        for kind in ('inner','outer'):
            target=pack['plans'][side]['spec'][kind];src=oldcenter[side][kind];delta=Vector((target[0]-src[0],target[1]-src[1],0))
            for suffix in ('urn','broad leaves','red flowers','soil'):
                ob=bpy.data.objects['BENTRY '+side+' '+kind+' '+suffix]
                ob.data=ob.data.copy()
                for v in ob.data.vertices:v.co+=ob.matrix_world.inverted().to_3x3()@delta
                ob.data.update();ob['p5_base_relation']='Foot retained at z=.915; new plinth top shares same inherited height'
                translations.append(dict(object=ob.name,delta=list(delta)))
    reports=[check(ob) for ob in new]
    (O/'mass-mesh-checks.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    bad=[r for r in reports if r['nonmanifold'] or r['zero_area'] or r['volume']<=0 or not r['finite']]
    assert not bad,bad
    assert all(digest(bpy.data.objects[n])==h for n,h in lock['protected'].items())
    assert sha(BASE)==lock['source_sha256']
    s['active_checkpoint']='v5 independent entrance planter mass';s['p5_evidence']='4464 west; 4485 east; 4480 stair side; all dimensions inferred'
    s.camera=cams['4464'];s.render.resolution_x=1500;s.render.resolution_y=1125
    bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage01-planter-mass.blend'))
    (O/'mass-validation.json').write_text(json.dumps(dict(protected_objects=len(lock['protected']),protected_unchanged=True,baseline_unchanged=True,plan_checks=pack['checks'],relocations=translations,solids=reports),ensure_ascii=False,indent=2),encoding='utf-8')
    render('diagnostic-after-4464.png',cams['4464'])
    render('diagnostic-after-pair-top.png',cams['pair-top'],top=True,ratio=.34)
    render('diagnostic-after-west-junction.png',cams['west-junction'],stone=True)
    render('diagnostic-after-stair-side.png',cams['stair-side'],stone=True)
    print('MASS_CHECKPOINT_COMPLETE',flush=True)
