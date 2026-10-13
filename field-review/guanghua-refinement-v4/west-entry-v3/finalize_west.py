"""Complete the accepted diagnostic, weld the path join, and validate delivery."""
import bpy, bmesh, hashlib, json, math, struct
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from export_visible_glb import export_visible_glb
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O = Path(__file__).resolve().parent
BASE = O.parent/'forecourt-v2/forecourt-complete-v2.blend'
DIAG = O/'diagnostic-west-entry.blend'
INFO = json.loads((O/'build-info.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources = {str(p): sha(p) for p in (BASE, DIAG)}
assert sources[str(BASE)] == INFO['source_sha256']

def digest(ob):
    a = np.empty(len(ob.data.vertices)*3, np.float32)
    ob.data.vertices.foreach_get('co', a)
    return hashlib.sha256(a.tobytes()+str(list(ob.matrix_world)).encode()+str([tuple(p.vertices) for p in ob.data.polygons]).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(BASE))
old_names = {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and
             (o.name.startswith('FURNITURE__') and any(k in o.name for k in
              ('urn-plinth', 'plinth-cap', 'geometry__pale', 'urn-planting', 'urn-flowers')) or o.name == 'V2 leaves FURNITURE')}
changed = old_names | {o.name for o in bpy.context.scene.objects if o.get('feature_id') == 'WOPEN'} | {
    'V2 leaves WOPEN', 'GROUND__terrain__FIN_garden_grass', 'GROUND__landscape-slab__soil',
    'FORECOURT photo grid plaza', 'EDGE_PATHS__edge-walk__FIN_pavers',
    'WPATH__west-garden__stone', 'WPATH__curb-west-garden__pale',
    'FURNITURE__bench__rail', 'FURNITURE__bench__benchwood'}
protected = {o.name: digest(o) for o in bpy.context.scene.objects if o.type == 'MESH' and o.name not in changed}
opening_before = {o.name: o.matrix_world.copy() for o in bpy.context.scene.objects if o.type == 'MESH' and
                  (o.get('feature_id') == 'WOPEN' or o.name == 'V2 leaves WOPEN')}
path_south = {n: sorted(tuple(v.co) for v in bpy.data.objects[n].data.vertices if
                       (bpy.data.objects[n].matrix_world @ v.co).y < 74.99)
              for n in ('WPATH__west-garden__stone', 'WPATH__curb-west-garden__pale')}
required_ids = {o.get('feature_id') for o in bpy.context.scene.objects if o.type == 'MESH' and o.get('feature_id')}
bpy.ops.wm.open_mainfile(filepath=str(DIAG)); s = bpy.context.scene
assert all(digest(bpy.data.objects[n]) == h for n, h in protected.items())
assert not any(bpy.data.objects.get(n) for n in old_names)
assert all(abs(bpy.data.objects[n].matrix_world.translation.y - m.translation.y - INFO['north_opening_translation_y']) < 1e-5
           for n, m in opening_before.items())

for name in ('W_ENTRY recessed garden path border', 'W_ENTRY recessed garden connection'):
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)

def metric_uv(ob):
    layer = ob.data.uv_layers.active
    if not layer: layer = ob.data.uv_layers.new(name='W_ENTRY_metric')
    for p in ob.data.polygons:
        axis = max(range(3), key=lambda k: abs(p.normal[k]))
        axes = (1, 2) if axis == 0 else (0, 2) if axis == 1 else (0, 1)
        for li in p.loop_indices:
            q = ob.matrix_world @ ob.data.vertices[ob.data.loops[li].vertex_index].co
            layer.data[li].uv = (q[axes[0]], q[axes[1]])

# Build identical centre lines; start with the exact horizontal cut section.
path = bpy.data.objects['WPATH__west-garden__stone']
end = [path.matrix_world @ v.co for v in path.data.vertices if abs((path.matrix_world @ v.co).y-75) < 1e-5]
cx = (min(p.x for p in end)+max(p.x for p in end))/2
a, b, c, d = [Vector(p) for p in ((cx,75), (cx,76.3), (-42.8,76.1), (-41.5,76.1))]
qs = []; tangents = []
for i in range(41):
    t = i/40; u = 1-t
    qs.append(u**3*a+3*u*u*t*b+3*u*t*t*c+t**3*d)
    tangents.append((3*u*u*(b-a)+6*u*t*(c-b)+3*t*t*(d-c)).normalized())
for i in range(1, 34):
    qs.append(d.lerp(Vector((-28.8,76.1)), i/33)); tangents.append(Vector((1,0)))

seams = []
for name, width in (('WPATH__west-garden__stone', 1.50), ('WPATH__curb-west-garden__pale', 1.74)):
    ob = bpy.data.objects[name]; inv = ob.matrix_world.inverted()
    cut = [ob.matrix_world @ v.co for v in ob.data.vertices if abs((ob.matrix_world @ v.co).y-75) < 1e-5]
    x0, x1 = min(p.x for p in cut), max(p.x for p in cut)
    z0, z1 = min(p.z for p in cut), max(p.z for p in cut)
    bm = bmesh.new(); bm.from_mesh(ob.data)
    cap = [f for f in bm.faces if all(abs((ob.matrix_world @ v.co).y-75) < 1e-5 for v in f.verts)]
    assert cap, name
    bmesh.ops.delete(bm, geom=cap, context='FACES_ONLY')
    ring0 = []
    for x,z in ((x0,z0),(x1,z0),(x1,z1),(x0,z1)):
        matches = [v for v in bm.verts if (ob.matrix_world @ v.co - Vector((x,75,z))).length < 1e-5]
        assert len(matches) == 1
        ring0.append(matches[0])
    previous = ring0
    for i, (q, tangent) in enumerate(zip(qs[1:], tangents[1:]), 1):
        f = min(1, (q-qs[0]).length/1.5); f = f*f*(3-2*f)
        w = (x1-x0)*(1-f) + width*f
        offset = Vector((-tangent.y, tangent.x))*w/2
        left, right = q+offset, q-offset
        ring = [bm.verts.new(inv @ Vector((p.x,p.y,z))) for p,z in ((left,z0),(right,z0),(right,z1),(left,z1))]
        for k in range(4): bm.faces.new((previous[k], previous[(k+1)%4], ring[(k+1)%4], ring[k]))
        previous = ring
    bm.faces.new(previous)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert all(e.is_manifold for e in bm.edges), name
    assert bm.calc_volume(signed=True) > 0
    bm.to_mesh(ob.data); bm.free(); ob.data.update()
    # Only map new loops, retaining existing south UVs.
    layer = ob.data.uv_layers.active
    if not layer:
        metric_uv(ob)
        layer = ob.data.uv_layers.active
    for p in ob.data.polygons:
        if not any((ob.matrix_world @ ob.data.vertices[i].co).y > 75 for i in p.vertices): continue
        for li in p.loop_indices:
            q = ob.matrix_world @ ob.data.vertices[ob.data.loops[li].vertex_index].co
            layer.data[li].uv = (q.x, q.y)
    south_now = sorted(tuple(v.co) for v in ob.data.vertices if (ob.matrix_world @ v.co).y < 74.99)
    assert path_south[name] == south_now, (name,len(path_south[name]),len(south_now))
    ob['west_entry_join'] = 'Shared welded cross section at y=75; continuous watertight mesh'
    seams.append(dict(object=name, shared_section=[x0,x1,75,z0,z1], boundary_edges=0, south_vertices_unchanged=True))

# Union a full-depth infill into the existing terrain, with the same top level.
ground = bpy.data.objects['GROUND__terrain__FIN_garden_grass']
patch = bpy.data.objects['W_ENTRY old stair hole infill']
gz0 = min((ground.matrix_world @ v.co).z for v in ground.data.vertices)
gz1 = max((ground.matrix_world @ v.co).z for v in ground.data.vertices)
for v in patch.data.vertices: v.co.z = gz0-.01 if v.co.z < -.9 else gz1
bpy.context.view_layer.objects.active = ground
mod = ground.modifiers.new('Old north stair hole filled to terrain depth', 'BOOLEAN')
mod.operation='UNION'; mod.solver='EXACT'; mod.object=patch
bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(patch, do_unlink=True)

# Actual surface rays catch holes and doubled surface levels at the joins.
def bvh(ob):
    deps = bpy.context.evaluated_depsgraph_get(); ev=ob.evaluated_get(deps); me=ev.to_mesh()
    tree=BVHTree.FromPolygons([ob.matrix_world@v.co for v in me.vertices], [list(p.vertices) for p in me.polygons], all_triangles=False)
    ev.to_mesh_clear(); return tree
terrain = bvh(ground)
for x in (-33.3,-32,-30.7):
    for y in (79.2,81,82.8):
        p,_,_,_=terrain.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),8)
        assert p and abs(p.z-gz1)<1e-5, ('old hole',x,y,p)
