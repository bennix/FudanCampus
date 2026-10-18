"""Reopen, check fixed assets and measure the actual plaza interface."""
import sys, json, math
from pathlib import Path
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0,str(Path(__file__).resolve().parent))
import build as B

O=B.O
report=json.loads((O/'validation.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(B.OUT))
after=B.snapshots()
assert all(after.get(n)==h for n,h in report['protected_fingerprints'].items())
assert B.sha(B.BASE)==report['source_sha256']
obs=[o for o in bpy.context.scene.objects if o.type=='MESH' and o.get('feature_id')=='E_WALK']
solids=[B.C.solid_check(o) for o in obs]
assert len(obs)==200
corners=[o.matrix_world@Vector(p) for o in obs for p in o.bound_box]
bounds=[min(p.x for p in corners),max(p.x for p in corners),min(p.y for p in corners),max(p.y for p in corners)]
assert max(abs(a-b) for a,b in zip(bounds,[B.X0,B.X1,B.Y0,B.Y1]))<1e-5
plaza=bpy.data.objects['FORECOURT photo grid plaza']
names=[o.name for o in obs]+[plaza.name]
trees={}
for name in names:
    ob=bpy.data.objects[name]
    trees[name]=BVHTree.FromPolygons([ob.matrix_world@v.co for v in ob.data.vertices],[tuple(p.vertices) for p in ob.data.polygons],all_triangles=False)

def height(x,y,allowed):
    hits=[]
    for n in allowed:
        hit=trees[n].ray_cast(Vector((x,y,2)),Vector((0,0,-1)),3)
        if hit[0] is not None:hits.append((hit[0].z,n))
    return max(hits) if hits else None

samples=[]
for i in range(241):
    x=B.X0+.00005+(B.X1-B.X0-.0001)*i/240
    a=height(x,B.Y1-.0001,[o.name for o in obs])
    b=height(x,B.Y1+.0001,[plaza.name])
    samples.append(dict(x=x,path_z=a[0] if a else None,plaza_z=b[0] if b else None,
        surface=a[1] if a else None))
missing=[s for s in samples if s['path_z'] is None or s['plaza_z'] is None]
assert not missing,missing
# Recessed filled mortar is intentional; stone faces must meet the inherited plaza level.
stone_samples=[s for s in samples if 'paving bed' not in s['surface']]
max_step=max(abs(s['path_z']-s['plaza_z']) for s in stone_samples)
assert max_step<1e-4,max_step
assert all(s['path_z']>=s['plaza_z']-.0026 and s['path_z']<=s['plaza_z']+.0001 for s in samples)

def clip(pts,axis,value,above):
    out=[]
    if not pts:return out
    for p,q in zip(pts,pts[1:]+pts[:1]):
        pin=p[axis]>=value if above else p[axis]<=value
        qin=q[axis]>=value if above else q[axis]<=value
        if pin:out.append(p)
        if pin!=qin:
            t=(value-p[axis])/(q[axis]-p[axis])
            out.append(tuple(p[k]+t*(q[k]-p[k]) for k in range(2)))
    return out

def occupied_area(ob,rect):
    total=0
    for p in ob.data.polygons:
        if p.normal.z<.01:continue
        pts=[tuple((ob.matrix_world@ob.data.vertices[i].co)[:2]) for i in p.vertices]
        for axis,value,above in [(0,rect[0],True),(0,rect[1],False),(1,rect[2],True),(1,rect[3],False)]:pts=clip(pts,axis,value,above)
        if len(pts)>2:
            area=abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(pts,pts[1:]+pts[:1])))/2
            total+=area
            if area>1e-6:print('OVERLAP_FACE',ob.name,p.index,area,pts,flush=True)
    return total

rect=[B.X0,B.X1,B.Y0,B.Y1]
overlap={n:occupied_area(bpy.data.objects[n],rect) for n in [plaza.name,'LAWN | satellite-fixed concave north edge','EDGE_PATHS__south-walk__FIN_pavers','LAWN_EDGE segmented granite 177']}
assert max(overlap.values())<1e-6,overlap
depths=[]
for o in obs:
    if o.get('component')!='arc border':continue
    depths.append(max(B.ztop(v.co.y)-v.co.z for v in o.data.vertices if v.co.z>B.ZB+.0001))
assert max(abs(d-B.DEPTH) for d in depths)<1e-6
result=dict(checkpoint_reopens=True,source_unchanged=True,protected_meshes_materials_uv_transforms_unchanged=len(report['protected_fingerprints']),
    centerline_and_width_preserved=True,actual_bounds=bounds,plaza_local_junction_cut_only=True,
    plaza_original_material_and_height_retained=True,
    entrance_urn_objects_preserved=len(report['unchanged_urns']),edited_closed_positive_solids=len(solids),
    zero_area_faces=0,nonmanifold_edges=0,finite_coordinates=True,
    interface_samples=len(samples),north_interface_coverage=True,
    maximum_stone_face_level_difference=max_step,intentional_filled_joint_recess=.0025,
    projected_overlap_area_with_corridor=overlap,measured_mesh_groove_depth_range=[min(depths),max(depths)],
    groove_depth_and_function='推定；网格深度验证不代表现场测量或功能确认',
    output_sha256=B.sha(B.OUT),limits=['相机人工近似，未摄影测量配准','全部尺度和标高为推定','检查范围为本通道及指定交界，不是全场景碰撞认证'])
(O/'reopen-validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'junction-samples.json').write_text(json.dumps(samples,indent=2),encoding='utf-8')
print('REOPEN_VALIDATION_OK',json.dumps(result,ensure_ascii=False),flush=True)
