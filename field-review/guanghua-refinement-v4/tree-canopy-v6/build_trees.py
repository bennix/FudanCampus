"""Reproducible canopy replacement. All non-whitelisted v5 meshes are protected."""
import bpy,sys,json,math,random,gc,time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O.parent/'scene-unified-v5'))
from scene_fingerprints import sha,snapshot,write
BASE=O.parent/'scene-unified-v5/guanghua-unified-v5.blend';OUT=O/'guanghua-tree-canopy-v6.blend'
assert sha(BASE)=='ba1a1169e1ff4705db5b467ce2359fe8c086a2801f07548e8d5bb3f085fb310f'
bpy.ops.wm.open_mainfile(filepath=str(BASE));S=bpy.context.scene
before=snapshot();write(O/'baseline-snapshot.json',before)
source_trees=json.loads((O.parent/'garden-vegetation-v3/validation.json').read_text(encoding='utf-8'))['trees']
whitelist=[t['name']+part for t in source_trees for part in [' bark',' foliage']]
roads=[o for o in S.objects if o.type=='MESH' and not o.hide_render and o.name.startswith('V2 tree ') and 'branches' in o.name]
road_positions=[(o.name,*list(o.location)) for o in roads]
whitelist.extend(o.name.replace('branches',part) for o in roads for part in ['branches','leaves'])
assert len(whitelist)==90 and all(n in before for n in whitelist)
old_triangles=sum(sum(len(p.vertices)-2 for p in bpy.data.objects[n].data.polygons) for n in whitelist)
old_meshes=[]
for n in whitelist:
    ob=bpy.data.objects[n];old_meshes.append(ob.data);bpy.data.objects.remove(ob,do_unlink=True)
for me in set(old_meshes):
    if me.users==0:bpy.data.meshes.remove(me)
gc.collect()
C=bpy.data.collections.new('13_Tree canopy v6 - photo inferred');S.collection.children.link(C)
def material(name,color,bark=False):
    m=bpy.data.materials.new('V6 '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=.88 if bark else .58
    p.inputs['Specular IOR Level'].default_value=.25
    if not bark:
        p.inputs['Subsurface Weight'].default_value=.035
        back=n.new('ShaderNodeNewGeometry');mix=n.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(*color,1);mix.inputs[2].default_value=(*(min(1,c*1.3) for c in color),1);l.new(back.outputs['Backfacing'],mix.inputs[0]);l.new(mix.outputs[0],p.inputs['Base Color'])
    else:
        tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3.8;tex.inputs['Detail'].default_value=5
        coord=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(8,8,.32);l.new(coord.outputs['Object'],scale.inputs[0]);l.new(scale.outputs[0],tex.inputs['Vector'])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*(c*.45 for c in color),1);ramp.color_ramp.elements[1].color=(*(c*1.6 for c in color),1);l.new(tex.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color'])
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.45;bump.inputs['Distance'].default_value=.035;l.new(tex.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
    return m
M=[material(n,c) for n,c in [('deep olive',(.055,.115,.021)),('olive',(.105,.21,.033)),('sage',(.145,.235,.072)),('new growth',(.22,.33,.059)),('plane green',(.13,.24,.056)),('autumn subdued',(.22,.22,.063)),('conifer dark',(.05,.115,.044)),('conifer grey',(.115,.19,.07)),('conifer tips',(.18,.265,.085))]]
BM=[material('grey fissured bark',(.11,.105,.080),True),material('warm conifer bark',(.16,.105,.065),True),material('plane mottled bark',(.18,.17,.135),True)]
rng=random.Random(60301);report=[];root_checks=[]
def mesh_object(name,vertices,faces,mats,indices=None,wood=False):
    me=bpy.data.meshes.new(name);me.from_pydata(vertices,[],faces);me.update()
    for m in mats:me.materials.append(m)
    if indices is not None:me.polygons.foreach_set('material_index',np.asarray(indices,dtype=np.int32))
    if wood:me.polygons.foreach_set('use_smooth',np.ones(len(me.polygons),dtype=np.bool_))
    ob=bpy.data.objects.new(name,me);C.objects.link(ob);ob['feature_id']='TREE_CANOPY_V6';ob['geometry_confidence']='inferred from photo appearance, not surveyed';ob['references']='IMG_4390; IMG_4582; IMG_4568; IMG_4597; IMG_4313';return ob
class Wood:
    def __init__(self):self.v=[];self.f=[];self.terminal=[];self.shoots=[]
    def tube(self,pts,r0,r1,sides=9):
        pts=[Vector(p) for p in pts];start=len(self.v)
        for j,p in enumerate(pts):
            tangent=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u)
            rad=r0+(r1-r0)*j/(len(pts)-1)
            for k in range(sides):
                a=k*math.tau/sides;self.v.append(tuple(p+(math.cos(a)*u+math.sin(a)*v)*rad*(1+.035*math.sin(k*5+j))))
        for j in range(len(pts)-1):
            for k in range(sides):a=start+j*sides+k;b=start+j*sides+(k+1)%sides;self.f.append((a,b,b+sides,a+sides))
        self.f.append(tuple(start+k for k in reversed(range(sides))));self.f.append(tuple(start+(len(pts)-1)*sides+k for k in range(sides)))
    def curve(self,start,end,r0,r1,bend=0):
        a=Vector(start);b=Vector(end);d=b-a;off=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-.5,.5)))*bend
        pts=[a.lerp(b,t)+off*math.sin(math.pi*t) for t in [0,.23,.53,.79,1]];self.tube(pts,r0,r1,8)
        return pts
