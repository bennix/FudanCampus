"""Whole east garden, photo-constrained v2. Independent checkpoint, no campus writes."""
import ast, bpy, bmesh, math, json, hashlib, random, struct
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/east-garden-v2'; OUT.mkdir(exist_ok=True)
BASE=ROOT/'field-review/guanghua-lawn-survey-v1/model/guanghua-lawn-v1.blend'
IDS={'ETERR','ERAMP','EPATH','ESKY','EOPEN','EOPEN_S'}
protected=[BASE,ROOT/'field-review/guanghua-lawn-shape-v2/guanghua-lawn-shape-v2.blend',ROOT/'field-review/west-garden-terrace-v3/west-garden-terrace-v3.blend']
protected += [ROOT/p for p in json.loads((ROOT/'assets/protected-buildings.json').read_text())['files'] if (ROOT/p).exists()]
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
bpy.ops.wm.open_mainfile(filepath=str(BASE)); s=bpy.context.scene
for o in list(bpy.data.objects):
    if o.get('feature_id') not in IDS and o.type not in {'LIGHT','CAMERA'}: bpy.data.objects.remove(o,do_unlink=True)
for c in bpy.data.collections:c.hide_render=False
M={m.name:m for m in bpy.data.materials}; B={}; ROOTS={}; META={}; current=('EPATH','02')
COL={'02':bpy.data.collections['02_Garden_structures']}
D=json.loads((ROOT/'field-review/guanghua-lawn-survey-v1/survey.json').read_text(encoding='utf-8'))
FEATURES={f['id']:f for f in D['features']}
tree=ast.parse((ROOT/'scripts/build_guanghua_lawn.py').read_text(encoding='utf-8'))
names={'add','box','prism','beam','cyl','blob','curve','edges','ribbon','rail','bench','skylight','flush','mat'}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'<east mesh helpers>','exec'))
def begin(fid,refs=None,note='Photo-constrained form; dimensions and site registration inferred.'):
    global current
    current=(fid,'02');f=FEATURES.get(fid,{})
    META[fid]=dict(feature_id=fid,label=f.get('name',fid),source_photos=refs or f.get('photos',[4518,4523]),existence_confidence='confirmed type; inferred placement',geometry_confidence='inferred',scale_status='provisional metres; not measured',note=note)
def camera(name,loc,target,scale=None,lens=34):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens
    if scale:d.type='ORTHO';d.ortho_scale=scale
    return o
views={
 'overview':camera('EAST overview',(161,-10,91),(90,49,0),91),
 'top':camera('EAST plan',(91,49,120),(91,49,0),105),
 'terrace':camera('EAST terrace',(116,38,20),(92,55,1),32),
 'entry':camera('EAST road entry',(108,53,2.0),(94,54,1.3),None,25),
 'ramp':camera('EAST ramp',(116,11,8),(98,29,0),30),
 'skylight':camera('EAST skylight',(88,39,4.0),(78,48,.5),None,32),
}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True
s.render.resolution_x=1120;s.render.resolution_y=900;s.render.resolution_percentage=100
def render(prefix,keys):
    for k in keys:
        s.camera=views[k];s.render.filepath=str(OUT/f'{prefix}-{k}.png');bpy.ops.render.render(write_still=True)
# Stable surrounding slab in both comparison batches. Lawn itself is excluded.
begin('E_CONTEXT',note='Review crop only. Does not replace or claim registration to the fixed satellite lawn.')
box(91,49,-1.6,42,78,3.2,'turf','ground')
box(112.05,49,-.125,5.1,78,.28,'road','east-road')
box(108,49,.03,3.0,78,.06,'paving','east-sidewalk')
box(73,49,.045,3.4,78,.09,'paving','lawn-edge-walk')
flush()
ground=next(o for o in bpy.data.objects if o.name.startswith('E_CONTEXT__ground'))
ramp_pts=curve([(109,19),(102,21),(97,25),(94,31),(94,39)],8)
left,right=edges(ramp_pts,6.7)
hole_polys=[[(77.4,75.9),(80.6,75.9),(80.6,80.1),(77.4,80.1)],[(76.4,47.4),(79.6,47.4),(79.6,51.6),(76.4,51.6)],left+list(reversed(right))]
for hi,poly in enumerate(hole_polys):
    begin('CUT');prism(poly,-3.3,.5,'dark','cut'+str(hi));flush()
    cutter=next(o for o in bpy.data.objects if o.name.startswith('CUT__cut'+str(hi)))
    bpy.context.view_layer.objects.active=ground;mod=ground.modifiers.new('opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
    bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)
