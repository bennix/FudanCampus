import bpy,bmesh,json,sys,hashlib
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;batch=O/('view-'+sys.argv[-1]);batch.mkdir(exist_ok=True)
D=json.loads((O/'shape.json').read_text());base=O.parent/'stage01-east.blend'
bpy.ops.wm.open_mainfile(filepath=str(base));s=bpy.context.scene
def signature(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],list(o.matrix_world))).encode()).hexdigest()
lawn=next(o for o in bpy.data.objects if o.type=='MESH' and o.get('feature_id')=='LAWN');lawn_sig=signature(lawn);lawn_name=lawn.name
base_hash=hashlib.sha256(base.read_bytes()).hexdigest()
root=next(o for o in bpy.data.objects if o.type=='EMPTY' and o.get('feature_id')=='EPATH')
for name,indices in D['removals'].items():
    o=bpy.data.objects[name]
    if len(indices)==len(o.data.vertices):bpy.data.objects.remove(o,do_unlink=True);continue
    bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in indices],context='VERTS');bm.to_mesh(o.data);bm.free()
for o in bpy.data.objects:
    if o.type=='MESH' and o.get('feature_id') in {'ESKY','EOPEN_S'}:
        o.location.z+=D['lift_skylight_and_opening'];o['shape_revision']='west-exit-shape-v1; local garden level inferred'
    if o.type=='MESH' and o.get('feature_id')=='ESKY' and 'planted-shrubs' in o.name:
        for v in o.data.vertices:v.co.z=.07+(v.co.z-.07)*.58
        o['shape_revision']='Lower hedge silhouette to reveal the photographed louvre base'
    if o.type=='MESH' and o.get('feature_id')=='ETERR' and any(p in o.name for p in ['__wall__','__coping__','__hedge__']):
        for v in o.data.vertices:
            if v.co.x<89 and v.co.y<47.5:
                w=max(0,min(1,(89-v.co.x)/3))*max(0,min(1,(47.5-v.co.y)/.7));v.co.y-=.45*w
        if 'leaf-bronze' in o.name:o.data.materials[0]=bpy.data.materials['leaf-green']
for name,material in [('road','pink-path'),('ground','FIN_garden_grass')]:
    data=D[name];mesh=bpy.data.meshes.new('WestExit_'+name);mesh.from_pydata(data['vertices'],[],data['faces']);mesh.update()
    ob=bpy.data.objects.new('EPATH__photo_shape_'+name,mesh);root.users_collection[0].objects.link(ob);ob.parent=root
    mesh.materials.append(bpy.data.materials[material]);ob['feature_id']='EPATH';ob['source_photos']=[4568,4572,4574];ob['geometry_confidence']='inferred';ob['shape_revision']='west-exit-shape-v1';ob['note']=D['uncertainty']
    uv=mesh.uv_layers.new(name='Shape_metre_UV')
    for loop in mesh.loops:
        co=mesh.vertices[loop.vertex_index].co;uv.data[loop.index].uv=(co.x*.3,co.y*.3)
    for p in mesh.polygons:p.use_smooth=(name=='ground' and p.normal.z>.01)
# Editable centreline remains available in the native model.
cu=bpy.data.curves.new('West exit editable reference centreline','CURVE');cu.dimensions='3D';sp=cu.splines.new('BEZIER');sp.bezier_points.add(len(D['controls'])-1)
for bp,(x,y) in zip(sp.bezier_points,D['controls']):bp.co=(x,y,1.8);bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
guide=bpy.data.objects.new('EPATH | west exit shape controls',cu);root.users_collection[0].objects.link(guide);guide.parent=root;guide.hide_render=True;guide['feature_id']='EPATH';guide['note']='XY shape guide only; surface heights are in prepare_shape.py'
DX=D['registration_x']
def cam(name,loc,target,scale=None,lens=24):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);s.collection.objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=1000
    if scale:d.type='ORTHO';d.ortho_scale=scale
    return o
views={
 'exit':cam('SHAPE exit approximate',(88.2+DX,47.8,3.82),(77+DX,44.5,2.2),lens=24),
 'top':cam('SHAPE top',(79.5+DX,46,50),(79.5+DX,46,0),25),
 'side':cam('SHAPE side',(95+DX,30,15),(80+DX,46,1),25),
 'old-view':bpy.data.objects['V4 east-exit']}
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1100;s.render.resolution_y=825;s.render.resolution_percentage=100
s.camera=views['exit'];s['west_exit_revision']='Photo-led shape iteration; local datum and distant road connections still inferred'
assert signature(lawn)==lawn_sig
target=batch/'west-exit-shape.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
for name,c in views.items():
    s.camera=c;s.render.filepath=str(batch/(name+'.png'));bpy.ops.render.render(write_still=True)
assert hashlib.sha256(base.read_bytes()).hexdigest()==base_hash
bpy.ops.wm.open_mainfile(filepath=str(target))
assert signature(bpy.data.objects[lawn_name])==lawn_sig
(batch/'check.json').write_text(json.dumps({'baseline_unchanged':True,'lawn_unchanged':True,'reopened':True,'status':'visual_review_pending','sources':[4568,4572,4574,4567]},indent=2))
print('SHAPE_SAVED')