def leaf_mesh(name,centers,lengths,widths,seed,conifer=False,plane=False):
    nr=np.random.default_rng(seed);n=len(centers)
    # Four-vertex thin, folded leaf: two triangles, no alpha cards or hidden solid crowns.
    az=nr.uniform(0,math.tau,n);pitch=nr.uniform(-.8,.8,n)
    u=np.column_stack((np.cos(az)*np.cos(pitch),np.sin(az)*np.cos(pitch),np.sin(pitch)))
    v=np.column_stack((-np.sin(az),np.cos(az),nr.uniform(-.3,.3,n)))
    a=u*lengths[:,None]*.5;b=v*widths[:,None]*.5
    vs=np.empty((n,4,3),np.float32);vs[:,0]=centers-a;vs[:,1]=centers+b;vs[:,2]=centers+a;vs[:,3]=centers-b
    # Small asymmetric fold keeps individual blades readable at close range.
    vs[:,1,2]+=lengths*.055;vs[:,3,2]-=lengths*.025
    verts=vs.reshape(-1,3);ids=np.arange(n,dtype=np.int32)*4
    faces=np.empty((n,2,3),np.int32);faces[:,0]=np.column_stack((ids,ids+1,ids+2));faces[:,1]=np.column_stack((ids,ids+2,ids+3))
    me=bpy.data.meshes.new(name);me.vertices.add(n*4);me.vertices.foreach_set('co',verts.ravel());me.loops.add(n*6);me.loops.foreach_set('vertex_index',faces.ravel());me.polygons.add(n*2);me.polygons.foreach_set('loop_start',np.arange(n*2,dtype=np.int32)*3);me.polygons.foreach_set('loop_total',np.full(n*2,3,dtype=np.int32))
    for m in M:me.materials.append(m)
    colors=nr.choice([6,7,8] if conifer else [0,1,2,3,4,5],n,p=[.40,.46,.14] if conifer else ([.12,.20,.15,.12,.38,.03] if plane else [.20,.36,.17,.14,.12,.01]))
    me.polygons.foreach_set('material_index',np.repeat(colors,2).astype(np.int32));me.update()
    ob=bpy.data.objects.new(name,me);C.objects.link(ob);ob['feature_id']='TREE_CANOPY_V6';ob['geometry_confidence']='inferred canopy envelope';ob['leaf_count']=n;return ob
def canopy_points(n,h,r,seed,open_crown=False):
    nr=np.random.default_rng(seed);p=nr.normal(size=(n,3));p/=np.linalg.norm(p,axis=1)[:,None];p*=nr.uniform(.16,1,n)[:,None]**(1/3)
    az=np.arctan2(p[:,1],p[:,0]);wave=.89+.1*np.sin(az*3+seed)+.07*np.cos(az*5-seed)+.06*np.sin(p[:,2]*9+az*2)
    p[:,0]*=r*wave;p[:,1]*=r*wave*(.94+.08*math.sin(seed));p[:,2]*=h*(.29 if not open_crown else .235)
    p[:,0]+=.4*np.sin(p[:,2]*.4+seed);p[:,1]+=.23*np.cos(p[:,2]*.7);p[:,2]+=h*.73
    return p
