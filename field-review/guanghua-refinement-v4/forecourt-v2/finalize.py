import bpy,bmesh,json,math,hashlib,struct
import numpy as np
from pathlib import Path
O=Path(__file__).resolve().parent
info=json.loads((O/'build-info.json').read_text());base=O.parent/'forecourt-v1/forecourt-entry-v1.blend'
bpy.ops.wm.open_mainfile(filepath=str(O/'forecourt-complete-v2.blend'));s=bpy.context.scene
def digest(o):
 a=np.empty(len(o.data.vertices)*3,np.float32);o.data.vertices.foreach_get('co',a)
 return hashlib.sha256(a.tobytes()+str(list(o.matrix_world)).encode()).hexdigest()
assert all(digest(bpy.data.objects[n])==h for n,h in info['protected'].items())
# Explicit image normal maps keep the fine surface finish portable in GLB.
for m in bpy.data.materials:
 if not m.name.startswith('FC_') or not m.use_nodes:continue
 p=m.node_tree.nodes.get('Principled BSDF');im=next((n.image for n in m.node_tree.nodes if n.type=='TEX_IMAGE' and n.image),None)
 if not im:continue
 n=512;rng=np.random.default_rng(630+len(m.name));h=rng.normal(0,.13,(n,n)).astype(np.float32)
 dx=(np.roll(h,1,1)-np.roll(h,-1,1))*.22;dy=(np.roll(h,1,0)-np.roll(h,-1,0))*.22
 v=np.stack([dx,dy,np.ones_like(h)],axis=-1);v/=np.linalg.norm(v,axis=-1)[:,:,None]
 px=np.ones((n,n,4),np.float32);px[:,:,:3]=v*.5+.5
 normal=bpy.data.images.new(m.name+' normal',width=n,height=n);normal.colorspace_settings.name='Non-Color';normal.pixels.foreach_set(px.ravel());normal.filepath_raw=str(O/(m.name+'-normal.png'));normal.file_format='PNG';normal.save();normal.pack()
 tx=m.node_tree.nodes.new('ShaderNodeTexImage');tx.image=normal;nm=m.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.4
 for link in list(p.inputs['Normal'].links):m.node_tree.links.remove(link)
 m.node_tree.links.new(tx.outputs['Color'],nm.inputs['Color']);m.node_tree.links.new(nm.outputs['Normal'],p.inputs['Normal'])
# Convert the plaque lettering for consistent rendering in third-party viewers.
for ob in list(s.objects):
 if ob.type=='FONT' and ob.get('feature_id')=='POET_DONKEY':
  bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
new=[o for o in s.objects if o.type=='MESH' and o.name.startswith(('POET_','E_ENTRY','FORECOURT','LAWN_EDGE'))]
assert len(new)>100
assert all(math.isfinite(c) for o in new for v in o.data.vertices for c in v.co)
axis=info['entry_axis'];centres=info['urn_centres'];assert abs((centres[0][0]+centres[1][0])/2-axis)<1e-6 and centres[0][1]==centres[1][1]
# Keep only the current mesh state selected, preserving editable baseline scene objects.
bpy.ops.object.select_all(action='DESELECT')
for ob in s.objects:
 if ob.type=='MESH' and not ob.hide_render:ob.hide_set(False);ob.select_set(True)
s.camera=bpy.data.objects[info['cameras']['entry']]
bpy.ops.wm.save_as_mainfile(filepath=str(O/'forecourt-complete-v2.blend'))
bpy.ops.export_scene.gltf(filepath=str(O/'forecourt-complete-v2.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_yup=True)
# Standalone sculpture also available for reuse/review.
bpy.ops.object.select_all(action='DESELECT')
for ob in s.objects:
 if ob.type=='MESH' and ob.get('feature_id')=='POET_DONKEY':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(O/'poet-donkey.glb'),export_format='GLB',use_selection=True,export_extras=True,export_apply=True)
# Final camera batch, with exactly matching geometry to the exported scene.
s.render.resolution_x=1400;s.render.resolution_y=1050;s.cycles.samples=24
for k,cam in info['cameras'].items():
 s.camera=bpy.data.objects[cam];s.render.filepath=str(O/('after-'+k+'.png'));bpy.ops.render.render(write_still=True)
raw=(O/'forecourt-complete-v2.glb').read_bytes();magic,version,size=struct.unpack_from('<4sII',raw);assert (magic,version,size)==(b'glTF',2,len(raw))
length,kind=struct.unpack_from('<II',raw,12);g=json.loads(raw[20:20+length]);assert all('bufferView' in i for i in g.get('images',[]))
assert any(n.get('extras',{}).get('feature_id')=='POET_DONKEY' for n in g['nodes'])
bpy.ops.wm.open_mainfile(filepath=str(O/'forecourt-complete-v2.blend'))
assert all(digest(bpy.data.objects[n])==h for n,h in info['protected'].items())
assert hashlib.sha256(base.read_bytes()).hexdigest()==info['baseline_sha256']
report=dict(baseline_unchanged=True,checkpoint_reopened=True,protected_lawn_building_and_terraces_unchanged=True,east_entry_symmetric=True,entry_axis=axis,entry_line=info['entry_line'],urn_centres=centres,new_finite_meshes=len(new),embedded_images=len(g.get('images',[])),glb_bytes=len(raw),sculpture_glb_bytes=(O/'poet-donkey.glb').stat().st_size,limits=['dimensions and placement are photo-proportion estimates','unseen sculpture surfaces simplified','existing unrelated garden details inherited','not a production campus asset replacement'])
(O/'validation.json').write_text(json.dumps(report,indent=2))
print('FORECOURT_FINAL_COMPLETE',flush=True)