for o in list(bpy.data.objects):
    if o.get('feature_id')=='CUT':bpy.data.objects.remove(o,do_unlink=True)
META.pop('CUT',None);ROOTS.pop('CUT',None)
if not (OUT/'before-overview.png').exists():render('before',['overview','terrace'])
for o in list(bpy.data.objects):
    if o.get('feature_id') in IDS:bpy.data.objects.remove(o,do_unlink=True)
# Portable, generated repeatable material textures. No source photograph is edited.
random.seed(92722);rng=np.random.default_rng(92722)
N=512;yy,xx=np.mgrid[0:N,0:N]/N
def textured(name,color,kind='stone',rough=.82):
    grain=rng.random((N,N));a=.88+.18*(grain-.5)
    if kind=='wood':a=.78+.11*np.sin(2*np.pi*(xx*37+.25*np.sin(yy*6.28)))+.12*(grain-.5)
    if kind=='leaf':a=.74+.30*grain
    if kind=='paver':
        a*=np.where((np.mod(xx*4,1)<.023)|(np.mod(yy*8,1)<.035),.5,1)
    if kind=='stamped':
        # Periodic irregular cells, with a narrow dark impression between them.
        nearest=np.full((N,N),1e9);second=nearest.copy();cell=np.zeros((N,N))
        seeds=rng.random((65,2))
        for i,(cx,cy) in enumerate(seeds):
            dx=np.minimum(abs(xx-cx),1-abs(xx-cx));dy=np.minimum(abs(yy-cy),1-abs(yy-cy));dist=np.sqrt(dx*dx+dy*dy)
            closer=dist<nearest;second=np.where(closer,nearest,np.minimum(second,dist));cell=np.where(closer,i,cell);nearest=np.minimum(nearest,dist)
        a=.86+.028*np.sin(cell*8.27)+.15*(grain-.5)
        a*=np.where(second-nearest<.0025,.34,1)
    px=np.ones((N,N,4),dtype=np.float32);px[:,:,:3]=np.clip(a[:,:,None]*np.array(color)[None,None,:],0,1)
    im=bpy.data.images.new(name+'_basecolor',width=N,height=N);im.pixels.foreach_set(px.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save();im.pack()
    m=mat(name,color,rough);p=m.node_tree.nodes.get('Principled BSDF');t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);return m
for name,color,kind in [
 ('warm-impressed-paving',(.63,.46,.30),'stamped'),('pink-path',(.57,.43,.36),'stamped'),
 ('grey-granite',(.53,.52,.47),'stone'),('warm-granite',(.56,.49,.39),'stone'),('dark-paving',(.23,.25,.24),'paver'),
 ('pale-inlay',(.71,.61,.44),'stone'),('aged-wall',(.62,.60,.51),'stone'),('dark-wood',(.15,.115,.08),'wood'),
 ('seat-orange',(.75,.36,.15),'wood'),('leaf-green',(.22,.34,.075),'leaf'),('leaf-bronze',(.36,.30,.15),'leaf'),
 ('ramp-worn-ochre',(.55,.43,.28),'stone'),('path-grey',(.50,.51,.47),'paver')]:textured(name,color,kind)
