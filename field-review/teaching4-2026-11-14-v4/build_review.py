"""Build/render a staged teaching4 candidate without touching production assets."""
from pathlib import Path
import hashlib
import importlib.util
import json
import math
import random
import sys
import time
import tempfile

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LOG = ROOT.parent / 'prompts_log/2026-11-14-teaching4-v4'
START = time.perf_counter()
export_temp=ROOT/'.local/blender-tmp'
export_temp.mkdir(parents=True,exist_ok=True)
tempfile.tempdir=str(export_temp)


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tracked_sources():
    paths = [ROOT / p for p in ['assets/buildings/17.blend', 'assets/buildings/55.blend',
             'scripts/teaching4_geometry.py', 'web/public/models/buildings/17.glb',
             'web/public/models/buildings/55.glb', 'web/public/campus-manifest.json',
             'web/public/campus-lod.json', 'web/public/buildings.json']]
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def setup_review():
    scene = bpy.context.scene
    scene.world = bpy.data.worlds.new('Review daylight')
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value = (.67,.72,.77,1)
    bg.inputs[1].default_value = .65
    light = bpy.data.lights.new('Review soft sun', 'SUN')
    light.energy = 2.1
    light.angle = .35
    ob = bpy.data.objects.new('Review soft sun', light)
    scene.collection.objects.link(ob)
    ob.rotation_euler = (.45,-.35,-.6)
    camera = bpy.data.objects.new('Review camera', bpy.data.cameras.new('Review camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 854
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    return scene, camera


VIEWS = [
    ('front', (35,-62,25), (0,-2,9), 43),
    ('rear', (30,60,25), (0,1,10), 48),
    ('side-door', (31,-18,6.5), (18,-4,3), 45),
    ('sculpture', (24,-29,10), (13.8,-11,3.3), 48),
    ('plan', (3,-2,68), (3,-2,0), 48),
    ('entry', (8,-20,5), (3.7,-7,1.9), 48),
    ('rear-window', (-5,20,5.5), (2,7,1.9), 50),
]


def render_views(label):
    scene, camera = setup_review()
    for name, pos, target, lens in VIEWS:
        if '--views' in mode and name not in mode[mode.index('--views')+1].split(','):continue
        camera.location = pos
        camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        camera.data.type = 'ORTHO' if name == 'plan' else 'PERSP'
        camera.data.ortho_scale = 59
        camera.data.lens = lens
        scene.render.filepath = str(HERE / f'renders/{label}-{name}.png')
        bpy.ops.render.render(write_still=True)
    # Ready-to-open source uses the front view.
    _, pos, target, lens = VIEWS[0]
    camera.location = pos
    camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
    camera.data.type = 'PERSP'
    camera.data.lens = lens
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces.active.region_3d.view_perspective = 'CAMERA'


def stone_textures(objects):
    # Deterministic small raster textures, assigned through UVs for actual GLB export.
    colors = {'T4 weathered book covers': (.30,.32,.29),
              'T4 stone page edges': (.48,.49,.44), 'T4 rough granite': (.45,.46,.41)}
    (HERE/'textures').mkdir(exist_ok=True)
    for index,(name,color) in enumerate(colors.items()):
        rng = random.Random(1700+index)
        image = bpy.data.images.new(f'granite-{index}', width=128, height=128)
        pixels=[]
        for y in range(128):
            for x in range(128):
                grain=rng.uniform(-.105,.105)
                if rng.random()<.04:grain += .15
                pixels.extend([max(.02,min(.95,c+grain)) for c in color]+[1])
        image.pixels = pixels
        image.filepath_raw = str(HERE/f'textures/granite-{index}.png')
        image.file_format = 'PNG'
        image.save()
        image.pack()
        material=bpy.data.materials.get(name)
        shader=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        texture=material.node_tree.nodes.new('ShaderNodeTexImage')
        texture.image=image
        material.node_tree.links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    for ob in objects:
        if not any(m.name in colors for m in ob.data.materials): continue
        uv=ob.data.uv_layers.new(name='StoneUV')
        for polygon in ob.data.polygons:
            normal=polygon.normal
            axes=(0,1) if abs(normal.z)>.7 else ((1,2) if abs(normal.x)>.7 else (0,2))
            for li in polygon.loop_indices:
                point=ob.data.vertices[ob.data.loops[li].vertex_index].co
                uv.data[li].uv=(point[axes[0]]*2,point[axes[1]]*2)


before = tracked_sources()
(LOG/'source-baseline.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
assert bpy.app.version[:3] == (4,4,3), 'Use project Blender 4.4.3'
mode = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--baseline' in mode:
    bpy.ops.wm.open_mainfile(filepath=str(HERE/'baseline/17.blend'))
    render_views('before')
else:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    spec = importlib.util.spec_from_file_location('teaching4_candidate',HERE/'source/teaching4_geometry.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    objects = module.build_teaching4()
    removed = 0
    for ob in objects:
        bm=bmesh.new()
        bm.from_mesh(ob.data)
        count=len(bm.faces)
        bmesh.ops.dissolve_degenerate(bm,dist=1e-6,edges=list(bm.edges))
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        removed += count-len(bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.update()
    stone_textures(objects)
    bpy.context.view_layer.update()
    exec(compile((HERE/'validate.py').read_text(encoding='utf-8'),str(HERE/'validate.py'),'exec'))
    exec(compile((HERE/'round2_validate.py').read_text(encoding='utf-8'),str(HERE/'round2_validate.py'),'exec'))
    exec(compile((HERE/'round3_validate.py').read_text(encoding='utf-8'),str(HERE/'round3_validate.py'),'exec'))
    bounds=[ob.matrix_world @ Vector(c) for ob in objects for c in ob.bound_box]
    triangles=sum(len(p.vertices)-2 for ob in objects for p in ob.data.polygons)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:ob.select_set(True)
    glb_path=HERE/'17-candidate.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb_path),export_format='GLB',use_selection=True,export_extras=True)
    import struct
    glb_data=glb_path.read_bytes();json_length=struct.unpack_from('<I',glb_data,12)[0]
    gltf=json.loads(glb_data[20:20+json_length])
    leaf_materials=[m for m in gltf['materials'] if 'tree leaves' in m.get('name','')]
    assert len(leaf_materials)==3 and all(m.get('alphaMode')=='MASK' and m.get('doubleSided') for m in leaf_materials), 'Tree alpha cutout export failed'
    assert all(n.get('extras',{}).get('campusVegetation') is True for n in gltf['nodes'] if 'Canopy T4' in n.get('name','') or 'Trunk T4' in n.get('name',''))
    render_views('after')
    bpy.ops.wm.save_as_mainfile(filepath=str(HERE/'17-candidate.blend'))
    source_objects=len(objects)
    materials=len({m.name for ob in objects for m in ob.data.materials})
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb_path))
    imported=[o for o in bpy.context.scene.objects if o.type=='MESH']
    assert len(imported)==source_objects, (len(imported),source_objects)
    assert len(bpy.data.images)>=3, 'Stone textures lost during GLB export'
    assert all(math.isfinite(c) for o in imported for v in o.data.vertices for c in v.co)
    report={'blender':bpy.app.version_string,'triangles':triangles,'mesh_objects':source_objects,
            'materials':materials,'glb_bytes':glb_path.stat().st_size,'glb_sha256':digest(glb_path),
            'cleaned_degenerate_faces':removed,
            'bounds_blender':{'min':[min(v[i] for v in bounds) for i in range(3)],
                              'max':[max(v[i] for v in bounds) for i in range(3)]},
            'glb_roundtrip':{'meshes':len(imported),'images':len(bpy.data.images)},
            'elapsed_seconds':round(time.perf_counter()-START,2),
            'status':'candidate awaiting human visual acceptance; production unchanged'}
    (HERE/'statistics.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
assert before==tracked_sources(), 'Production source changed'
print('REVIEW_STAGE_PASS', 'baseline' if '--baseline' in mode else 'candidate', 'production hashes unchanged')
