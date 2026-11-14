"""Build only 55 with Blender 4.4.3, then export/reimport and render."""
from pathlib import Path
import bpy,bmesh,sys,json,hashlib,time,random,tempfile
from mathutils import Vector
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(HERE))
from chemistry_geometry import build_chemistry, BRICK_SRGB
from check_model import validate
assert bpy.app.version[:3]==(4,4,3)
temp=ROOT/'.local/blender-tmp';temp.mkdir(parents=True,exist_ok=True);tempfile.tempdir=str(temp)
mode=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []

def mat(name,color,rough=.75):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough
    return m

def mesh(name,vs,fs,m):
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m)
    ob=bpy.data.objects.new(name,me);bpy.context.scene.collection.objects.link(ob)
    return ob

VIEWS=[('front',(51,-87,31),(0,-3,6),42),('rear',(-51,87,31),(0,3,6),42),
       ('east',(55,-15,9),(32.8,0,5),44),('entry',(12,-24,7),(0,-7,3),43),
       ('west',(-58,-32,24),(-25,0,6),43),('plan',(0,0,100),(0,0,0),45)]

def render(label):
    scene=bpy.context.scene
    for ob in list(scene.objects):
        if ob.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(ob,do_unlink=True)
    scene.world=bpy.data.worlds.new('Review daylight');scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.67,.72,.77,1);bg.inputs[1].default_value=.65
    light=bpy.data.lights.new('Review sun','SUN');light.energy=2.1;light.angle=.35
    ob=bpy.data.objects.new('Review sun',light);scene.collection.objects.link(ob);ob.rotation_euler=(.45,-.35,-.6)
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(camera);scene.camera=camera
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    scene.render.resolution_x=1200;scene.render.resolution_y=800;scene.render.resolution_percentage=100
    scene.view_settings.view_transform='AgX'
    (HERE/'renders').mkdir(exist_ok=True)
    for name,pos,target,lens in VIEWS:
        if '--views' in mode and name not in mode[mode.index('--views')+1].split(','):continue
        camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type='ORTHO' if name=='plan' else 'PERSP';camera.data.ortho_scale=78;camera.data.lens=lens
        scene.render.filepath=str(HERE/f'renders/{label}-{name}.png');bpy.ops.render.render(write_still=True)

if '--baseline' in mode:
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'web-integration-backup/assets/buildings/55.blend'))
    render('before')
else:
    start=time.perf_counter();bpy.ops.wm.read_factory_settings(use_empty=True)
    objects=build_chemistry(0,0,mat,mesh,bpy.context.scene.collection,bpy)
    for ob in objects:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    bpy.context.view_layer.update();validate()
    # Small deterministic brick bitmap and explicit UVs survive GLB export.
    rng=random.Random(55);im=bpy.data.images.new('Chemistry brick courses',width=256,height=128)
    pixels=[]
    for v in range(128):
        row=v//16
        for u in range(256):
            mortar=v%16<1 or (u+(16 if row%2 else 0))%32<1
            c=(211/255,149/255,130/255) if mortar else BRICK_SRGB
            noise=rng.uniform(-.008,.008)
            pixels.extend([max(0,min(1,a+noise)) for a in c]+[1])
    im.pixels=pixels;im.pack()
    m=bpy.data.materials['Chemistry deep red brick'];node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
    m.node_tree.links.new(node.outputs['Color'],m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    for ob in objects:
        if not any(m.name=='Chemistry deep red brick' for m in ob.data.materials):continue
        uv=ob.data.uv_layers.new(name='BrickUV')
        for p in ob.data.polygons:
            axes=(1,2) if abs(p.normal.x)>.5 else (0,2)
            for li in p.loop_indices:
                co=ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv.data[li].uv=(co[axes[0]]/2.4,co[axes[1]]/1.2)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    target=HERE/'55-candidate.glb'
    bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_extras=True)
    bounds=[ob.matrix_world@Vector(c) for ob in objects for c in ob.bound_box]
    stats=dict(blender=bpy.app.version_string,triangles=sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons),
      mesh_objects=len(objects),glb_bytes=target.stat().st_size,glb_sha256=hashlib.sha256(target.read_bytes()).hexdigest(),
      bounds_blender=dict(min=[min(v[i] for v in bounds) for i in range(3)],max=[max(v[i] for v in bounds) for i in range(3)]))
    stats['brick_base_srgb']='#D46B57'
    render('after');bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'55-candidate.blend'))
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(target))
    validate();assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==len(objects)
    stats['elapsed_seconds']=round(time.perf_counter()-start,2)
    (HERE/'statistics.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    print('CHEMISTRY_CANDIDATE_PASS',stats)