for x in (-33.3,-32,-30.7):
    for y in (70.2,71.85,73.5):
        p,_,_,_=terrain.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),8)
        assert p is None or p.z < -.5, ('new hole',x,y,p)
road=bvh(path); path_samples=[]
for y in (74.8,74.99,75,75.01):
    p,_,_,_=road.ray_cast(Vector((cx,y,1)),Vector((0,0,-1)),2)
    assert p and abs(p.z-.094)<1e-5, ('join surface',y,p)
    path_samples.append([cx,y,p.z])
for q in qs[:-1]:
    p,_,_,_=road.ray_cast(Vector((q.x,q.y,1)),Vector((0,0,-1)),2)
    assert p and abs(p.z-.094)<1e-5, ('connection',list(q),p)
assert abs(max((path.matrix_world@v.co).x for v in path.data.vertices if (path.matrix_world@v.co).y>75)-(-28.8))<1e-5

# Only the bench at the rebuilt bend needs clearance. These two meshes also
# contain unrelated benches, so translate individual disconnected components.
bench_changes=[]
for name in ('FURNITURE__bench__rail','FURNITURE__bench__benchwood'):
    ob=bpy.data.objects[name]
    selected={v.index for v in ob.data.vertices if -47<(ob.matrix_world@v.co).x<-40 and 74<(ob.matrix_world@v.co).y<80}
    assert selected
    assert all(not(selected&set(p.vertices)) or set(p.vertices)<=selected for p in ob.data.polygons)
    other={v.index:tuple(v.co) for v in ob.data.vertices if v.index not in selected}
    delta=ob.matrix_world.inverted().to_3x3()@Vector((-2.1,0,0))
    for index in selected:ob.data.vertices[index].co+=delta
    assert all(tuple(ob.data.vertices[i].co)==co for i,co in other.items())
    ob.data.update()
    points=[ob.matrix_world@ob.data.vertices[i].co for i in selected]
    for p in points:
        hit,_,_,_=road.ray_cast(Vector((p.x,p.y,2)),Vector((0,0,-1)),3)
        assert hit is None,('bench clearance',name,p)
    bench_changes.append(dict(object=name,translated_vertices=len(selected),translation=[-2.1,0,0],other_bench_vertices_unchanged=True,
                              bounds=[[min(p[k] for p in points) for k in range(3)],[max(p[k] for p in points) for k in range(3)]]))