mat('metal-green',(.09,.18,.16),.48,.5);mat('soil-east',(.24,.20,.13));mat('joint-dark',(.18,.17,.15))
mat('glass-east',(.43,.57,.57),.17,.26,.82)
def stair(a,b,w,z0,z1,n,part):
    a,b=Vector(a),Vector(b);d=(b-a)/n;u=Vector((-d.y,d.x)).normalized()*w/2
    for i in range(n):
        p=a+d*i;q=p+d;h=z0+(z1-z0)*(i+1)/n
        prism([tuple(p-u),tuple(q-u),tuple(q+u),tuple(p+u)],min(z0-.14,-.02),h,'warm-granite',part)
        prism([tuple(p-u),tuple(q-u),tuple(q+u),tuple(p+u)],h,h+.026,'grey-granite',part+'-tread')
def platform(poly,z,name,material='warm-impressed-paving'):
    prism(poly,-.02,z-.045,'aged-wall',name+'-support');prism(poly,z-.045,z,material,name+'-surface')
def planted_edge(pts,z,height=.42,width=.65,red=False):
    points=curve(pts,8) if len(pts)>2 else pts
    ribbon(points,width,-.02,z+height,'warm-granite','planter-wall')
    ribbon(points,width+.05,z+height,z+height+.06,'grey-granite','planter-coping')
    ribbon(points,width*.84,z+height+.06,z+height+.11,'soil-east','planter-soil')
    for a,b in zip(points,points[1:]):
        a,b=Vector(a),Vector(b);count=max(1,math.ceil((b-a).length/.48))
        for k in range(count):
            p=a+(b-a)*k/count
            blob(p.x,p.y,z+height+.43+random.uniform(-.04,.05),width*.64,.42,.42,'leaf-bronze' if red else 'leaf-green','planted-shrubs',8,5)
# ETERR: three rising flights from east road, and an upper short flight visible in 4564.
begin('ETERR',[4556,4559,4562,4564,4566,4568], 'Three road-to-upper flights; west exit meets locally raised garden path. Counts/heights remain inferred.')
stair((106.5,53.5),(104.34,53.5),5.6,.06,.84,6,'road-flight')
platform([(104.34,50.7),(104.34,56.3),(98.8,56.3),(98.8,50.7)],.866,'lower-landing','dark-paving')
for x in [99.6,101.2,102.8]:
    for y in [51.6,53.2,54.8]:box(x,y,.875,.48,.48,.018,'pale-inlay','square-inlay')
stair((98.8,53.5),(96.64,53.5),3.1,.866,1.646,6,'middle-flight')
platform([(96.64,50.2),(96.64,59.1),(95,61),(91,61),(91,50.2)],1.672,'middle-landing')
stair((91,54.3),(89.95,54.3),4.4,1.672,2.092,3,'upper-short-flight')
upper=[(89.95,51.7),(89.95,60.8),(88.7,62),(86.2,62),(84.8,60.5),(84.8,53.5),(86,51.7)]
platform(upper,2.118,'upper-landing')
# Westward exit: local mound supports the path, avoiding a fictional tall flight.
stair((83.75,55.7),(84.8,55.7),1.8,1.672,2.092,3,'garden-exit-flight')
planted_edge([(104.2,50.3),(101.8,49.6),(99.3,50.1)],.866,.35,1.1)
planted_edge([(104.2,56.8),(103,58),(100.3,58.3),(99.1,56.8)],.866,.35,1.1)
planted_edge([(98.45,50.0),(96,48.8),(91,48.8),(88.3,50.0)],1.672,.80,1.1,True)
planted_edge([(96.3,59.6),(94.6,61.5),(91.5,61.7)],1.672,.36,.75)
planted_edge([(89.4,61.7),(87.7,62.7),(85.5,61.9),(84.3,59.7),(84.3,57.0)],2.118,.35,.75,True)
planted_edge([(84.3,54.4),(84.6,52.3),(86.3,51.0),(89.3,51.0)],2.118,.35,.75,True)
# Lower planting terraces by the visible outer wall.
planted_edge([(103,47.7),(98,46.8),(93,46.9),(89,48.3)],.20,.35,1.5)
planted_edge([(101,48.5),(97,47.8),(92.5,47.9)],.80,.3,1.1)
for x,y,z,a in [(93.7,59.7,1.672,0),(87.3,61.2,2.118,0),(85.7,58.9,2.118,90)]:bench(x,y,z,a,2.1)
# EPATH replaces all old crossing geometry, with separate connections to lawn edge.
begin('EPATH', [4496,4507,4513,4572,4574,4578,4582,4584,4585], 'Paths detour around ESKY/EOPEN_S. Route curvature, widths and northern layout provisional.')
route=curve([(73,85.5),(85,83),(89.8,74),(87.6,66.5),(79.8,61),(80.7,55),(82,53),(83,46),(85,39),(81,33),(83.7,25),(92,18),(106.5,15.5)],8)
ribbon(route,1.65,.025,.095,'pink-path','main-curve')
for pts in [[(81,33),(78,29),(73,27)],[(83.2,42),(79.8,39.5),(76,39),(73,40)],[(83,66),(78,67),(73,68)]]:
    pts[0]=min(route,key=lambda p:(Vector(p)-Vector(pts[0])).length)
    ribbon(curve(pts,8),1.5,.026,.097,'pink-path','lawn-connection')