def broad_tree(label,x,y,z,h,r,seed,open_crown=False,plane=False):
    nr=np.random.default_rng(seed);w=Wood();dr=max(.13,h*(.017 if plane else .0175));lean=Vector((rng.uniform(-1.2,1.2),rng.uniform(-.8,.8),0))
    habit=seed%5
    # Different unequal branch spans and crown aspect ratios, rather than the same envelope.
    sx=[1.2,.87,1.15,1.03,.95][habit];sy=[.86,1.06,.93,.78,1.12][habit]
    base=Vector((0,0,-.012));split=h*(rng.uniform(.33,.43) if plane else rng.uniform(.24,.38));trunk=[base,Vector((.08,-.05,1.4)),lean*.35+Vector((0,0,split*.55)),lean+Vector((0,0,split))]
    w.tube(trunk,dr,dr*.66,14)
    for i in range(5):
        a=i*1.27+rng.uniform(-.35,.35);pt=Vector((math.cos(a)*dr*3.0,math.sin(a)*dr*3.0,-.01));w.tube([pt,pt*.65+Vector((0,0,.22)),trunk[1]],dr*.38,dr*.12,8)
    # Unequal leaders, several branch generations, tapered small twigs through the crown.
    leaders=[];nleaders=3+seed%3;rotation=rng.uniform(0,math.tau)
    for j in range(nleaders):
        a=rotation+j*math.tau/nleaders+rng.uniform(-.5,.5);rr=r*rng.uniform(.36,.69);end=Vector((math.cos(a)*rr*sx,math.sin(a)*rr*sy,h*rng.uniform(.65,.87)))
        pts=w.curve(trunk[-1] if j<2 else trunk[-2].lerp(trunk[-1],rng.uniform(.55,.95)),end,dr*rng.uniform(.48,.73),dr*.055,bend=r*.12);leaders.append(pts)
        branch_number=rng.randint(9,13) if not open_crown else rng.randint(6,9)
        for k in range(branch_number):
            a2=a+rng.uniform(-1.55,1.55);rr2=r*rng.uniform(.48,1.03)
            # Branch tips have independent heights, deliberate missing sectors, and unequal spread.
            tipheight=h*rng.uniform(.53,.97) if habit!=1 else h*rng.uniform(.62,1.03)
            target=Vector((math.cos(a2)*rr2*sx,math.sin(a2)*rr2*sy,tipheight))
            origin=pts[rng.choice([1,2,3])];secondary=w.curve(origin,target,dr*rng.uniform(.10,.19),dr*.012,bend=r*.09)
            # Foliage follows elongated twig sprays rather than filling a spherical volume.
            for t in range(5):
                tip=target+Vector((rng.uniform(-r*.23,r*.23),rng.uniform(-r*.19,r*.19),rng.uniform(-h*.06,h*.06)))
                shoot=w.curve(secondary[rng.choice([2,3])],tip,dr*.030,dr*.003,bend=.19)
                w.shoots.append(shoot)
                w.terminal.append(tuple(tip))
    n=int((r/6)**1.15*(56000 if not open_crown else 15500));n=max(6500,n)
    chosen=nr.integers(0,len(w.shoots),n);t=nr.uniform(.15,1,n)
    shoots=np.asarray(w.shoots);segment=np.minimum((t*4).astype(int),3);fraction=t*4-segment
    points=shoots[chosen,segment]*(1-fraction[:,None])+shoots[chosen,segment+1]*fraction[:,None]
    # Long narrow connected sprays make an uneven lacy silhouette, with daylight through gaps.
    points+=nr.normal(size=(n,3))*[r*.044,r*.038,h*.020]
    lengths=nr.uniform(.10,.16,n) if not open_crown else nr.uniform(.085,.145,n);widths=lengths*nr.uniform(.39,.62,n)
    bark=mesh_object(label+' wood',w.v,w.f,[BM[2 if plane else 0]],wood=True);leaves=leaf_mesh(label+' leaves',points,lengths,widths,seed,plane=plane)
    for ob in [bark,leaves]:ob.location=(x,y,z);ob['tree_group']=label;ob['placement_confidence']='inferred; existing v5 root retained where applicable'
    report.append(dict(name=label,x=x,y=y,z=z,height=h,crown_radius=r,type='open broadleaf' if open_crown else ('mature avenue broadleaf' if plane else 'garden broadleaf'),crown_habit=['spreading unequal limbs','upright uneven crown','asymmetric wide limbs','shallow spreading crown','irregular narrow crown'][habit],leaf_distribution='along irregular twig sprays, no filled spherical envelope',leaves=n,seed=seed))
    print('TREE',label,n,flush=True)