for i in range(2):
    for ob in [o for o in s.objects if o.name.startswith(f'W_ENTRY {i} ')]:
        src=bpy.data.objects[ob['source_component']]
        assert ob.data == src.data
        assert abs(ob.matrix_world.translation.y-src.matrix_world.translation.y)<1e-5
        assert abs(ob.matrix_world.translation.z-src.matrix_world.translation.z)<1e-5

walk = bpy.data.objects['EDGE_PATHS__edge-walk__FIN_pavers']
assert abs(max((walk.matrix_world@v.co).y for v in walk.data.vertices if (walk.matrix_world@v.co).x<0)-INFO['entry_line'])<1e-5
assert all(digest(bpy.data.objects[n]) == h for n,h in protected.items())
required_ids.remove('FURNITURE') if not any(o.get('feature_id')=='FURNITURE' for o in s.objects) else None
assert required_ids <= {o.get('feature_id') for o in s.objects}
solids=[]
for ob in [ground,path,bpy.data.objects['WPATH__curb-west-garden__pale'],bpy.data.objects['FORECOURT photo grid plaza']]:
    bm=bmesh.new();bm.from_mesh(ob.data)
    row=dict(name=ob.name,nonmanifold_edges=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True))
    bm.free();assert row['nonmanifold_edges']==0 and row['volume']>0,row;solids.append(row)