# A graded short branch meets the west steps. Height is explicitly a terrain hypothesis.
branch_start=min(route,key=lambda p:(Vector(p)-Vector((79.8,61))).length)
branch=curve([branch_start,(82.4,60.1),(83.1,57.9),(83.75,55.7)],7)
bl,br=edges(branch,1.8)
for i in range(len(branch)-1):
    z0=.095+1.603*i/(len(branch)-1);z1=.095+1.603*(i+1)/(len(branch)-1)
    v=[(*bl[i],z0),(*br[i],z0),(*br[i+1],z1),(*bl[i+1],z1)]
    verts=[(x,y,z-.13) for x,y,z in v]+v
    add(verts,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'pink-path','raised-west-branch')
    # Graded shoulder cross-sections sit below the branch rather than intersect it.
    profiles=[]
    for j,z in [(i,z0),(i+1,z1)]:
        c=Vector(branch[j]);l=Vector(bl[j]);r=Vector(br[j]);u=(l-r).normalized()
        profiles.append([(*(c+u*1.25),.006),(*l,max(.007,z-.13)),(*r,max(.007,z-.13)),(*(c-u*1.25),.006)])
    for k in range(3):
        top=[profiles[0][k],profiles[0][k+1],profiles[1][k+1],profiles[1][k]]
        add([(x,y,-.05) for x,y,z in top]+top,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'turf','graded-shoulder')
begin('E_PLANTING',[4499,4500,4525,4532,4579,4582], 'Vegetation masses and tree locations are approximate; hidden crowns omitted in structure views.')
for x,y in [(88,68),(86,73),(87,78),(78,36),(88,25),(90,20),(80,70)]:
    cyl(x,y,0,.11,.7,'trunk');blob(x,y,1.05,.85,.8,.85,'leaf-green','clipped-shrub',12,7)
# ESKY corrected away from path, beside EOPEN_S, low louvred plinth + four-sided roof.
begin('ESKY',[4505,4568,4574,4577], 'One skylight only, directly south of EOPEN_S; low base, full louvred sides.')
x,y=78,44.95;size=3.45
box(x,y,.16,3.72,3.72,.32,'warm-granite','plinth')
box(x,y,.47,3.45,3.45,.36,'metal-green','louvre-dark-back')
for z in [.36,.47,.58,.69]:
    for sign in [-1,1]:
        box(x,y+sign*size/2,z,size,.09,.055,'metal-green','louvres')
        box(x+sign*size/2,y,z,.09,size,.055,'metal-green','louvres')
