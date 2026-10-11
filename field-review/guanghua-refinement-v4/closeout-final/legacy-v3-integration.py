"""Derive campus landscape assets; never overwrite accepted source scenes or GLBs."""
import bpy, bmesh, json, hashlib
from pathlib import Path
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / 'web/public'
OUT = ROOT / 'field-review/guanghua-campus-integration'
OUT.mkdir(exist_ok=True)
SOURCE = ROOT / 'field-review/guanghua-complete-v3/guanghua-complete-v3.blend'
MANIFEST = json.loads((PUBLIC / 'campus-manifest.json').read_text(encoding='utf-8'))
BUILDING = next(b for b in MANIFEST['buildings'] if b['id'] == '27')
SCALE = 2 / 3
TRANSLATION = Vector((BUILDING['position'][0] - 20*SCALE,
                      -BUILDING['position'][2] - 153*SCALE, 0))
TRANSFORM = Matrix.Translation(TRANSLATION) @ Matrix.Scale(SCALE, 4)
LOCAL_RECT = (-90, 112.3021175619119, -9, 124)
X0, X1, Y0, Y1 = (LOCAL_RECT[0]*SCALE+TRANSLATION.x,
                  LOCAL_RECT[1]*SCALE+TRANSLATION.x,
                  LOCAL_RECT[2]*SCALE+TRANSLATION.y,
                  LOCAL_RECT[3]*SCALE+TRANSLATION.y)
BASELINES = [SOURCE, PUBLIC/'models/shared/00-hanbing-v14.glb', PUBLIC/'models/shared/05.glb']
BASELINES += [PUBLIC / b['url'] for b in MANIFEST['buildings']]
HASHES = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in BASELINES}
report = dict(source=str(SOURCE.relative_to(ROOT)), scale=SCALE, translation_blender=list(TRANSLATION),
              footprint_blender=[X0,X1,Y0,Y1], baselines=HASHES,
              registration='Uniform 2/3 scale matching the existing 1.5x contextual building; provisional, not surveyed')

def export(path, objects=None):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects or list(bpy.context.scene.objects):
        if o.type == 'MESH': o.hide_set(False); o.select_set(True)
    path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
                              export_cameras=False, export_lights=False, export_extras=True)

def bounds(o):
    vs=[o.matrix_world @ Vector(v) for v in o.bound_box]
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]

def overlaps(o):
    lo,hi=bounds(o)
    return hi[0]>X0 and lo[0]<X1 and hi[1]>Y0 and lo[1]<Y1

def signature(o):
    h=hashlib.sha256()
    h.update(str(tuple(tuple(row) for row in o.matrix_world)).encode())
    for v in o.data.vertices:h.update(str(tuple(v.co)).encode())
    for p in o.data.polygons:h.update(str((tuple(p.vertices),p.material_index)).encode())
    return h.hexdigest()

