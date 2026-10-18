"""WTERR entrance topology study. Never replaces accepted site or lawn assets."""
import ast, bpy, bmesh, math, json, hashlib, struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/west-garden-terrace-v2'
OUT.mkdir(exist_ok=True)
BASE=ROOT/'field-review/guanghua-lawn-survey-v1/model/guanghua-lawn-v1.blend'
protected=[BASE,ROOT/'field-review/guanghua-lawn-shape-v2/guanghua-lawn-shape-v2.blend']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
bpy.ops.wm.open_mainfile(filepath=str(BASE))
s=bpy.context.scene
# Preserve WTERR only: other locations are independent studies and not integrated here.
for o in list(bpy.data.objects):
    if o.get('feature_id')!='WTERR' and o.type not in {'CAMERA','LIGHT'}:
        bpy.data.objects.remove(o,do_unlink=True)
for c in bpy.data.collections: c.hide_render=False
COL={'02':bpy.data.collections['02_Garden_structures']}
M={m.name:m for m in bpy.data.materials}
B={}; ROOTS={'WTERR':next(o for o in bpy.data.objects if o.type=='EMPTY' and o.get('feature_id')=='WTERR')}
META={'WTERR':dict(feature_id='WTERR',label='西花园高台',source_photos=[4366,4368,4375,4377,4378,4380,4384,4395],existence_confidence='confirmed',geometry_confidence='inferred',scale_status='provisional; not measured',note='Entrance topology revision; retained overall footprint and skylight positions remain provisional.')}
current=('WTERR','02')
# Reuse pure mesh helpers without executing the original scene builder.
tree=ast.parse((ROOT/'scripts/build_guanghua_lawn.py').read_text(encoding='utf-8'))
names={'add','box','prism','beam','stair','rail','flush','curve','edges','ribbon','hedge'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<mesh helpers>','exec'))
def stair(a,b,w,z0,z1,n=6):
    a,b=Vector(a),Vector(b);d=(b-a)/n;u=Vector((-d.y,d.x)).normalized()*w/2
    for i in range(n):
        p=a+d*i;q=p+d
        prism([tuple(p-u),tuple(q-u),tuple(q+u),tuple(p+u)],-.02,z0+(z1-z0)*(i+1)/n,'pale','steps')
def cam(name,loc,target,scale=None):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    d.lens=30
    if scale:d.type='ORTHO';d.ortho_scale=scale
    return o
views={
 'overview':cam('WTERR overview',(-24,24,28),(-61,56,0),43),
 'top':cam('WTERR orthographic',(-61,57,65),(-61,57,0),42),
 'entry':cam('WTERR entrance photo 4368',(-49.5,40.3,2.2),(-50.5,50.5,1.0)),
}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100
# Identical review pad and lighting for both comparison batches.
me=bpy.data.meshes.new('review-ground');me.from_pydata([(-79,38,-.025),(-42,38,-.025),(-42,75,-.025),(-79,75,-.025)],[],[(0,1,2,3)]);me.materials.append(M['turf'])
pad=bpy.data.objects.new('REVIEW_ONLY_ground',me);s.collection.objects.link(pad)
def render(prefix,keys):
    for key in keys:
        s.camera=views[key];s.render.filepath=str(OUT/f'{prefix}-{key}.png');bpy.ops.render.render(write_still=True)
render('before',['overview','top'])
# Replace only the entrance-bearing shell and rail sections, retaining double skylights.
parts={'raised-platform','stone-platform','steps','stair-landing','stair-rail','stair-rail-cross','rail-post','rail-bar','rail-cross','paving-bands'}
for o in list(bpy.data.objects):
    if o.get('feature_id')=='WTERR' and any(o.name.startswith('WTERR__'+p+'__') for p in parts):bpy.data.objects.remove(o,do_unlink=True)
# Provisional east recess expanded to accommodate the evidenced adjacent low/high paths.
poly=[(-74,43),(-54,43),(-54,55.5),(-51,55.5),(-51,71),(-74,71)]
prism(poly,-.02,1.20,'concrete','raised-platform')
prism(poly,1.20,1.23,'stone','stone-platform')
# Three low steps, long walk, three low steps, turning landing, five return steps.
# 4368 confirms the two short flights; 4375/4377 establish the adjacent upper flight.
stair((-49.5,44),(-49.5,45.05),2.2,0,.42,3)
box(-49.5,47.55,.20,2.2,5,.44,'pale','low-walk') # top .42, bottom -.02
stair((-49.5,50.05),(-49.5,51.1),2.2,.42,.75,3)
box(-50.9,52.2,.365,5,2.2,.77,'pale','turn-landing') # top .75
stair((-52.3,51.1),(-52.3,49.35),2.2,.75,1.23,5)
box(-52.6,48.25,.605,2.8,2.2,1.25,'stone','upper-entry') # joins x=-54
# Low planted retaining edges frame the approach; no invented handrails along low flight.
box(-47.95,47.55,.44,.9,7.1,.90,'concrete','approach-planter')
box(-47.95,47.55,.93,1.0,7.1,.08,'pale','approach-coping')
hedge([(-47.95,44),(-47.95,51.1)],.78,.97,.5)
box(-51.05,47.55,.525,.5,7.1,1.09,'concrete','central-retaining-wall')
box(-51.05,47.55,1.11,.58,7.1,.08,'pale','central-coping')
# Recess-side walls support the upper rail, with the upper entrance left open.
box(-53.85,52.425,.59,.3,6.15,1.28,'concrete','recess-wall')
# Rails follow platform edges and leave a 2.2 m opening at y=47.15..49.35.
rail([(-74,43),(-54,43),(-54,47.15)],1.23,cross=True,m='wood')
rail([(-54,49.35),(-54,55.5),(-51,55.5),(-51,71),(-74,71)],1.23,cross=True,m='wood')
rail([(-53.4,53.3),(-48.4,53.3),(-48.4,51.1)],.75,cross=True,m='wood')
for x in [-53.4,-51.2]:
    a=(x,51.1,.75);b=(x,49.35,1.23)
    for p in [a,b]:beam(p,(p[0],p[1],p[2]+1.05),.12,'wood','upper-stair-post')
    for dz in [.2,1.05]:beam((a[0],a[1],a[2]+dz),(b[0],b[1],b[2]+dz),.10,'wood','upper-stair-bar')
    beam((a[0],a[1],a[2]+.2),(b[0],b[1],b[2]+.93),.09,'wood','upper-stair-cross')
    beam((a[0],a[1],a[2]+.93),(b[0],b[1],b[2]+.2),.09,'wood','upper-stair-cross')
# Retain prior paving-band convention, clipped to the revised footprint.
for y in [44,47.7,54.3,58,61.5,69.5]:
    right=-54.2 if y<55.5 else -51.2
    box((-73.8+right)/2,y,1.245,right+73.8,.1,.015,'joint','paving-bands')
for x in [-71,-67,-59,-55]:box(x,57,1.247,.1,27,.015,'joint','paving-bands')
flush()
for o in bpy.data.objects:
    if o.get('feature_id')=='WTERR':
        for k,v in META['WTERR'].items():o[k]=v
s['scope']='WTERR entrance study only; not registered to satellite-fixed LAWN'
s['uncertainty']='Full footprint, heights, step dimensions, compass registration and hidden west edge remain inferred.'
s.camera=views['overview']
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        r=area.spaces.active.region_3d;r.view_location=(-60,56,0);r.view_distance=38;r.view_rotation=views['overview'].rotation_euler.to_quaternion()
checkpoint=OUT/'west-garden-terrace-v2.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
render('after',['overview','top','entry'])
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.get('feature_id')=='WTERR':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'west-garden-terrace-v2.glb'),export_format='GLB',use_selection=True,export_extras=True)
# Reopen checkpoint and validate changed solids and baseline preservation.
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
checks=[]
for o in bpy.data.objects:
    if o.type!='MESH' or o.get('feature_id')!='WTERR':continue
    assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
    bm=bmesh.new();bm.from_mesh(o.data)
    checks.append({'object':o.name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True)})
    bm.free()
assert all(c['nonmanifold_edges']==0 and c['signed_volume']>0 for c in checks)
for p,h in hashes.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h
raw=(OUT/'west-garden-terrace-v2.glb').read_bytes();magic,ver,length=struct.unpack_from('<4sII',raw);assert (magic,ver,length)==(b'glTF',2,len(raw))
n,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);assert any(x.get('extras',{}).get('feature_id')=='WTERR' for x in g['nodes'])
report={'checkpoint_reopens':True,'baselines_unchanged':hashes,'glb_parses':True,'WTERR_id_retained':True,'meshes':checks,'not_claimed':['survey accuracy','full garden integration','exhaustive self-intersection checks','resolved entire terrace footprint'],'connections':{'lower_walk_z':.42,'turn_z':.75,'upper_z':1.23,'flights':[3,3,5],'status':'counts read from visible photos; dimensions inferred'}}
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'west-garden-terrace-v2.glb'))
assert any(o.type=='MESH' and o.get('feature_id')=='WTERR' for o in bpy.data.objects)
report['glb_imports_in_blender']=True
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('WTERR_REFINEMENT_COMPLETE',str(OUT))