def conifer_tree(label,x,y,z,h,r,seed):
    nr=np.random.default_rng(seed);w=Wood();dr=h*.021
    trunk=[(.06*math.sin(t*5),.04*math.cos(t*3),h*t) for t in [0,.1,.25,.45,.65,.85,1]];w.tube(trunk,dr,.025,14)
    allpoints=[];total=0
    for level in range(17):
        f=.30+level*.039+nr.uniform(-.015,.015);rad=r*(1-(f-.3)/.73)**.74
        for j in range(5):
            if nr.uniform()<.16:continue
            a=j*math.tau/5+level*1.38+nr.uniform(-.45,.45);rr=rad*nr.uniform(.65,1.12);start=Vector((0,0,h*f+nr.uniform(-.16,.16)));end=Vector((math.cos(a)*rr,math.sin(a)*rr,h*f-h*nr.uniform(.014,.038)));mid=start.lerp(end,.45)+Vector((0,0,h*.022));w.tube([start,mid,end],max(.014,dr*(1-f)*.33),.006,7)
            for k in range(6):
                t=.25+k*.13;origin=mid.lerp(end,max(0,(t-.45)/.55)) if t>.45 else start.lerp(mid,t/.45);angle=a+((-1)**k)*nr.uniform(.35,1.0);tip=origin+Vector((math.cos(angle)*rr*.36,math.sin(angle)*rr*.36,h*.01));w.curve(origin,tip,.013,.002,bend=.08)
                # Narrow, flattened feathery foliage sprays along each branchlet.
                count=int(135*max(.22,(1-f))*(rr+1));tvals=nr.uniform(0,1,count);p=np.asarray(origin)[None,:]*(1-tvals[:,None])+np.asarray(tip)[None,:]*tvals[:,None];p+=nr.normal(size=(count,3))*[.18,.18,.12];allpoints.append(p);total+=count
    p=np.vstack(allpoints);n=len(p)
    # Thin tapered foliage leaflets. Each is a true thin mesh, no opaque cone.
    lengths=nr.uniform(.12,.24,n);widths=lengths*nr.uniform(.13,.22,n)
    bark=mesh_object(label+' wood',w.v,w.f,[BM[1]],wood=True);leaves=leaf_mesh(label+' needles',p,lengths,widths,seed,conifer=True)
    for ob in [bark,leaves]:ob.location=(x,y,z);ob['tree_group']=label;ob['species_confidence']='杉类形态参考，具体物种未鉴定';ob['placement_confidence']='inferred from southern planting strip'
    report.append(dict(name=label,x=x,y=y,z=z,height=h,crown_radius=r,type='inferred mature conifer',leaves=n,seed=seed));print('CONIFER',label,n,flush=True)
# Terrain and upward hardscape facets for new trees, excluding foliage and main lawn.
gv=[];gf=[];ov=[];of=[]
plant_ids={'VEGETATION','VEGETATION_PILOT','VEGETATION_V2','E_TREES','E_PLANTING','GARDEN_VEGETATION_V3','TREE_CANOPY_V6'}
for ob in S.objects:
    if ob.type!='MESH' or ob.hide_render or ob.get('feature_id') in plant_ids or len(ob.data.polygons)>180000:continue
    if any(k in ob.name.lower() for k in ['hedge','shrub','leaf','leaves','vine','grass tips','flower']):continue
    ob.data.calc_loop_triangles()
    for tri in ob.data.loop_triangles:
        a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices]
        if (b-a).cross(c-a).z<1e-7:continue
        mat=ob.data.materials[tri.material_index] if ob.data.materials else None
        ground=mat and any(k in mat.name.lower() for k in ['garden_grass','soil']) and ob.get('feature_id') not in {'LAWN','BUILDING_ENTRY'}
        vv,ff=(gv,gf) if ground else (ov,of);i=len(vv);vv.extend([a,b,c]);ff.append((i,i+1,i+2))