# Flatten evaluated meshes so fonts, bevels and all accepted transforms survive export.
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
source_scene=bpy.context.scene
dep=bpy.context.evaluated_depsgraph_get()
scene=bpy.data.scenes.new('Guanghua campus landscape')
ids=set()
web_materials={}
def compatible_material(material):
    if material is None or not material.use_nodes:return material
    shader=next((n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if not shader or not shader.inputs['Base Color'].is_linked:return material
    # glTF cannot serialize Noise/ColorRamp/Brick shader graphs. An unsupported
    # linked Base Color exports as white, ignoring the socket's default value.
    # Image-textured materials already export correctly and remain untouched.
    if any(n.type=='TEX_IMAGE' for n in material.node_tree.nodes):return material
    if material.name not in web_materials:
        derived=material.copy();derived.name=material.name+'_web'
        shader=next(n for n in derived.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        socket=shader.inputs['Base Color']
        for link in list(socket.links):derived.node_tree.links.remove(link)
        socket.default_value=material.diffuse_color
        derived['web_color_source']='Original diffuse_color fallback for unsupported procedural shader'
        web_materials[material.name]=derived
    return web_materials[material.name]
for o in list(source_scene.objects):
    fid=o.get('feature_id') or (o.parent.get('feature_id') if o.parent else None)
    if o.type not in {'MESH','FONT','CURVE'} or fid=='CONTEXT_GUANGHUA':continue
    mesh=bpy.data.meshes.new_from_object(o.evaluated_get(dep), preserve_all_data_layers=True, depsgraph=dep)
    for i,material in enumerate(mesh.materials):mesh.materials[i]=compatible_material(material)
    copy=bpy.data.objects.new('GH_'+o.name,mesh);scene.collection.objects.link(copy)
    copy.matrix_world=TRANSFORM @ o.matrix_world
    for key in o.keys():copy[key]=o[key]
    copy['feature_id']=fid or 'UNCLASSIFIED'
    copy['campus_landscape']='guanghua-complete-v3'
    copy['campusVegetation']=bool(fid=='VEGETATION' and any(k in o.name.lower() for k in ['canop','trunk','branch']))
    ids.add(fid)
bpy.context.window.scene=scene
bpy.context.view_layer.update()
report['feature_ids']=sorted(i for i in ids if i)
report['procedural_color_fallbacks']={name:list(material.diffuse_color) for name,material in web_materials.items()}
assert {'LAWN','WTERR','ETERR','WB1','WB2','WOPEN','WOPEN_S','EOPEN','EOPEN_S','DING','SIGN','FLOWER'}<=ids
landscape=PUBLIC/'models/landscape/guanghua-complete-v3.glb'
export(landscape)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'guanghua-campus-landscape.blend'))

# Cut only the replacement footprint from existing terrain and roads. This also
# removes the old rectangle and exposes the six accepted below-grade entries.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(PUBLIC/'models/shared/00-hanbing-v14.glb'))
objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
untouched={o.name:signature(o) for o in objects if not overlaps(o)}
bpy.ops.mesh.primitive_cube_add(size=1, location=((X0+X1)/2,(Y0+Y1)/2,-2))
cutter=bpy.context.object;cutter.name='GH replacement footprint cutter'
cutter.dimensions=(X1-X0,Y1-Y0,10)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
changed=[]
for o in objects:
    if not overlaps(o):continue
    lo,hi=bounds(o)
    if lo[0]>=X0-1e-5 and hi[0]<=X1+1e-5 and lo[1]>=Y0-1e-5 and hi[1]<=Y1+1e-5:
        changed.append(dict(name=o.name,action='removed'));bpy.data.objects.remove(o,do_unlink=True);continue
    bpy.context.view_layer.objects.active=o
    mod=o.modifiers.new('Guanghua replacement footprint','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name)
    changed.append(dict(name=o.name,action='clipped',faces=len(o.data.polygons)))
bpy.data.objects.remove(cutter,do_unlink=True)
assert all(signature(bpy.data.objects[n])==h for n,h in untouched.items())
report['terrain_changes']=changed;report['unchanged_terrain_objects']=len(untouched)
export(PUBLIC/'models/shared/00-guanghua-v3.glb')

# Remove complete connected tree/foliage components inside the replacement site,
# retaining every vertex and polygon outside it exactly in the editable mesh.
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(PUBLIC/'models/shared/05.glb'))
removed=[]
for o in list(bpy.context.scene.objects):
    if o.type!='MESH' or not overlaps(o):continue
    bm=bmesh.new();bm.from_mesh(o.data);seen=set();delete=[];count=0
    # glTF splits vertices at flat normals. Traverse coincident vertices as well
    # as edges, without welding or otherwise changing the surviving geometry.
    coincident={}
    for v in bm.verts:coincident.setdefault(tuple(round(c,5) for c in v.co),[]).append(v)
    for v in bm.verts:
        if v in seen:continue
        component=[];stack=[v];seen.add(v)
        while stack:
            p=stack.pop();component.append(p)
            for q in coincident[tuple(round(c,5) for c in p.co)]:
                if q not in seen:seen.add(q);stack.append(q)
            for edge in p.link_edges:
                q=edge.other_vert(p)
                if q not in seen:seen.add(q);stack.append(q)
        center=o.matrix_world @ (sum((p.co for p in component),Vector())/len(component))
        if X0<=center.x<=X1 and Y0<=center.y<=Y1:delete.extend(component);count+=1
    if delete:
        bmesh.ops.delete(bm,geom=delete,context='VERTS');bm.to_mesh(o.data);o.data.update()
        removed.append(dict(name=o.name,components=count,vertices=len(delete)))
    bm.free()
report['old_vegetation_removed']=removed
export(PUBLIC/'models/shared/05-guanghua-v3.glb')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in HASHES.items())
(OUT/'integration.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('GUANGHUA_ASSETS_EXPORTED',len(ids),'features; originals unchanged. Manifest not changed yet.')