def camera(name,loc,target,scale):
    data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);s.collection.objects.link(ob)
    ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()
    data.type='ORTHO';data.ortho_scale=scale;data.clip_end=1500;return ob

cameras={k:bpy.data.objects[v] for k,v in INFO['cameras'].items()}
cameras['path-join']=camera('W3 welded path seam',(cx+1,86,14),(cx+1,75.8,.08),11)
# Explicit Blender orientation keeps west on the left and north at the top.
pair=cameras['paired-top']; pair.location=(19.15,75,120);pair.rotation_euler=(0,0,0);pair.data.ortho_scale=118
s['scope']='Complete west entrance alignment; accepted east urn copies; welded west garden path. Original main lawn retained.'
s.camera=cameras['west-front'];s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
s.render.resolution_x=1600;s.render.resolution_y=1200;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(O/'west-entry-aligned-v3.blend'))
bpy.ops.object.select_all(action='DESELECT')
for ob in s.objects:
    if ob.type=='MESH' and not ob.hide_render:ob.hide_set(False);ob.select_set(True)
export_visible_glb(filepath=str(O/'west-entry-aligned-v3.glb'),export_apply=True)
raw=(O/'west-entry-aligned-v3.glb').read_bytes()
assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw))
length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
g=json.loads(raw[20:20+length]);assert all('bufferView' in im for im in g.get('images',[]))
exported_ids={n.get('extras',{}).get('feature_id') for n in g['nodes']}
assert {'W_ENTRY','E_ENTRY','WOPEN','WOPEN_S','LAWN','POET_DONKEY'} <= exported_ids
assert not any(n.get('name') in old_names for n in g['nodes'])
report=dict(INFO,source_asset_sha256=sources,protected_objects=len(protected),protected_geometry_unchanged=True,
            path_join=seams,path_surface_samples=path_samples,old_hole_filled=True,new_hole_open=True,
            all_opening_components_and_leaf_skin_translated_once=True,four_urns_share_identical_meshes=True,
            solids=solids,local_bench_clearance=bench_changes,export_bytes=len(raw),embedded_images=len(g.get('images',[])),
            exported_meshes=len(g['meshes']),feature_ids=sorted(f for f in exported_ids if f),renders=[])
(O/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('WEST_ENTRY_GEOMETRY_AND_EXPORT_OK',flush=True)
for key,cam in cameras.items():
    hidden=[]
    if key=='path-join':
        hidden=[ob for ob in s.objects if ob.type=='MESH' and not ob.hide_render and any(token in ob.name.lower() for token in ('leaves','canopy','mound'))]
        for ob in hidden:ob.hide_render=True
    s.camera=cam;s.render.filepath=str(O/('after-'+key+'.png'));bpy.ops.render.render(write_still=True)
    for ob in hidden:ob.hide_render=False
    report['renders'].append(dict(view=key,camera=cam.name,sha256=sha(O/('after-'+key+'.png'))))
    (O/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
bpy.ops.wm.open_mainfile(filepath=str(O/'west-entry-aligned-v3.blend'))
assert all(digest(bpy.data.objects[n])==h for n,h in protected.items())
assert all(sha(Path(p))==h for p,h in sources.items())
report.update(checkpoint_reopened=True,source_unchanged=True,render_complete=True,final_blend_sha256=sha(O/'west-entry-aligned-v3.blend'),final_glb_sha256=sha(O/'west-entry-aligned-v3.glb'))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(O/'west-entry-aligned-v3.glb'))
assert {'W_ENTRY','E_ENTRY','WOPEN','WOPEN_S','LAWN','POET_DONKEY'} <= {o.get('feature_id') for o in bpy.data.objects}
report['glb_reimports']=True
(O/'validation.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print('WEST_ENTRY_FINAL_COMPLETE',flush=True)
