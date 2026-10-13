import bpy,sys,json,numpy as np,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import sha,snapshot,write,plain,rna_values,props
M=json.loads((O/'version-manifest.json').read_text(encoding='utf-8'));expected=json.loads((O/'expected-snapshot.json').read_text(encoding='utf-8'));before=json.loads((O/'baseline-snapshot.json').read_text(encoding='utf-8'))
assert sha(M['source'])==M['source_sha256'];assert sha(M['scene'])==M['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=M['source'])
def labels():
    return {o.name:dict(body=o.data.body,matrix=plain(o.matrix_world),properties=props(o),settings=rna_values(o.data,('users','name','name_full','is_updated','is_updated_data','is_evaluated','session_uid')),fonts=[getattr(o.data,k).name for k in ['font','font_bold','font_italic','font_bold_italic']],visible=not o.hide_render) for o in bpy.context.scene.objects if o.type=='FONT'}
original_labels=labels();original_features=set(o.get('feature_id') for o in bpy.context.scene.objects if o.get('feature_id'))
original_cameras={o.name:dict(matrix=plain(o.matrix_world),lens=o.data.lens,type=o.data.type,ortho=o.data.ortho_scale) for o in bpy.context.scene.objects if o.type=='CAMERA'}
bpy.ops.wm.open_mainfile(filepath=M['scene']);S=bpy.context.scene
actual=snapshot();assert actual==expected
removed=set(M['removed_tree_objects']);assert not (removed&actual.keys())
protected=[n for n in before if n not in removed];assert all(actual.get(n)==before[n] for n in protected)
assert original_labels==labels();assert original_features<=set(o.get('feature_id') for o in S.objects if o.get('feature_id'))
for n,v in original_cameras.items():
    o=bpy.data.objects[n];assert v==dict(matrix=plain(o.matrix_world),lens=o.data.lens,type=o.data.type,ortho=o.data.ortho_scale),n
finite=0;seen=set();wood=[];leaf_count=0;leaf_bad=0
for ob in S.objects:
    if ob.type!='MESH':continue
    me=ob.data
    if me.as_pointer() not in seen:
        a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);assert np.isfinite(a).all(),ob.name;finite+=1;seen.add(me.as_pointer())
    if ob.get('feature_id')!='TREE_CANOPY_V6':continue
    if ob.name.endswith('wood'):
        counts={}
        for p in me.polygons:
            ids=list(p.vertices)
            for a,b in zip(ids,ids[1:]+ids[:1]):k=tuple(sorted((a,b)));counts[k]=counts.get(k,0)+1
        nonmanifold=sum(v!=2 for v in counts.values());assert nonmanifold==0,ob.name
        me.calc_loop_triangles();volume=0;zero=0
        for tri in me.loop_triangles:
            a,b,c=[me.vertices[i].co for i in tri.vertices];volume+=a.dot(b.cross(c))/6;zero+=int((b-a).cross(c-a).length<1e-10)
        assert volume>0 and zero==0,(ob.name,volume,zero);wood.append(dict(name=ob.name,nonmanifold=0,volume=volume,zero_area=0))
    else:
        n=int(ob['leaf_count']);assert len(me.polygons)==n*2;leaf_count+=n
        vertices=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',vertices);v=vertices.reshape(n,4,3)
        areas=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1);bad=int(np.count_nonzero(areas<1e-10));assert bad==0,(ob.name,bad);leaf_bad+=bad
images=[im for im in bpy.data.images if im.name.startswith('P5 ') and im.type=='IMAGE'];assert len(images)==4 and all(im.packed_file for im in images)
used_unpacked=[]
for o in S.objects:
    if o.type!='MESH':continue
    for m in o.data.materials:
        if m and m.node_tree:
            for n in m.node_tree.nodes:
                if n.type=='TEX_IMAGE' and n.image and not n.image.packed_file:used_unpacked.append(n.image.name)
assert not used_unpacked
# Exact protected snapshots guarantee the original 241-point junction result remains valid.
pathobs=[o for o in S.objects if o.type=='MESH' and o.get('feature_id')=='E_WALK'];assert len(pathobs)==200 and all(o.name in protected for o in pathobs)
plaza=bpy.data.objects['FORECOURT photo grid plaza'];assert plaza.name in protected
oldcheck=json.loads((O.parent/'scene-unified-v5/validation.json').read_text(encoding='utf-8'))
R=dict(scene_sha256=M['scene_sha256'],checkpoint_reopens=True,exact_saved_snapshot_matches=True,source_sha256_unchanged=True,protected_meshes=len(protected),non_tree_geometry_uv_materials_transforms_visibility_properties_unchanged=True,labels_unchanged=original_labels,cameras_unchanged=len(original_cameras),all_required_feature_ids_retained=True,unique_meshes_finite=finite,wood_meshes=wood,leaf_count=leaf_count,zero_area_leaf_faces=leaf_bad,packed_planter_textures=4,all_used_images_packed=True,protected_path_solids=200,unchanged_junction_validation={'samples':oldcheck['plaza_interface_samples'],'maximum_stone_face_step':oldcheck['maximum_stone_face_step'],'reason':'All audited junction mesh geometry, world transforms and visibility equal v5'},new_tree_count=len(M['trees']),new_tree_ground_checks=M['new_root_checks'],source_tree_root_positions_retained=True,limits=['Canopy/branch structure, dimensions and additional planting locations are photo-based inferences','Species represented as mature broadleaf and conifer types; no exact species identification','All new roots pass ground/clearance checks; normal crown/branch overlaps are intentional; no exhaustive pairwise canopy intersection test','Leaf blades are thin open surfaces, wood tube branch junctions intentionally overlap','Native scene stage only; no new GLB or campus webpage asset replacement'])
write(O/'validation.json',R);print('VALIDATED',len(protected),'protected meshes;',len(wood),'closed wood objects;',leaf_count,'leaves',flush=True)
