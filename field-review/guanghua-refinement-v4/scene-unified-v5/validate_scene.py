"""Reopen the unified checkpoint and validate all branch content and corridor junction."""
import sys,json,bpy,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O))
from scene_fingerprints import sha,snapshot,write
A=json.loads((O/'source-audit.json').read_text(encoding='utf-8'))
M=json.loads((O/'version-manifest.json').read_text(encoding='utf-8'))
expected=json.loads((O/'expected-unified-snapshot.json').read_text(encoding='utf-8'))
OUT=Path(M['scene']);assert sha(OUT)==M['scene_sha256']
bpy.ops.wm.open_mainfile(filepath=str(OUT))
actual=snapshot()
errors={n:[k for k in expected[n] if actual.get(n,{}).get(k)!=expected[n][k]] for n in expected if actual.get(n)!=expected[n]}
assert not errors,errors
assert actual.keys()==expected.keys()
for x in A['sources'].values():assert sha(x['path'])==x['sha256'],x['path']
fids=set(o.get('feature_id') for o in bpy.context.scene.objects if o.get('feature_id'))
original=json.loads((O.parent/'straight-path-a-v1/validation.json').read_text(encoding='utf-8'))
assert set(original['source_feature_ids'])<=fids
meshes=set()
for ob in bpy.context.scene.objects:
    if ob.type!='MESH' or ob.data.as_pointer() in meshes:continue
    meshes.add(ob.data.as_pointer());a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
    assert np.isfinite(a).all(),ob.name
sys.path.insert(0,str(O.parent/'straight-path-a-v1'))
import build as B
pathobs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id')=='E_WALK']
solids=[B.C.solid_check(ob) for ob in pathobs];assert len(pathobs)==200
plaza=bpy.data.objects['FORECOURT photo grid plaza']
trees={o.name:BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],all_triangles=False) for o in pathobs+[plaza]}

def height(x,y,names):
    hits=[]
    for name in names:
        hit=trees[name].ray_cast(Vector((x,y,2)),Vector((0,0,-1)),3)
        if hit[0] is not None:hits.append((hit[0].z,name))
    return max(hits) if hits else None
samples=[]
for i in range(241):
    x=B.X0+.00005+(B.X1-B.X0-.0001)*i/240
    a=height(x,B.Y1-.0001,[o.name for o in pathobs]);b=height(x,B.Y1+.0001,[plaza.name])
    assert a and b,(x,a,b)
    samples.append({'x':x,'path_z':a[0],'plaza_z':b[0],'surface':a[1]})
stone=[r for r in samples if 'paving bed' not in r['surface']]
step=max(abs(r['path_z']-r['plaza_z']) for r in stone);assert step<1e-4
assert all(r['plaza_z']-.0026<=r['path_z']<=r['plaza_z']+.0001 for r in samples)
# Reuse the original audit's polygon projection method on the merged scene.
import ast
parsed=ast.parse((O.parent/'straight-path-a-v1/verify.py').read_text(encoding='utf-8'))
exec(compile(ast.Module(body=[n for n in parsed.body if isinstance(n,ast.FunctionDef) and n.name in ['clip','occupied_area']],type_ignores=[]),'<original junction area audit>','exec'))
overlaps={n:occupied_area(bpy.data.objects[n],[B.X0,B.X1,B.Y0,B.Y1]) for n in [plaza.name,'LAWN | satellite-fixed concave north edge','EDGE_PATHS__south-walk__FIN_pavers','LAWN_EDGE segmented granite 177']}
assert max(overlaps.values())<1e-6,overlaps
depths=[max(B.ztop(v.co.y)-v.co.z for v in o.data.vertices if v.co.z>B.ZB+.0001) for o in pathobs if o.get('component')=='arc border']
assert len(depths)==198 and max(abs(d-B.DEPTH) for d in depths)<1e-6
images=[im for im in bpy.data.images if im.name.startswith('P5 ') and im.type=='IMAGE']
assert len(images)==4 and all(im.packed_file for im in images)
missing_textures=[]
for ob in bpy.context.scene.objects:
    if ob.type!='MESH':continue
    for mat in ob.data.materials:
        if not mat or not mat.node_tree:continue
        for n in mat.node_tree.nodes:
            if n.type=='TEX_IMAGE' and n.image and not n.image.packed_file:missing_textures.append(n.image.name)
assert not missing_textures,sorted(set(missing_textures))
counts={k:sum(1 for owner in M['object_owners'].values() if owner==k) for k in ['base','garden','planters','path']}
R={'checkpoint_reopens':True,'scene_sha256':M['scene_sha256'],'exact_expected_mesh_content':True,'mesh_objects':len(actual),
 'all_source_files_unchanged':True,'content_owners':counts,'object_conflicts':A['object_conflicts'],
 'garden_new_objects':len(A['diff']['garden']['added']),'garden_changed_original_objects':len(A['diff']['garden']['changed']),
 'planter_material_objects':4,'packed_planter_textures':4,'all_used_image_textures_packed':True,
 'path_solids':len(pathobs),'path_nonmanifold_edges':sum(r['nonmanifold'] for r in solids),
 'path_zero_area_faces':sum(r['zero_area'] for r in solids),'path_positive_volumes':all(r['volume']>0 for r in solids),
 'all_mesh_coordinates_finite':True,'required_feature_ids_retained':True,'deleted_old_curbs_absent':len(A['diff']['path']['deleted']),
 'plaza_interface_samples':len(samples),'plaza_interface_covered':True,'maximum_stone_face_step':step,
 'intentional_filled_joint_recess':.0025,'corridor_projected_overlap_areas':overlaps,
 'arc_bands':len(depths),'mesh_groove_depth_range':[min(depths),max(depths)],
 'limits':M['limits']}
write(O/'validation.json',R);write(O/'unified-junction-samples.json',samples)
M['status']='reopen/content/junction validation passed; renders pending';write(O/'version-manifest.json',M)
print('VALIDATED',json.dumps(R,ensure_ascii=False),flush=True)
