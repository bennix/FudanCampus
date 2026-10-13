import bpy,bmesh,json,hashlib,sys,shutil
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;R=O.parents[2]
batch=O/sys.argv[-1];base=O.parent/'stage01-east.blend'
payload=json.loads((batch/'mesh-payload.json').read_text())
target=batch/'west-exit-study.blend'
if target.exists():raise RuntimeError('Immutable batch already contains a model')
def sig(o):
    data={'matrix':[list(r) for r in o.matrix_world],'vertices':[list(v.co) for v in o.data.vertices],'faces':[list(f.vertices) for f in o.data.polygons],'materials':[m.name for m in o.data.materials]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def protected():return {o.name:sig(o) for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')!='EPATH'}
def file_hash(p):return hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(base));s=bpy.context.scene;original=protected()
mat=bpy.data.materials['pink-path'];turf=bpy.data.materials['FIN_garden_grass']
root=next(o for o in bpy.data.objects if o.get('feature_id')=='EPATH' and o.type=='EMPTY')
def cam(name,loc,target,scale):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.type='ORTHO';d.ortho_scale=scale;d.clip_end=1000;return o
top=cam('ROAD_SAMPLE_TOP',(76.7,47.3,45),(76.7,47.3,0),20)
side=cam('ROAD_SAMPLE_SIDE',(90,35,15),(76.7,47,1),22)
exitcam=bpy.data.objects['V4 east-exit']
s.render.resolution_x=1000;s.render.resolution_y=800;s.render.resolution_percentage=100;s.cycles.samples=16
neutral=bpy.data.materials.new('ROAD_QA_neutral');neutral.diffuse_color=(.62,.62,.62,1);neutral.use_nodes=True
neutral.use_fake_user=True
neutral.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.62,.62,.62,1)
def render(name,camera,clay=False):
    restore=[]
    if clay:
        for o in bpy.data.objects:
            if o.type=='MESH' and o.get('feature_id')=='EPATH' and 'terrain' not in o.name:
                restore.append((o,list(o.data.materials)))
                for i in range(len(o.data.materials)):o.data.materials[i]=neutral
    s.camera=camera;s.render.filepath=str(batch/(name+'.png'));bpy.ops.render.render(write_still=True)
    for o,materials in restore:
        for i,m in enumerate(materials):o.data.materials[i]=m
for name,camera in [('before-top-neutral',top),('before-exit-neutral',exitcam)]:
    cached=O/'diagnostic-01'/(name+'.png')
    if batch.name!='diagnostic-01' and cached.exists():shutil.copy2(cached,batch/(name+'.png'))
    else:render(name,camera,True)
retained={}
for name,remove in payload['removals'].items():
    o=bpy.data.objects[name];indices=set(remove)
    old_coords=[tuple(v.co) for v in o.data.vertices if v.index not in indices]
    if len(indices)==len(o.data.vertices):bpy.data.objects.remove(o,do_unlink=True);continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm,geom=[bm.verts[i] for i in sorted(indices)],context='VERTS');bm.to_mesh(o.data);bm.free()
    assert sorted(tuple(v.co) for v in o.data.vertices)==sorted(old_coords)
    retained[name]={'remaining_vertices':len(old_coords),'outside_patch_coordinates_unchanged':True}
generated=[]
for kind,material in [('road',mat),('terrain',turf)]:
    d=payload[kind];mesh=bpy.data.meshes.new('EPATH_west_sample_'+kind);mesh.from_pydata(d['vertices'],[],d['faces']);mesh.update()
    assert not mesh.validate(),'Blender found invalid input geometry'
    mesh.materials.append(material)
    o=bpy.data.objects.new('EPATH__west_sample_'+kind,mesh);root.users_collection[0].objects.link(o);o.parent=root
    o['feature_id']='EPATH';o['revision']='road-rebuild-v1';o['source_photos']=[4568,4565,4569];o['geometry_confidence']='inferred';o['scope']='West exit only; remainder not repaired';o['surface_role']=kind
    o['source_segment_ids']=json.dumps(sorted(set(v['source'] for v in payload['network']['source_strip_boundaries'])))
    o['profile_status']='Technical hypothesis, not accepted as measured reconstruction'
    uv=mesh.uv_layers.new(name='Road_metres')
    for loop in mesh.loops:
        co=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x*.3,co.y*.3)
    bm=bmesh.new();bm.from_mesh(mesh)
    bad=sum(not e.is_manifold for e in bm.edges);volume=bm.calc_volume(signed=True);bm.free()
    assert bad==0 and volume>0,(kind,bad,volume)
    generated.append({'object':o.name,'nonmanifold_edges':bad,'signed_volume':volume,'vertices':len(mesh.vertices),'faces':len(mesh.polygons)})
assert protected()==original
s['road_rebuild_status']='LOCAL GEOMETRY STUDY; WEST EXIT ONLY; SITE ELEVATIONS UNVERIFIED'
s.camera=exitcam
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.wm.open_mainfile(filepath=str(target));s=bpy.context.scene
assert protected()==original
hashes=json.loads((O/'protected-files.json').read_text());assert all(file_hash(R/p)==h for p,h in hashes.items())
report={'non_EPATH_geometry_materials_unchanged':True,'outside_patch_remaining_vertices':retained,'checkpoint_reopened':True,'protected_files_unchanged':len(hashes),'generated_meshes':generated,'visual_review':'pending','site_profile':'inferred'}
(batch/'blender-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
mat=bpy.data.materials['pink-path'];neutral=bpy.data.materials['ROAD_QA_neutral']
render('after-top-neutral',bpy.data.objects['ROAD_SAMPLE_TOP'],True)
render('after-exit-neutral',bpy.data.objects['V4 east-exit'],True)
render('after-exit-textured',bpy.data.objects['V4 east-exit'])
render('after-side-neutral',bpy.data.objects['ROAD_SAMPLE_SIDE'],True)
manifest={'model_sha256':file_hash(target),'base_sha256':file_hash(base),'batch':batch.name,'status':'diagnostic_visual_pending','script_sha256':file_hash(Path(__file__)),'configuration_sha256':file_hash(O/'road-generation-config.json'),'payload_sha256':file_hash(batch/'mesh-payload.json'),'cameras':{name:{'matrix':[list(r) for r in bpy.data.objects[name].matrix_world],'lens':bpy.data.objects[name].data.lens,'ortho_scale':bpy.data.objects[name].data.ortho_scale} for name in ['ROAD_SAMPLE_TOP','ROAD_SAMPLE_SIDE','V4 east-exit']}}
(batch/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('WEST_SAMPLE_COMPLETE')