v=[(x-size/2,y-size/2,.76),(x+size/2,y-size/2,.76),(x+size/2,y+size/2,.76),(x-size/2,y+size/2,.76),(x,y,1.5)]
add(v,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(3,2,1,0)],'glass-east','glass-roof')
for i in range(4):beam(v[i],v[4],.045,'metal-green','roof-frame');beam(v[i],v[(i+1)%4],.055,'metal-green','roof-frame')
planted_edge([(75.9,43),(80.1,43),(80.1,46.8)],.02,.08,.65)
# Two distinct stair openings; three-sided metal rail with intermediate uprights.
for fid,x,y in [('EOPEN',79,78),('EOPEN_S',78,49.5)]:
    begin(fid, [4492,4493] if fid=='EOPEN' else [4505,4506,4574,4577], 'Opening location inherited; entry direction and hidden depth unresolved. No underground extension.')
    for xx0 in [x-1.75,x+1.75]:box(xx0,y,-.64,.30,4.5,1.6,'aged-wall','opening-wall')
    box(x,y+2.25,-.64,3.2,.30,1.6,'aged-wall','opening-end')
    stair((x,y-2.1),(x,y+2.1),2.9,-1.5,.07,12,'descending-steps')
    rail([(x-1.82,y-2.1),(x-1.82,y+2.4),(x+1.82,y+2.4),(x+1.82,y-2.1)],.16,1.0,'metal-green')
    for side in [-1,1]:
        for i in range(1,7):beam((x+side*1.82,y-2.1+i*.64,.16),(x+side*1.82,y-2.1+i*.64,1.15),.04,'metal-green','rail-infill')
        beam((x+side*1.30,y-2.0,-.5),(x+side*1.30,y+2.0,1.0),.045,'silver','descending-handrail')
    planted_edge([(x-2.35,y-2.1),(x-2.35,y+2.9),(x+2.35,y+2.9),(x+2.35,y-1.5)],.01,.03,.60)
    for j in range(4):box(x-2.25-j*.6,y-2.7,.055,.45,1.05,.11,'grey-granite','access-slabs')
    box(x,y-2.09,-1.3,3.15,.045,.4,'joint-dark','occlusion-limit')
