"""Photo-guided WTERR v3: bounded skylight correction and portable textured materials."""
import bpy,bmesh,ast,math,json,hashlib,random,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'field-review/west-garden-terrace-v3';OUT.mkdir(exist_ok=True)
BASE=ROOT/'field-review/west-garden-terrace-v2/west-garden-terrace-v2.blend'
protected=[BASE,ROOT/'field-review/guanghua-lawn-shape-v2/guanghua-lawn-shape-v2.blend']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
random.seed(92703);rng=np.random.default_rng(92703)
M={m.name:m for m in bpy.data.materials};B={};current=('WTERR','02')
COL={'02':bpy.data.collections['02_Garden_structures']};ROOTS={'WTERR':next(o for o in bpy.data.objects if o.type=='EMPTY' and o.get('feature_id')=='WTERR')}
META={'WTERR':dict(feature_id='WTERR',label='西花园高台',source_photos=[4368,4377,4378,4380,4384,4390,4395],geometry_confidence='inferred photo proportions',material_confidence='photo-guided approximate palette; generated grain and stone arrangement')}
tree=ast.parse((ROOT/'scripts/build_guanghua_lawn.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'add','box','prism','beam','blob','flush'}],type_ignores=[]),'<helpers>','exec'))
def camera(name,loc,target,lens=32):
 d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;return o
views={'overview':bpy.data.objects['WTERR overview'],'entry':bpy.data.objects['WTERR entrance photo 4368'],'platform':camera('WTERR material photo 4380',(-54.8,57,2.95),(-66.5,57,2.05),23)}
s.cycles.samples=24;s.render.resolution_x=1200;s.render.resolution_y=900
def render(prefix,keys):
 for k in keys:s.camera=views[k];s.render.filepath=str(OUT/f'{prefix}-{k}.png');bpy.ops.render.render(write_still=True)
if not (OUT/'before-platform.png').exists():render('before',['overview','platform'])
# Confirmed relation: roof base behind planting; dimensions still inferred.
for o in bpy.data.objects:
 if o.get('feature_id')!='WTERR' or o.type!='MESH':continue
 if any(t in o.name for t in ['skylight-glass','skylight-frame']):
  for v in o.data.vertices:v.co.z=1.95+(v.co.z-2.47)*.85
 elif 'skylight-base' in o.name:
  for v in o.data.vertices:v.co.z=1.51+(v.co.z-1.51)*.24
 elif 'vent-louvre' in o.name:
  for v in o.data.vertices:v.co.z=1.65+(v.co.z-2.13)*.8
# Tileable, deterministic surface maps. These are material assets, not edited photos.
def texture(name,kind):
 n=512;y,x=np.mgrid[0:n,0:n]/n;fine=rng.random((n,n));coarse=np.zeros((n,n))
 for i in range(1,14):
  k,l=rng.integers(-9,10,size=2);coarse+=np.sin(2*np.pi*(x*k+y*l)+rng.uniform(0,6.28))*.17
 if kind=='wood':a=.50+.11*np.sin(2*np.pi*(x*39+.18*np.sin(y*2*np.pi)))+.06*np.sin(x*2*np.pi*103)+.10*coarse+.08*(fine-.5)
 elif kind=='leaf':a=.83+.09*coarse+.24*(fine-.5)
 else:a=.88+.013*coarse+.22*(fine-.5)
 if kind=='paver':a*=np.where((x<.010)|(y<.010),.48,1)
 a=np.clip(a,.14,.98);rgba=np.ones((n,n,4),dtype=np.float32);rgba[:,:,:3]=a[:,:,None]
 im=bpy.data.images.new(name,width=n,height=n);im.pixels.foreach_set(rgba.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save();im.pack();return im
maps={k:texture('WTERR_'+k,k) for k in ['stone','wood','leaf','paver']}
def material(name,color,rough=.75,kind='stone',metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;m.diffuse_color=(*color,1)
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 # Store tint directly in image so standard glTF needs no unsupported node math.
 src=maps[kind];px=np.empty(512*512*4,dtype=np.float32);src.pixels.foreach_get(px);px=px.reshape((-1,4));px[:,:3]*=np.array(color)[None,:]
 im=bpy.data.images.new(name+'_basecolor',width=512,height=512);im.pixels.foreach_set(px.ravel());im.filepath_raw=str(OUT/(name+'.png'));im.file_format='PNG';im.save();im.pack()
 t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=im;m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
 M[name]=m;return m
palette=[(.42,.44,.44),(.52,.53,.52),(.34,.36,.37),(.59,.58,.54),(.57,.49,.46),(.40,.41,.42),(.64,.62,.58),(.46,.43,.43)]
for i,c in enumerate(palette):material('stone-chip-'+str(i),c,.82)
material('granite-grey',(.55,.56,.54),.76);material('granite-warm',(.54,.46,.37),.87)
material('charcoal-band',(.23,.25,.25),.79);material('aged-timber',(.17,.135,.10),.73,'wood')
material('seat-timber',(.82,.44,.23),.64,'wood');material('hedge-green',(.34,.47,.12),.93,'leaf')
material('hedge-burgundy',(.40,.22,.25),.95,'leaf');material('aged-render',(.64,.59,.51),.92)
material('walkway-pavers',(.53,.54,.52),.78,'paver')
def assign(o,key):o.data.materials.clear();o.data.materials.append(M[key])
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('feature_id')!='WTERR':continue
 n=o.name
 if n.endswith('__wood'):assign(o,'aged-timber')
 elif 'benchwood' in n:assign(o,'seat-timber')
 elif 'paving-bands' in n:assign(o,'charcoal-band')
 elif 'hedge__redhedge' in n:assign(o,'hedge-burgundy')
 elif 'hedge__hedge' in n:assign(o,'hedge-green')
 elif any(t in n for t in ['low-walk','turn-landing']):assign(o,'walkway-pavers')
 elif any(t in n for t in ['coping','skylight-planter','steps']):assign(o,'granite-grey')
 elif any(t in n for t in ['raised-platform','retaining-wall','recess-wall','approach-planter']):assign(o,'aged-render')
 elif any(t in n for t in ['stone-platform','upper-entry']):assign(o,'charcoal-band')
 if 'steps' in n:
  o.data.materials.append(M['granite-warm'])
  for p in o.data.polygons:
   if p.normal.z<.5:p.material_index=1
 if 'paving-bands' in n:
  for start in range(0,len(o.data.vertices),8):
   vv=list(o.data.vertices)[start:start+8];lo=[min(v.co[k] for v in vv) for k in range(2)];hi=[max(v.co[k] for v in vv) for k in range(2)];axis=min(range(2),key=lambda k:hi[k]-lo[k]);mid=(hi[axis]+lo[axis])/2
   for v in vv:v.co[axis]=mid+(v.co[axis]-mid)*2.2
# Glass tint, reflections and transmission are supported by glTF extension.
g=M['glass'];p=g.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.69,.82,.78,1);p.inputs['Alpha'].default_value=1;p.inputs['Roughness'].default_value=.14;p.inputs['Metallic'].default_value=0;p.inputs['Transmission Weight'].default_value=.72;p.inputs['IOR'].default_value=1.46;g.diffuse_color=(.69,.82,.78,1)
# Irregular stone field made of convex closed prisms; grayscale/pink palette from 4378/4380.
def clip(poly,a,b,c):
 out=[]
 for P,Q in zip(poly,poly[1:]+poly[:1]):
  d=a*P[0]+b*P[1]-c;e=a*Q[0]+b*Q[1]-c
  if d<=0:out.append(P)
  if (d<=0)!=(e<=0):t=d/(d-e);out.append((P[0]+t*(Q[0]-P[0]),P[1]+t*(Q[1]-P[1])))
 return out
def subtract_rect(poly,r):
 # Disjoint outside fragments; discard the interior flower-bed area.
 x0,y0,x1,y1=r;remain=poly;out=[]
 for a,b,c in [(-1,0,-x0),(1,0,x1),(0,-1,-y0),(0,1,y1)]:
  if not remain:break
  q=clip(remain,-a,-b,-c)
  if len(q)>=3:out.append(q)
  remain=clip(remain,a,b,c)
 return out
seeds={(i,j):(i*.65+random.uniform(-.22,.22),j*.65+random.uniform(-.22,.22)) for i in range(-118,-73) for j in range(62,113)}
count=0
for (i,j),(x,y) in seeds.items():
 if not(-74.7<x<-50.3 and 42.3<y<71.7):continue
 poly=[(x-1,y-1),(x+1,y-1),(x+1,y+1),(x-1,y+1)]
 for di in range(-2,3):
  for dj in range(-2,3):
   if (di,dj)==(0,0) or (i+di,j+dj) not in seeds:continue
   xx,yy=seeds[i+di,j+dj];poly=clip(poly,xx-x,yy-y,((xx*xx+yy*yy)-(x*x+y*y))/2)
 for bounds in [(-73.92,43.08,-54.02,70.92),(-54.02,55.52,-51.08,70.92)]:
  q=poly
  for a,b,c in [(-1,0,-bounds[0]),(1,0,bounds[2]),(0,-1,-bounds[1]),(0,1,bounds[3])]:q=clip(q,a,b,c) if q else []
  fragments=[q] if len(q)>2 else []
  for r in [(-66.27,46.73,-59.73,53.27),(-66.27,60.73,-59.73,67.27)]:fragments=[s for f in fragments for s in subtract_rect(f,r)]
  divided=[]
  for f in fragments:
   if random.random()<.38:
    a,b=random.choice([(1,0),(0,1),(1,.65)]);c=sum(a*v[0]+b*v[1] for v in f)/len(f)
    divided.extend([clip(f,a,b,c),clip(f,-a,-b,-c)])
   else:divided.append(f)
  for f in divided:
   cx=sum(v[0] for v in f)/len(f);cy=sum(v[1] for v in f)/len(f)
   f=[(cx+(a-cx)*.967,cy+(b-cy)*.967) for a,b in f]
   if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(f,f[1:]+f[:1])))<.005:continue
   prism(f,1.231,1.249,'stone-chip-'+str(random.randrange(len(palette))),'irregular-paving');count+=1
# Flower-bed coping in stone blocks, instead of a single smooth pale slab.
for cy in [50,64]:
 for side in [-1,1]:
  for j in range(8):
   t=-2.84+j*.81
   box(-63+t,cy+side*3.18,1.55,.795,.23,.08,'granite-grey','planter-coping')
   box(-63+side*3.18,cy+t,1.55,.23,.795,.08,'granite-grey','planter-coping')
# Small leaf masses break the ruler-straight hedge edge without claiming exact plants.
for cy in [50,64]:
 for side in [-1,1]:
  for j in range(30):
   t=-2.85+j*5.7/29
   for x,y in [(-63+t,cy+side*2.9),(-63+side*2.9,cy+t)]:
    blob(x+random.uniform(-.12,.12),y+random.uniform(-.12,.12),2.1+random.uniform(-.04,.05),.23,.22,.14,'hedge-green','hedge-leaf-masses',8,4)
for j in range(100):blob(-73+random.uniform(-.45,.45),44+j*26/99,2.02+random.uniform(-.04,.09),.4,.3,.22,'hedge-burgundy','back-hedge-leaves',8,4)
flush()
# Per-face UVs: wood's longest edge is its grain direction, paving uses world scale.
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('feature_id')!='WTERR':continue
 uv=o.data.uv_layers.new(name='WTERR_surface') if not o.data.uv_layers else o.data.uv_layers.active
 for p in o.data.polygons:
  vs=[o.data.vertices[v].co for v in p.vertices];wood=any('timber' in m.name for m in o.data.materials)
  if wood:
   edges=[vs[(k+1)%len(vs)]-v for k,v in enumerate(vs)];u=max(edges,key=lambda e:e.length).normalized();v=p.normal.cross(u).normalized()
  else:
   axis=max(range(3),key=lambda k:abs(p.normal[k]));u=Vector((0,1,0) if axis==0 else (1,0,0));v=p.normal.cross(u).normalized()
  for li in p.loop_indices:
   co=o.data.vertices[o.data.loops[li].vertex_index].co
   uv.data[li].uv=(co.dot(v)*3,co.dot(u)*.45) if wood else (co.dot(u)*1.7,co.dot(v)*1.7)
 o['material_reference']='IMG_4378,4380,4384,4395';o['texture_status']='generated repeatable approximations; not photo-projected'
 if any(t in o.name for t in ['steps','coping','rail-post','rail-bar','upper-stair']):
  mod=o.modifiers.new('softened visible edges','BEVEL');mod.width=.012;mod.segments=2
s['revision']='v3 photo-guided skylight exposure and materials';s.camera=views['overview']
checkpoint=OUT/'west-garden-terrace-v3.blend';bpy.ops.wm.save_as_mainfile(filepath=str(checkpoint))
render('after',['overview','platform','entry'])
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.data.objects:
 if o.get('feature_id')=='WTERR':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'west-garden-terrace-v3.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
bpy.ops.wm.open_mainfile(filepath=str(checkpoint))
bad=[]
for o in bpy.data.objects:
 if o.type!='MESH' or o.get('feature_id')!='WTERR':continue
 bm=bmesh.new();bm.from_mesh(o.data)
 if any(not e.is_manifold for e in bm.edges) or bm.calc_volume(signed=True)<=0:bad.append(o.name)
 bm.free()
assert not bad,bad
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in hashes.items())
raw=(OUT/'west-garden-terrace-v3.glb').read_bytes();n,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+n]);assert all('bufferView' in im for im in g['images']);assert len(g['images'])>=10
report=dict(baselines_unchanged=hashes,checkpoint_reopens=True,closed_positive_meshes=True,stone_pieces=count,embedded_images=len(g['images']),glb_bytes=len(raw),source_photos=[4368,4377,4378,4380,4384,4390,4395],geometry_change='skylight eave 2.47 -> 1.95; apex 3.47 -> 2.80; metres inferred',limitations=['footprint and compass registration unresolved','stone layout and texture grain are generated approximations','no exhaustive self intersection check'])
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(OUT/'west-garden-terrace-v3.glb'));assert any(o.get('feature_id')=='WTERR' for o in bpy.data.objects);report['glb_imports']=True
(OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print('WTERR_V3_COMPLETE',report)