terrain=BVHTree.FromPolygons(gv,gf,all_triangles=True);hard=BVHTree.FromPolygons(ov,of,all_triangles=True)
def new_ground(x,y,clearance=.7):
    p=terrain.ray_cast(Vector((x,y,35)),Vector((0,0,-1)))[0]
    if p is None:return None
    for a in np.arange(8)*math.tau/8:
        q=hard.ray_cast(Vector((x+clearance*math.cos(a),y+clearance*math.sin(a),35)),Vector((0,0,-1)))[0]
        if q is not None and q.z>p.z-.025:return None
    q=hard.ray_cast(Vector((x,y,35)),Vector((0,0,-1)))[0]
    if q is not None and q.z>p.z-.025:return None
    root_checks.append(dict(x=x,y=y,z=p.z,clearance=clearance,passed=True));return p.z
for i,t in enumerate(source_trees):
    opened=t['type']=='open deciduous';h=t['height']*(1.05 if t['x']<0 else (1.14 if not opened else 1));r=t['crown_radius']*(1.02 if t['x']<0 else (1.03 if not opened else 1))
    broad_tree('V6 '+t['name'],t['x'],t['y'],t['z'],h,r,6100+i,opened)
for i,(old,x,y,z) in enumerate(road_positions):
    broad_tree('V6 south avenue %02d'%i,x,y,z,15.5+(i%4)*1.1,5.4+(i%3)*.35,6200+i,plane=True)
# Gaps under high crowns filled from photos; do not plant central LAWN.
added=[];rejected=[]
candidates=[] # User review: no extra broadleaf background trees at this stage.
for i,(x,y,h,r) in enumerate(candidates):
    if min(math.hypot(x-t['x'],y-t['y']) for t in report)<3.5:rejected.append([x,y,'existing trunk spacing']);continue
    z=new_ground(x,y,.75)
    if z is None:rejected.append([x,y,'ground or hardscape clearance']);continue
    broad_tree('V6 garden background %02d'%i,x,y,z,h,r,6300+i);added.append(report[-1]['name'])
for i,(x,y,h,r) in enumerate([(-59,9.4,21,3.8),(-20,9.4,19.5,3.3),(6,9.4,21.5,3.5),(26,9.4,20,3.6),(58,9.4,21,3.4),(87,10.5,20,3.3)]):
    z=new_ground(x,y,.75)
    if z is None:rejected.append([x,y,'conifer ground or clearance']);continue
    conifer_tree('V6 south conifer %02d'%i,x,y,z,h,r,6400+i);added.append(report[-1]['name'])
def camera(name,loc,target,lens=27):
    d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);C.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=2500;ob['camera_confidence']='Approximate IMG_4597, not solved';return ob
camera('V6 south photo4597',(59,14.5,1.75),(-20,14.5,3.4),29)
camera('V6 south crown elevation',(18,-40,9),(18,9,10),30)
after=snapshot();protected={n:v for n,v in before.items() if n not in whitelist}
errors=[n for n,v in protected.items() if after.get(n)!=v];assert not errors,errors
write(O/'expected-snapshot.json',after)
new_triangles=sum(sum(len(p.vertices)-2 for p in ob.data.polygons) for ob in C.objects if ob.type=='MESH')
R=dict(source=str(BASE),source_sha256=sha(BASE),scene=str(OUT),removed_tree_objects=whitelist,protected_meshes=len(protected),protected_objects_match=True,trees=report,added_trees=added,rejected_positions=rejected,new_root_checks=root_checks,old_replaced_tree_triangles=old_triangles,new_tree_triangles=new_triangles,tree_triangle_change_percent=round((new_triangles/old_triangles-1)*100,2),scope='Garden tree crowns and southern mixed avenue only; all other v5 meshes preserved',dimensions='Tree sizes, exact new positions and species inferred from appearance; not surveyed')
S['tree_canopy_v6']='Continuous irregular crowns, layered high backdrop, broadleaf and inferred conifer southern avenue; v5 non-tree objects untouched'
bpy.context.preferences.filepaths.save_version=0;S.camera=bpy.data.objects['FINAL landscape']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
R['scene_sha256']=sha(OUT);R['scene_bytes']=OUT.stat().st_size;write(O/'version-manifest.json',R)
assert sha(BASE)==R['source_sha256'];print('V6_SAVED',len(report),'trees',new_triangles,'triangles',OUT.stat().st_size,flush=True)
