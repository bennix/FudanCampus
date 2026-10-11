"""Independent three-detail-level export; never save back into the native source."""
import bpy,bmesh,sys,json,math,gc
from pathlib import Path
import numpy as np
from mathutils import Matrix,Vector
O=Path(__file__).resolve().parent;ROOT=O.parents[2];sys.path.insert(0,str(ROOT/'scripts'))
from export_visible_glb import export_visible_glb
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,write,plain,material_signature
SRC=O/'guanghua-closeout-final.blend';srcsha=sha(SRC)
manifest=json.loads((ROOT/'web/public/campus-manifest.json').read_text(encoding='utf-8'))
building=next(b for b in manifest['buildings'] if b['id']=='27');scale=2/3
translation=Vector((building['position'][0]-20*scale,-building['position'][2]-153*scale,0))
transform=Matrix.Translation(translation)@Matrix.Scale(scale,4)
bpy.ops.wm.open_mainfile(filepath=str(SRC));source=bpy.context.scene;dep=bpy.context.evaluated_depsgraph_get()
scene=bpy.data.scenes.new('Closeout web derivative');bpy.context.window.scene=scene
cache={};leafmats={};buffers={};prototype_cache={};stats={'near':0,'middle':0,'far':0,'static':0};font_expected=[]
def material(m):
 if m is None:return None
 key=material_signature(m)
 if key in cache:return cache[key]
 mm=m.copy();mm.name='WEB '+m.name
 if mm.use_nodes:
  p=next((n for n in mm.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if p and p.inputs['Base Color'].is_linked and not any(n.type=='TEX_IMAGE' for n in mm.node_tree.nodes):
   for link in list(p.inputs['Base Color'].links):mm.node_tree.links.remove(link)
   p.inputs['Base Color'].default_value=mm.diffuse_color
   mm['web_conversion']='Controlled native diffuse color; procedural microrelief not represented in glTF'
 cache[key]=mm;return mm
def leafmat(key):
 if key in leafmats:return leafmats[key]
 color={'olive':(.10,.19,.048),'sage':(.145,.235,.065),'red':(.145,.041,.05),'conifer':(.075,.145,.060)}[key]
 n=128;y,x=np.mgrid[0:n,0:n];u=x/(n-1)*2-1;v=y/(n-1)*2-1
 alpha=(u*u+(v/(.90-.08*u))**2<.96).astype(np.float32)
 brightness=.90+.13*np.exp(-(v/.09)**2)+.025*np.sin(u*24+v*12)
 rgba=np.empty((n,n,4),np.float32);rgba[:,:,:3]=np.asarray(color)[None,None,:]*brightness[:,:,None];rgba[:,:,3]=alpha
 im=bpy.data.images.new('Closeout oval blade '+key,width=n,height=n,alpha=True);im.pixels.foreach_set(rgba.ravel());im.file_format='PNG';im.filepath_raw=str(O/('leaf-'+key+'.png'));im.save();im.pack()
 m=bpy.data.materials.new('WEB leaf '+key);m.use_nodes=True;m.diffuse_color=(*color,1);nt=m.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.65
 tex=nt.nodes.new('ShaderNodeTexImage');tex.image=im;nt.links.new(tex.outputs['Color'],p.inputs['Base Color']);nt.links.new(tex.outputs['Alpha'],p.inputs['Alpha']);m.surface_render_method='DITHERED';m.use_backface_culling=False
 leafmats[key]=m;return m
def mesh(name,v,f,mats,mi=None,uv=None):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
 for mat in mats:me.materials.append(mat)
 if mi is not None:me.polygons.foreach_set('material_index',np.asarray(mi,np.int32))
 if uv is not None:
  lay=me.uv_layers.new(name='Leaf UV');a=np.asarray([uv[l.vertex_index] for l in me.loops],np.float32);lay.data.foreach_set('uv',a.ravel())
 return me
def link(name,me,matrix,props):
 o=bpy.data.objects.new(name,me);scene.collection.objects.link(o);o.matrix_world=matrix
 for k,v in props.items():
  if v is not None:o[k]=v
 return o
def add_static(o,me):
 # Feature IDs remain separable; spatial tiles retain useful culling bounds.
 a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
 mx=np.asarray(o.matrix_world);p=a@mx[:3,:3].T+mx[:3,3];center=p.mean(axis=0)
 fid=o.get('feature_id') or 'UNCLASSIFIED'
 vegetation=fid in {'TREE_CANOPY_V6','GARDEN_VEGETATION_V3','VEGETATION','VEGETATION_V2'} or o.get('closeout_role')=='vegetation'
 key=(fid,int(center[0]//45),int(center[1]//45),vegetation)
 group=buffers.setdefault(key,dict(v=[],f=[],mi=[],uv=[],mats=[],sources=[]));group['sources'].append(o.name)
 mats=[material(m) for m in me.materials];lookup=[]
 for m in mats:
  if m not in group['mats']:group['mats'].append(m)
  lookup.append(group['mats'].index(m))
 uv=me.uv_layers.active
 # Preserve per-corner UV by splitting polygon corners; compression welds later.
 for face in me.polygons:
  ids=[]
  for li in face.loop_indices:
   vi=me.loops[li].vertex_index;ids.append(len(group['v']));group['v'].append(p[vi].tolist());group['uv'].append(tuple(uv.data[li].uv) if uv else tuple(p[vi,:2]))
  group['f'].append(ids);group['mi'].append(lookup[face.material_index] if lookup else 0)
 # UV array for original unused vertices is filled at write time.
def leaf_fans(me):
 starts=np.empty(len(me.polygons),np.int32);totals=starts.copy();me.polygons.foreach_get('loop_start',starts);me.polygons.foreach_get('loop_total',totals)
 ix=np.empty(len(me.loops),np.int32);me.loops.foreach_get('vertex_index',ix);rows=np.zeros((len(me.polygons),3),np.int32);valid=totals==3;rows[valid]=ix[starts[valid,None]+np.arange(3)]
 cand=np.where(valid&(rows[:,1]==rows[:,0]+1)&(rows[:,2]==rows[:,0]+8))[0];cand=cand[cand+7<len(rows)];out=[];removed=np.zeros(len(me.polygons),bool)
 mats=np.empty(len(me.polygons),np.int32);me.polygons.foreach_get('material_index',mats)
 for j in cand:
  b=int(rows[j,0]);r=rows[j:j+8]
  if np.array_equal(r[:,0],np.arange(b,b+8)) and np.all(r[:,2]==b+8):out.append((b,int(mats[j])));removed[j:j+8]=True
 return out,removed
def blades(o,centers,us,ws,colors,tree=False):
 seed=sum(ord(c) for c in o.name)+100117;nr=np.random.default_rng(seed);count=len(centers);order=nr.permutation(count)
 for lod,fraction,enlarge in [('near',.52 if tree else .38,1.08),('middle',.23 if tree else .18,1.30),('far',.04,2.30)]:
  ix=order[:max(1,int(count*fraction))];c=centers[ix];u=us[ix]*enlarge;w=ws[ix]*enlarge
  v=np.stack([c-u-w,c+u-w,c+u+w,c-u+w],axis=1).reshape(-1,3);base=np.arange(len(ix))*4
  f=np.stack([np.column_stack([base,base+1,base+2]),np.column_stack([base,base+2,base+3])],axis=1).reshape(-1,3)
  keys=['olive','sage','red','conifer'];mats=[leafmat(k) for k in keys];mi=np.repeat(colors[ix],2);uv=np.tile([[0,0],[1,0],[1,1],[0,1]],(len(ix),1))
  me=mesh(o.name+' '+lod,v.tolist(),f.tolist(),mats,mi,uv);matrix=transform@o.matrix_world
  shared=False
  if lod!='near' and (tree or o.name.startswith('GV3 shrub ')):
   habit=('conifer' if 'needles' in o.name else 'avenue' if 'south avenue' in o.name else 'garden',seed%5,lod) if tree else ('shrub',o.data.name,seed%3,lod)
   if habit in prototype_cache:
    proto,psize=prototype_cache[habit];size=np.ptp(v,axis=0);factor=np.maximum(size,.001)/np.maximum(psize,.001)
    # Center and span registration retains each inferred root and crown envelope.
    pco=np.array([v.co[:] for v in proto.vertices]);shift=v.mean(axis=0)-pco.mean(axis=0)*factor
    matrix=matrix@Matrix.Translation(Vector(shift))@Matrix.Diagonal(Vector((*factor,1)));bpy.data.meshes.remove(me);me=proto;shared=True
   else:prototype_cache[habit]=(me,np.ptp(v,axis=0))
  link(o.name+' '+lod,me,matrix,dict(feature_id=o.get('feature_id'),closeout_lod=lod,campusVegetation=True,
       tree_group=o.get('tree_group'),source_object=o.name,source_sha256=srcsha,shared_prototype=shared,
       detail_method='Deterministic complete-blade sampling with oval alpha cutouts; crown prototype sharing at middle/far'))
  stats[lod]+=len(f)
for o in list(source.objects):
 if o.hide_render or o.type not in {'MESH','FONT','CURVE'} or o.get('feature_id')=='CONTEXT_GUANGHUA':continue
 if o.type=='FONT':
  native_name=o.name;o.name=native_name+'__native_source'
  copy=bpy.data.objects.new(native_name,o.data.copy());scene.collection.objects.link(copy);copy.matrix_world=transform@o.matrix_world
  for k in o.keys():copy[k]=o[k]
  copy['text_content']=o.data.body
  for i,m in enumerate(copy.data.materials):copy.data.materials[i]=material(m)
  font_expected.append(dict(name=native_name,body=o.data.body,matrix=plain(copy.matrix_world)));continue
 me=bpy.data.meshes.new_from_object(o.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep)
 a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);a=a.reshape(-1,3)
 tree=o.get('feature_id')=='TREE_CANOPY_V6' and ('leaves' in o.name or 'needles' in o.name)
 if tree and len(a)%4==0:
  q=a.reshape(-1,4,3);centers=q.mean(axis=1);us=(q[:,2]-q[:,0])*.5;ws=(q[:,1]-q[:,3])*.5
  colors=np.full(len(q),3 if 'needles' in o.name else 0,np.int32);blades(o,centers,us,ws,colors,True)
 elif o.get('feature_id')=='GARDEN_VEGETATION_V3':
  fans,removed=leaf_fans(me)
  if fans:
   ids=np.asarray([r[0] for r in fans]);q=a[ids[:,None]+np.arange(9)];centers=(q[:,0]+q[:,4])*.5;us=(q[:,4]-q[:,0])*.5;ws=(q[:,6]-q[:,2])*.5
   colors=np.asarray([2 if r[1] in {5,6,7} else r[1]%2 for r in fans],np.int32);blades(o,centers,us,ws,colors)
   # Keep the original connected wood independently of thinning leaf blades.
   faces=[tuple(p.vertices) for p in me.polygons if not removed[p.index]]
   if faces:
    rem=mesh(o.name+' retained twigs',a.tolist(),faces,[material(m) for m in me.materials],[p.material_index for p in me.polygons if not removed[p.index]])
    add_static(o,rem);bpy.data.meshes.remove(rem)
  else:add_static(o,me)
 elif o.name in {'POET_DONKEY 驢背詩思','POET_DONKEY inset nameplate'}:
  for i,m in enumerate(me.materials):me.materials[i]=material(m)
  link(o.name,me.copy(),transform@o.matrix_world,dict(feature_id='POET_DONKEY',text_content='驢背詩思' if '驢' in o.name else '',source_sha256=srcsha,closeout_lod='static'))
 else:add_static(o,me)
 bpy.data.meshes.remove(me)
 print('PREPARED',o.name,flush=True)
for (fid,tx,ty,vegetation),data in buffers.items():
 used=len(data['uv']);unused=len(data['v'])-used
 # add_static interleaves unused source arrays with used corners; derive correct
 # loop UV order directly since every exported polygon corner is unique.
 me=mesh(f'GH {fid} tile {tx} {ty} '+('planting' if vegetation else 'hardscape'),data['v'],data['f'],data['mats'],data['mi'])
 lay=me.uv_layers.new(name='Preserved corner UV');lay.data.foreach_set('uv',np.asarray(data['uv'],np.float32).ravel())
 ob=link(me.name,me,transform,dict(feature_id=fid,closeout_lod='static',campusVegetation=vegetation,source_object_count=len(data['sources']),
 source_sha256=srcsha,sources='; '.join(data['sources'])))
 ratio=.18 if fid=='TREE_CANOPY_V6' else .32 if vegetation or fid=='POET_GARDEN' else .40 if fid=='POET_DONKEY' else .45 if fid=='BUILDING_ENTRY' else .50 if fid in {'WB1','WB2'} else None
 if ratio and len(me.polygons)>3000:
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-5);bm.to_mesh(me);bm.free();me.update()
  bpy.context.view_layer.update();bpy.context.view_layer.objects.active=ob
  mod=ob.modifiers.new('Web-only detail reduction','DECIMATE');mod.ratio=ratio;mod.use_collapse_triangulate=True
  bpy.ops.object.modifier_apply(modifier=mod.name);me=ob.data
  if vegetation:me.polygons.foreach_set('use_smooth',np.ones(len(me.polygons),bool))
 stats['static']+=sum(len(p.vertices)-2 for p in ob.data.polygons)
scene.world=source.world;bpy.context.view_layer.update()
font_records=export_visible_glb(O/'guanghua-closeout-raw.glb',export_cameras=False,export_lights=False,export_apply=True,use_active_scene=True)
assert len(font_records)==3
# Native context building is exported separately to supersede the old staircase
# and front columns; original 27.glb remains a protected comparison source.
for o in list(scene.objects):bpy.data.objects.remove(o,do_unlink=True)
for o in source.objects:
 if o.type!='MESH' or o.hide_render or o.get('feature_id')!='CONTEXT_GUANGHUA':continue
 me=bpy.data.meshes.new_from_object(o.evaluated_get(dep),preserve_all_data_layers=True,depsgraph=dep)
 for i,m in enumerate(me.materials):me.materials[i]=material(m)
 local=Matrix.Translation(Vector((-building['position'][0],building['position'][2],0)))@transform@o.matrix_world
 link(o.name,me,local,dict(building_id='27',feature_id='CONTEXT_GUANGHUA',source_sha256=srcsha,geometry_confidence='Visible front updated; hidden facades inferred'))
bpy.context.view_layer.update()
export_visible_glb(O/'guanghua-building-27.glb',export_cameras=False,export_lights=False,export_apply=True,use_active_scene=True)
assert sha(SRC)==srcsha
write(O/'export-conversion.json',dict(source=str(SRC),source_sha256=srcsha,scale=scale,translation_blender=list(translation),
 transform_confidence='Inherited provisional campus registration, not surveyed',triangle_estimates=stats,editable_text_export=font_records,
 font_expected=font_expected,shared_canopy_prototypes=len(prototype_cache),raw_bytes=(O/'guanghua-closeout-raw.glb').stat().st_size,
 feature_ids=sorted(set(o.get('feature_id') for o in source.objects if o.type in {'MESH','FONT'} and not o.hide_render and o.get('feature_id') and o.get('feature_id')!='CONTEXT_GUANGHUA')),
 material_conversion='Procedural color fallback recorded in WEB material extras; native microrelief does not transfer',native_source_unchanged=True))
print('THREE_LOD_EXPORT_COMPLETE',stats,len(prototype_cache),flush=True)