# ERAMP: continuous sloped deck and vertical retaining walls with level coping.
begin('ERAMP',[4534,4539,4540,4547,4550], 'Continuous curved surface, level wall tops and pergola; slope and spans inferred; terminates at photographed visibility limit.')
zs=[.03-2.2*i/(len(ramp_pts)-1) for i in range(len(ramp_pts))]
for i in range(len(ramp_pts)-1):
    v=[(*left[i],zs[i]),(*right[i],zs[i]),(*right[i+1],zs[i+1]),(*left[i+1],zs[i+1])]
    add([(x,y,z-.16) for x,y,z in v]+v,[(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'ramp-worn-ochre','sloped-deck')
for side in [left,right]:
    for i in range(len(side)-1):
        a,b=Vector(side[i]),Vector(side[i+1]);n=Vector((-(b-a).y,(b-a).x)).normalized()*.16
        prism([tuple(a-n),tuple(b-n),tuple(b+n),tuple(a+n)],min(zs[i],zs[i+1])-.1,1.05,'aged-wall','retaining-wall')
        beam((*a,1.1),(*b,1.1),.34,'grey-granite','wall-coping',.10)
        aa=Vector(ramp_pts[i])+(a-Vector(ramp_pts[i]))*.91;bb=Vector(ramp_pts[i+1])+(b-Vector(ramp_pts[i+1]))*.91
        beam((*aa,zs[i]+.018),(*bb,zs[i+1]+.018),.10,'yellow','edge-line',.015)
    for i in range(2,len(side)-1,5):
        x,y=side[i];box(x,y,.64,.11,.09,.20,'yellow','wall-reflector')
    for i in range(2,len(side),5):
        x,y=side[i];box(x,y,2.04,.24,.24,1.92,'dark-wood','pergola-post')
    for a,b in zip(side[1:],side[2:]):beam((*a,3.02),(*b,3.02),.24,'dark-wood','pergola-long-beam',.30)
for i in range(1,len(ramp_pts)):
    a,b=Vector(left[i]),Vector(right[i]);u=(b-a).normalized()*.35
    beam((*(a-u),3.25),(*(b+u),3.25),.14,'dark-wood','pergola-slats',.22)
for i in range(2,len(ramp_pts),5):beam((*left[i],3.04),(*right[i],3.04),.23,'dark-wood','pergola-cross-beam',.28)
# Short transverse water grate at mouth; no imaginary basement facade.
beam((*left[1],zs[1]+.02),(*right[1],zs[1]+.02),.23,'joint-dark','mouth-drain',.04)
for i in range(4,len(ramp_pts)-1,2):
    for side in [left,right]:
        x,y=side[i];blob(x,y,3.47,.8,.85,.30,'leaf-green','pergola-vines',10,6)
        for j in range(4):
            blob(x+random.uniform(-.65,.65),y+random.uniform(-.65,.65),3.50+random.uniform(-.08,.18),.28,.30,.20,'leaf-green','vine-leaf-clusters',8,5)
        for j in range(2):blob(x+random.uniform(-.3,.3),y+random.uniform(-.4,.4),3.06-j*.30,.18,.2,.32,'leaf-green','hanging-vines',8,5)
# Ring bench and adjacent sitting apron, explicit reference 4547.
begin('E_FURNITURE',[4544,4547,4548,4564], 'Ring bench form confirmed; tree and seat placements are approximate.')
platform([(99,30),(106.5,30),(106.5,44),(100,44),(99,40)],.07,'road-sitting-apron','path-grey')
cx,cy=103.2,36.8
for i in range(72):
    a=i*2*math.pi/72;b=(i+.88)*2*math.pi/72
    poly=[(cx+r*math.cos(t),cy+r*math.sin(t)) for r,t in [(1.08,a),(1.72,a),(1.72,b),(1.08,b)]]
    prism(poly,.47,.53,'dark-wood','ring-seat')
    beam((cx+1.05*math.cos(a),cy+1.05*math.sin(a),.53),(cx+1.05*math.cos(a),cy+1.05*math.sin(a),1.06),.072,'dark-wood','ring-back',.055)
for i in range(8):
    t=i*math.pi/4;box(cx+1.45*math.cos(t),cy+1.45*math.sin(t),.26,.075,.075,.42,'metal-green','ring-legs')
bench(103,42,.07,0,2.2)
flush()
# Recolor helpers' bench materials with shared editable assignments.
for o in bpy.data.objects:
    if o.type!='MESH':continue
    for i,m in enumerate(o.data.materials):
        if m.name=='benchwood':o.data.materials[i]=M['seat-orange']
        elif m.name=='rail':o.data.materials[i]=M['metal-green']
        elif o.get('feature_id')=='E_CONTEXT' and m.name=='paving':o.data.materials[i]=M['path-grey']
    # Ensure consistently oriented solids, including sloping path/deck strips.
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
    uv=o.data.uv_layers.new(name='EAST_surface')
    for p in o.data.polygons:
        axis=max(range(3),key=lambda k:abs(p.normal[k]));u=Vector((0,1,0) if axis==0 else (1,0,0));v=p.normal.cross(u).normalized()
        name=o.data.materials[p.material_index].name
        scale=.30 if 'impressed' in name or 'pink-path' in name else .5 if 'paving' in name or 'path-grey' in name else 1.6
        for li in p.loop_indices:
            co=o.data.vertices[o.data.loops[li].vertex_index].co;uv.data[li].uv=(co.dot(u)*scale,co.dot(v)*scale)
    o['texture_status']='Generated approximate material pattern; not surveyed or photo-projected'
# Sparse, optional trees for the photographed shaded-garden context.
begin('E_TREES',[4500,4516,4525,4547,4569,4574,4582], 'Approximate tree silhouettes only; no species/count/position claim.')
tree_positions=[]
def path_distance(x,y):
    p=Vector((x,y));dist=float('inf')
    for a,b in zip(route,route[1:]):
        a,b=Vector(a),Vector(b);d=b-a;t=max(0,min(1,(p-a).dot(d)/d.length_squared));dist=min(dist,(p-a-d*t).length)
    return dist
for x,y,h in [(103.2,36.8,8),(105,64,8),(98,73,7),(87,35,6),(76,42,5),(77.5,57.5,5),(92,81,7),(87,20,7),(101,15,8)]:
    # Context trees are movable proxies: never place a trunk on the main walk.
    while path_distance(x,y)<1.3:x-=2.0
    tree_positions.append([x,y,h,path_distance(x,y)])
    cyl(x,y,.02,.20,h*.57,'trunk',.09,12,'trunk')
    for j in range(5):
        t=j*2.4;end=(x+math.cos(t)*1.6,y+math.sin(t)*1.6,h*.76)
        beam((x,y,h*.42),end,.10,'trunk','branches')
        blob(end[0],end[1],h*.82,1.9,1.7,h*.19,'leaf'+str(j%4),'canopy',10,6)
flush()
tree_objects=[o for o in bpy.data.objects if o.get('feature_id')=='E_TREES']
for o in tree_objects:o.hide_render='canopy' in o.name
for o in bpy.data.objects:
    if o.type=='MESH' and any(k in o.name for k in ['shrubs','vines','leaf-clusters','clipped-shrub','canopy']):
        for p in o.data.polygons:p.use_smooth=True
s['scope']='Whole east garden, 6 fixed location IDs + review context. Not integrated into campus.'
s['uncertainty']='Inherited provisional site frame; no metric registration to satellite lawn. Terrace terrain, hidden stair depth, route curvature and vegetation inferred.'
s.camera=views['overview']
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        r=area.spaces.active.region_3d;r.view_location=(91,49,0);r.view_distance=70;r.view_rotation=views['overview'].rotation_euler.to_quaternion()
checkpoint=OUT/'east-garden-v2.blend';bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
render('after',['overview','top','terrace','ramp','skylight','entry'])
for o in tree_objects:o.hide_render=False
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
    if o.type in {'MESH','EMPTY'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'east-garden-v2.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
checks=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data)
    checks.append(dict(object=o.name,nonmanifold=sum(not e.is_manifold for e in bm.edges),volume=bm.calc_volume(signed=True),finite=all(math.isfinite(c) for v in o.data.vertices for c in v.co)));bm.free()
bad=[c for c in checks if c['nonmanifold'] or c['volume']<=0 or not c['finite']]
assert not bad,bad
assert IDS <= {o.get('feature_id') for o in bpy.data.objects}
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
raw=(OUT/'east-garden-v2.glb').read_bytes();magic,version,length=struct.unpack_from('<4sII',raw);assert (magic,version,length)==(b'glTF',2,len(raw))
n,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);assert all('bufferView' in im for im in g['images'])
assert IDS <= {node.get('extras',{}).get('feature_id') for node in g['nodes']}
report=dict(checkpoint_reopens=True,baselines_unchanged=hashes,closed_positive_meshes=len(checks),feature_ids=sorted(IDS),embedded_images=len(g['images']),glb_bytes=len(raw),meshes=checks,tree_centres_and_main_path_clearance=tree_positions,limitations=['not measured','not registered to satellite lawn','no exhaustive self-intersection check','west terrace grading and underground depth inferred'])
(OUT/'component-evidence.json').write_text(json.dumps(META,ensure_ascii=False,indent=2),encoding='utf-8')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'east-garden-v2.glb'));assert IDS <= {o.get('feature_id') for o in bpy.data.objects};report['glb_imports']=True
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('EAST_GARDEN_COMPLETE',len(checks),'meshes',len(raw),'bytes')

