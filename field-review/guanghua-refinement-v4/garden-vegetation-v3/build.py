"""Bounded garden appearance edit. Keeps paths, planter stonework and front beds."""
import bpy, math, random, json, hashlib, sys, time
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend'
OUT=O/'garden-vegetation-v3.blend'
DIAG='--final' not in sys.argv
SECOND='--second' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(BASE))
S=bpy.context.scene; rng=random.Random(93083)
source_hash=hashlib.sha256(BASE.read_bytes()).hexdigest()
C=bpy.data.collections.new('12_Garden vegetation v3');S.collection.children.link(C)

def fingerprint(ob):
    h=hashlib.sha256()
    for group,key,n,dtype in [(ob.data.vertices,'co',3,np.float32),(ob.data.loops,'vertex_index',1,np.int32),(ob.data.polygons,'material_index',1,np.int32)]:
        a=np.empty(len(group)*n,dtype);group.foreach_get(key,a);h.update(a.tobytes())
    h.update(str([list(r) for r in ob.matrix_world]).encode())
    h.update(str([m.name if m else None for m in ob.data.materials]).encode())
    h.update(str([(m.name,m.type) for m in ob.modifiers]).encode())
    for uv in ob.data.uv_layers:
        a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    return h.hexdigest()
baseline={ob.name:fingerprint(ob) for ob in S.objects if ob.type=='MESH'}
baseline_visibility={ob.name:ob.hide_render for ob in S.objects if ob.type=='MESH'}
changed=[];hidden=[];B={};leaf_count=0

palette=[('deep olive',(.060,.120,.022)),('olive',(.115,.215,.039)),('grey green',(.135,.195,.078)),('fresh green',(.195,.325,.050)),('leaf underside',(.19,.265,.090)),('burgundy',(.125,.035,.046)),('bronze',(.215,.092,.055)),('autumn',(.34,.225,.065))]
M=[]
for name,color in palette:
    m=bpy.data.materials.new('GV3 '+name);m.use_nodes=True;m.diffuse_color=(*color,1)
    nt=m.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.49;p.inputs['Specular IOR Level'].default_value=.28
    p.inputs['Base Color'].default_value=(*color,1);p.inputs['Subsurface Weight'].default_value=.045
    uv=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(uv.outputs['UV'],sep.inputs[0])
    sub=nt.nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=.5;nt.links.new(sep.outputs['Y'],sub.inputs[0])
    ab=nt.nodes.new('ShaderNodeMath');ab.operation='ABSOLUTE';nt.links.new(sub.outputs[0],ab.inputs[0])
    vein=nt.nodes.new('ShaderNodeMapRange');vein.inputs['From Min'].default_value=0;vein.inputs['From Max'].default_value=.06;vein.inputs['To Min'].default_value=1.14;vein.inputs['To Max'].default_value=.96
    nt.links.new(ab.outputs[0],vein.inputs[0]);mix=nt.nodes.new('ShaderNodeVectorMath');mix.operation='SCALE';mix.inputs[0].default_value=color;nt.links.new(vein.outputs[0],mix.inputs[3]);nt.links.new(mix.outputs[0],p.inputs['Base Color'])
    M.append(m)
bark=bpy.data.materials.new('GV3 fissured grey bark');bark.use_nodes=True;bark.diffuse_color=(.12,.105,.080,1)
nt=bark.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.91
tex=nt.nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=17;tex.inputs['Detail'].default_value=4
co=nt.nodes.new('ShaderNodeTexCoord');scale=nt.nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(3,3,.55);nt.links.new(co.outputs['Generated'],scale.inputs[0]);nt.links.new(scale.outputs[0],tex.inputs[0])
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.031,.025,.018,1);ramp.color_ramp.elements[1].color=(.23,.212,.175,1);nt.links.new(tex.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.48;bump.inputs['Distance'].default_value=.035;nt.links.new(tex.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal']);M.append(bark)

def add(name,vs,fs,mi,uvs=None):
    v,f,m,u=B.setdefault(name,([],[],[],[]));k=len(v);v.extend([tuple(x) for x in vs]);f.extend([tuple(k+i for i in face) for face in fs]);m.extend([mi]*len(fs));u.extend(uvs if uvs else [(0,0)]*len(vs))

def leaf(name,p,length=.09,mi=1,angle=None,tilt=None,width=.39):
    global leaf_count
    p=Vector(p);a=rng.uniform(0,math.tau) if angle is None else angle
    t=rng.uniform(-.65,.65) if tilt is None else tilt
    u=Vector((math.cos(a),math.sin(a),t)).normalized()*length
    w=u.cross(Vector((0,0,1))).normalized()*length*width
    # Curved oval blade with taper and a shallow raised midrib.
    lift=Vector((0,0,length*.12))
    vs=[p-u,p-u*.62-w*.66,p-w,p+u*.62-w*.66,p+u,p+u*.62+w*.66,p+w,p-u*.62+w*.66,p+lift]
    uv=[(0,.5),(.19,.17),(.5,0),(.81,.17),(1,.5),(.81,.83),(.5,1),(.19,.83),(.5,.5)]
    add(name,vs,[(i,(i+1)%8,8) for i in range(8)],mi,uv);leaf_count+=1

def tube(name,points,r0,r1,mi=8):
    pts=[Vector(p) for p in points];vs=[];n=8
    for j,p in enumerate(pts):
        d=(pts[min(j+1,len(pts)-1)]-pts[max(0,j-1)]).normalized();u=d.cross(Vector((0,0,1)))
        if u.length<.01:u=d.cross(Vector((0,1,0)))
        u.normalize();v=d.cross(u);r=r0+(r1-r0)*j/(len(pts)-1)
        for i in range(n):
            a=i*math.tau/n;rr=r*(1+.055*math.sin(i*2.3+j*1.7));vs.append(p+rr*(math.cos(a)*u+math.sin(a)*v))
    fs=[tuple(range(n-1,-1,-1)),tuple(range((len(pts)-1)*n,len(pts)*n))]
    fs += [(j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i) for j in range(len(pts)-1) for i in range(n)]
    add(name,vs,fs,mi)

def flush():
    result=[]
    for name,(v,f,mi,uvs) in B.items():
        me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update()
        for m in M:me.materials.append(m)
        for p,idx in zip(me.polygons,mi):p.material_index=idx;p.use_smooth=True
        uv=me.uv_layers.new(name='GV3 leaf UV')
        a=np.array([uvs[l.vertex_index] for l in me.loops],dtype=np.float32);uv.data.foreach_get('uv',a.ravel())
        ob=bpy.data.objects.new(name,me);C.objects.link(ob);ob['feature_id']='GARDEN_VEGETATION_V3';ob['source_photos']=[4377,4384,4390,4547,4568,4574,4582];ob['geometry_confidence']='inferred; appearance guided by photos; additional understory authorized'
        result.append(ob.name)
    B.clear();return result

def hide(ob):
    if not ob.hide_render:ob.hide_render=True;ob.hide_set(True);hidden.append(ob.name)

def cam(name,loc,target,ortho=None,lens=28):
    d=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,d);C.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=2500
    if ortho:d.type='ORTHO';d.ortho_scale=ortho
    ob['camera_confidence']='Approximate photo viewpoint, not measured';return ob

views={
    'east-exit':bpy.data.objects['SHAPE exit approximate'],
    'east-garden':bpy.data.objects['04-east-garden'],
    'west-garden':bpy.data.objects['03-west-garden'],
    'west-platform':cam('GV3 west platform photo 4390',(-55.5,43.1,2.85),(-64,59,4.6),lens=26),
    'east-understory':cam('GV3 east understory photo 4582',(75.5,58.5,1.9),(84,69,4.8),lens=27),
    'overall':bpy.data.objects['FINAL landscape'],
}

def render(label,cam,width,samples):
    S.camera=cam;S.render.engine='CYCLES';S.cycles.samples=samples;S.cycles.use_denoising=True;S.cycles.device='CPU';S.render.threads_mode='FIXED';S.render.threads=8
    S.render.resolution_x=width;S.render.resolution_y=round(width*.75);S.render.resolution_percentage=100
    S.render.image_settings.file_format='PNG';S.render.filepath=str(O/(label+'.png'))
    S.render.film_transparent=False;S.view_settings.view_transform='AgX';S.view_settings.exposure=.65
    start=time.time();bpy.ops.render.render(write_still=True);print('VIEW_DONE',label,round(time.time()-start,1),flush=True)

if DIAG and not SECOND:
    for key in ['east-exit','west-platform']:
        render('before-'+key,views[key],900,12)

# Ground and hardscape queries only constrain the new planting. No source edit.
gv=[];gf=[];ov=[];of=[]
plant_ids={'VEGETATION','VEGETATION_PILOT','VEGETATION_V2','E_TREES','E_PLANTING'}
for ob in list(S.objects):
    if ob.type!='MESH' or ob.hide_render or ob.get('feature_id') in plant_ids:continue
    if any(k in ob.name.lower() for k in ['hedge','shrub','planting','leaves','leaf-clusters','vine']):continue
    ob.data.calc_loop_triangles()
    for tri in ob.data.loop_triangles:
        ma=ob.data.materials[tri.material_index] if ob.data.materials else None
        isground=ma and any(k in ma.name.lower() for k in ['garden_grass','soil']) and ob.get('feature_id')!='LAWN'
        a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices]
        if (b-a).cross(c-a).z<1e-7:continue
        v,f=(gv,gf) if isground else (ov,of);k=len(v);v.extend([a,b,c]);f.append((k,k+1,k+2))
terrain=BVHTree.FromPolygons(gv,gf,all_triangles=True);obstacles=BVHTree.FromPolygons(ov,of,all_triangles=True)
print('GROUND_READY',len(gf),len(of),flush=True)

def garden(x,y):return 15<y<91 and (-79<x<-29 or 67.4<x<102)
def ground(x,y,clearance=0):
    if not garden(x,y):return None
    p,n,i,d=terrain.ray_cast(Vector((x,y,35)),Vector((0,0,-1)))
    if p is None:return None
    for dx,dy in [(0,0)]+[(clearance*math.cos(i*math.pi/4),clearance*math.sin(i*math.pi/4)) for i in range(8)] if clearance else [(0,0)]:
        hit=obstacles.ray_cast(Vector((x+dx,y+dy,35)),Vector((0,0,-1)))[0]
        if hit is not None and hit.z>p.z-.035:return None
    return p.z

trees=[]
def tree(name,x,y,z,h,radius,evergreen=True,density=1):
    p=Vector((x,y,z));r=h*.027 if evergreen else h*.032
    trunk=[p,p+Vector((-.12,.10,h*.13)),p+Vector((.20,-.10,h*.29)),p+Vector((.42,.13,h*.43)),p+Vector((.18,.3,h*.61))]
    tube(name+' bark',trunk,r,r*.26)
    # Buttress roots remain in soil; main limbs emerge at different heights.
    for k in range(5):
        a=rng.uniform(0,math.tau);q=p+Vector((math.cos(a)*r*2.5,math.sin(a)*r*2.5,.015));tube(name+' bark',[q,p+Vector((0,0,.28)),trunk[1]],r*.22,r*.15)
    clusters=[]
    for j in range(8 if evergreen else 7):
        a=j*2.399+rng.uniform(-.45,.45);start=trunk[rng.choice([2,3,3,4])]
        end=p+Vector((math.cos(a)*radius*rng.uniform(.55,1),math.sin(a)*radius*rng.uniform(.55,1),h*rng.uniform(.62,.94)))
        mid=start.lerp(end,.48)+Vector((rng.uniform(-.3,.3),rng.uniform(-.3,.3),-.3))
        tube(name+' bark',[start,mid,end],r*rng.uniform(.30,.50),r*.04)
        for k in range(5):
            s=mid.lerp(end,.20+k*.17);aa=a+rng.uniform(-1.8,1.8)
            tip=s+Vector((math.cos(aa)*radius*rng.uniform(.20,.36),math.sin(aa)*radius*rng.uniform(.20,.36),h*rng.uniform(.025,.13)))
            knee=s.lerp(tip,.5)+Vector((0,0,rng.uniform(-.15,.15)))
            tube(name+' bark',[s,knee,tip],r*.067,r*.011)
            # Irregular crown lobes attach to twigs, never an enclosing sphere.
            clusters.append((tip,radius*rng.uniform(.17,.25),h*rng.uniform(.07,.13)))
            for t in range(4):
                origin=s.lerp(tip,.25+t*.22);dest=origin+Vector((rng.uniform(-.65,.65),rng.uniform(-.65,.65),rng.uniform(-.1,.5)))
                tube(name+' bark',[origin,dest],r*.014,r*.003)
                for _ in range(round((24 if evergreen else 12)*density)):
                    c=origin.lerp(dest,rng.random())+Vector((rng.gauss(0,.12),rng.gauss(0,.12),rng.gauss(0,.10)))
                    leaf(name+' foliage',c,rng.uniform(.055,.105),rng.choices([0,1,2,3,4,7],[20,40,18,12,9,1] if evergreen else [10,31,30,8,14,7])[0])
    for tip,spread,height in clusters:
        for _ in range(round((1380 if evergreen else 135)*density)):
            u=rng.uniform(-1,1);a=rng.uniform(0,math.tau);rr=math.sqrt(1-u*u)*rng.random()**.22
            c=tip+Vector((math.cos(a)*spread*rr,math.sin(a)*spread*rr,height*u))
            leaf(name+' foliage',c,rng.uniform(.065,.112) if evergreen else rng.uniform(.053,.100),rng.choices([0,1,2,3,4,7],[19,42,15,15,8,1] if evergreen else [14,30,30,7,12,7])[0])
    if evergreen:
        # A continuous interior crown links outer twig clusters into mature shade.
        for j in range(13):
            a=rng.uniform(0,math.tau);rr=radius*rng.uniform(.12,.62)
            centre=p+Vector((math.cos(a)*rr,math.sin(a)*rr,h*rng.uniform(.64,.91)))
            tube(name+' bark',[trunk[3],trunk[3].lerp(centre,.55),centre],r*.065,r*.012)
            spread=radius*rng.uniform(.25,.35)
            for _ in range(round(720*density)):
                u=rng.uniform(-1,1);aa=rng.uniform(0,math.tau);rad=math.sqrt(1-u*u)*rng.random()**.28
                c=centre+Vector((math.cos(aa)*spread*rad,math.sin(aa)*spread*rad,spread*.8*u))
                leaf(name+' foliage',c,rng.uniform(.063,.109),rng.choices([0,1,2,3,4],[23,40,17,14,6])[0])
    trees.append(dict(name=name,x=x,y=y,z=z,height=h,crown_radius=radius,type='dense evergreen' if evergreen else 'open deciduous'))

old_trees=[ob for ob in list(S.objects) if ob.name.startswith('V2 tree ') and 'branches' in ob.name and garden(ob.location.x,ob.location.y)]
for i,ob in enumerate(old_trees):
    x,y,z=ob.location;west=x<0;h=8*ob.scale.z*(1.38 if west else 1.15)
    tree(('West' if west else 'East')+' mature %02d'%i,x,y,z,h,(4.9 if west else 4.1)*ob.scale.z,west or y>65,1 if west else .75)
    hide(ob);hide(bpy.data.objects[ob.name.replace('branches','leaves')]);flush();print('TREE_DONE',i,flush=True)
pilot=[(68.6,41.5,4.8,2.4),(67.9,46.5,7.1,4.2),(76,50.9,7.2,4.3),(80.8,59.5,7.3,3.2),(78.4,35.8,6.5,3)]
for i,(x,y,h,r) in enumerate(pilot):
    old=bpy.data.objects[next(n for n in baseline if n.startswith('V0'+str(i+1)) and 'branches' in n)]
    pts=[old.matrix_world@Vector(p) for p in old.bound_box];z=min(p.z for p in pts)+.025
    tree('East spreading %02d'%i,x,y,z,h*1.22,r*1.10,False,.7)
    hide(old);hide(bpy.data.objects[old.name.replace('branches','leaves')]);flush()
for i,(x,y) in enumerate([(-75,37),(-76,61),(-53,74),(-69,80),(87,65),(90,40)]):
    z=ground(x,y,.5)
    if z is not None:tree('Garden backdrop %02d'%i,x,y,z,rng.uniform(10.5,13.4),rng.uniform(4.5,5.8),True,.85);flush()

# Replace only garden leaf surfaces. All stonework and planter boundaries persist.
hedges=[ob for ob in list(S.objects) if ob.type=='MESH' and not ob.hide_render and ob.get('feature_id') in ['WTERR','ETERR','ESKY','EOPEN','EOPEN_S','WOPEN','WOPEN_S'] and any(k in ob.name.lower() for k in ['hedge','planted-shrubs']) and not any(k in ob.name.lower() for k in ['leaves','leaf-masses','leaf-clusters'])]
for ob in hedges:
    red='red' in ob.name.lower() or 'bronze' in ob.name.lower()
    ob.data=ob.data.copy();mat=bpy.data.materials.new('GV3 clipped core '+ob.name);mat.use_nodes=True
    p=mat.node_tree.nodes['Principled BSDF'];p.inputs['Base Color'].default_value=(.048,.014,.023,1) if red else (.033,.061,.012,1);p.inputs['Roughness'].default_value=.86
    ob.data.materials.clear();ob.data.materials.append(mat);changed.append(ob.name);ob.data.calc_loop_triangles()
    name=('West' if ob.get('feature_id').startswith('W') else 'East')+' hedge '+ob.name
    for tri in ob.data.loop_triangles:
        a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices];normal=(b-a).cross(c-a);area=normal.length*.5
        if area<1e-8:continue
        normal.normalize()
        if normal.z<-.25:continue
        for _ in range(round(area*(900 if red else 740))):
            u=math.sqrt(rng.random());v=rng.random();pos=a*(1-u)+b*u*(1-v)+c*u*v+normal*rng.uniform(.018,.060)
            mi=rng.choices([5,6,1,4],[63,22,10,5])[0] if red else rng.choices([0,1,2,3,4],[17,38,11,28,6])[0]
            leaf(name,pos,rng.uniform(.025,.058),mi,width=rng.uniform(.35,.57))
    flush()
for ob in list(S.objects):
    if ob.name in baseline and (ob.name in ['H ESKY textured leaves','H ETERR textured leaves','H EOPEN_S textured leaves','V2 leaves WTERR','V2 leaves WOPEN','V2 leaves WOPEN_S','V2 leaves EOPEN'] or (ob.get('feature_id') in ['WTERR','ETERR','EOPEN','EOPEN_S','WOPEN','WOPEN_S'] and any(k in ob.name.lower() for k in ['leaf-masses','hedge-leaf-clusters','back-hedge-leaves']))):hide(ob)
print('HEDGES_DONE',len(hedges),flush=True)

# Reusable irregular bushes have fine leaf surfaces, inner twigs and varied habit.
proto=[]
def bush_proto(k,broad=False,red=False):
    name='GV3 shrub prototype '+str(k)
    for j in range(11):
        a=j*2.399;tip=Vector((.63*math.cos(a),.58*math.sin(a),rng.uniform(.65,1.10)))
        tube(name+' twigs',[(0,0,.04),tip*.50,tip],.020,.0025)
    for _ in range(4100 if broad else 3300):
        u=rng.uniform(-1,1);a=rng.uniform(0,math.tau);rr=math.sqrt(1-u*u)*rng.uniform(.72,1)**.4
        p=Vector((math.cos(a)*rr,math.sin(a)*rr*.87,.64+.59*u))
        p.x+=.055*math.sin(a*5+u*7);p.y+=.06*math.cos(a*4-u*6)
        mi=rng.choices([5,6,1,4],[64,17,14,5])[0] if red else rng.choices([0,1,2,3,4],[28,41,12,14,5])[0]
        leaf(name+' foliage',p,rng.uniform(.073,.12) if broad else rng.uniform(.035,.070),mi,width=.32 if broad else .51)
    names=flush();objects=[bpy.data.objects[n] for n in names];data=[o.data for o in objects]
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
    return data
for k in range(6):proto.append(bush_proto(k,k in [0,3],k in [2,5]))
shrubs=[]
def shrub(x,y,z,rx,ry,h,kind):
    n=len(shrubs);a=rng.uniform(0,math.tau)
    for me in proto[kind]:
        ob=bpy.data.objects.new('GV3 shrub %03d '%n+me.name,me);C.objects.link(ob);ob.location=(x,y,z);ob.scale=(rx,ry,h/1.23);ob.rotation_euler.z=a
        ob['feature_id']='GARDEN_VEGETATION_V3';ob['source_photos']=[4384,4390,4568,4582];ob['geometry_confidence']='Additional understory per user; position and plant count inferred'
    shrubs.append(dict(x=x,y=y,z=z,width=2*rx,height=h,kind=kind))

pockets=[(-69,28,9,11),(-55,26,8,7),(-41,28,5,8),(-41,55,5,13),(-43,77,6,9),(-66,79,10,7),(-77,57,2.5,17),(77,27,7,9),(81,66,7,11),(89,78,7,9),(77,41,5,7),(99,61,3,16),(73,79,4,7),(69.3,38.3,2.5,5)]
for west in [True,False]:
    xmin,xmax=(-78,-30) if west else (68,101)
    for ix in range(round((xmax-xmin)/2.25)):
        for iy in range(33):
            x=xmin+ix*2.25+rng.uniform(-.55,.55);y=16+iy*2.25+rng.uniform(-.55,.55)
            d=min(((x-cx)/rx)**2+((y-cy)/ry)**2 for cx,cy,rx,ry in pockets if (cx<0)==west)
            if d>1 or rng.random()<.13:continue
            rx=rng.uniform(.86,1.48);ry=rx*rng.uniform(.80,1.12)
            z=ground(x,y,max(rx,ry)+.35)
            if z is None:continue
            h=rng.uniform(.65,1.52);kind=rng.choices(range(6),[24,27,10,17,15,7])[0]
            if d<.35:h*=1.15
            shrub(x,y,z,rx,ry,h,kind)
# Nearby coarse ball shrubs remain hidden only when an actual finer replacement fits.
for ob in list(S.objects):
    if ob.name in baseline and (ob.name.startswith('S0') or ob.name in ['E_PLANTING__clipped-shrub__leaf-green','V2 leaves E_PLANTING']):hide(ob)
for x,y,rx,ry,h in [(77.6,44.9,.80,.85,1.12),(76.2,42.3,.78,.87,1.05),(78,50.4,.90,.8,1.18),(68.6,42.7,.77,.74,.95)]:
    z=ground(x,y,.4)
    if z is not None:shrub(x,y,z,rx,ry,h,0)
# Replace the remaining isolated low-poly shrub balls at their existing centres.
for name in ['VEGETATION__clipped-shrubs__FIN_hedge','E_PLANTING__clipped-shrub__leaf-green']:
    ob=bpy.data.objects[name];neighbours=[set() for _ in ob.data.vertices]
    for e in ob.data.edges:a,b=e.vertices;neighbours[a].add(b);neighbours[b].add(a)
    seen=set()
    for start in range(len(neighbours)):
        if start in seen:continue
        stack=[start];seen.add(start);ids=[]
        while stack:
            i=stack.pop();ids.append(i)
            for j in neighbours[i]:
                if j not in seen:seen.add(j);stack.append(j)
        pts=[ob.matrix_world@ob.data.vertices[i].co for i in ids]
        lo=[min(p[k] for p in pts) for k in range(3)];hi=[max(p[k] for p in pts) for k in range(3)]
        x=(lo[0]+hi[0])/2;y=(lo[1]+hi[1])/2
        if garden(x,y):
            z=ground(x,y) or 0;shrub(x,y,z,(hi[0]-lo[0])*.5,(hi[1]-lo[1])*.5,hi[2]-z,rng.choice([0,1,4]))
    hide(ob)
print('UNDERSTORY_DONE',len(shrubs),flush=True)

# Ground finish is an overlay restricted to exposed garden soil; main lawn fixed.
soil=bpy.data.materials.new('GV3 fine mixed garden turf');soil.use_nodes=True
nt=soil.node_tree;p=nt.nodes['Principled BSDF'];p.inputs['Roughness'].default_value=.96
co=nt.nodes.new('ShaderNodeTexCoord');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1.3;noise.inputs['Detail'].default_value=3;nt.links.new(co.outputs['Object'],noise.inputs[0])
ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[0].color=(.088,.099,.035,1);ramp.color_ramp.elements[1].position=.78;ramp.color_ramp.elements[1].color=(.225,.279,.065,1)
nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],p.inputs['Base Color'])
fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=150;fine.inputs['Detail'].default_value=2;nt.links.new(co.outputs['Object'],fine.inputs[0]);bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.35;bump.inputs['Distance'].default_value=.018;nt.links.new(fine.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs[0],p.inputs['Normal'])
# Small terrain triangles follow inherited heights without altering any old mesh.
vv=[];ff=[]
for west in [True,False]:
    xmin,xmax=(-78.5,-29.5) if west else (67.6,101.5)
    for x in np.arange(xmin,xmax,.8):
        for y in np.arange(15.5,90,.8):
            pts=[(x,y),(x+.8,y),(x+.8,y+.8),(x,y+.8)]
            zs=[ground(a,b) for a,b in pts]
            if any(z is None for z in zs) or max(zs)-min(zs)>.25:continue
            # Extra centre checks avoid spilling across narrow paths.
            if ground(x+.4,y+.4,.35) is None:continue
            n=len(vv);vv.extend([(a,b,z+.0025) for (a,b),z in zip(pts,zs)]);ff.append((n,n+1,n+2,n+3))
me=bpy.data.meshes.new('GV3 garden turf surface');me.from_pydata(vv,[],ff);me.materials.append(soil)
ob=bpy.data.objects.new(me.name,me);C.objects.link(ob);ob['feature_id']='GARDEN_VEGETATION_V3';ob['scope']='Exposed E/W garden ground overlay; no main lawn or path edits'
ob.hide_render=True;ob.hide_set(True) # Preserve smooth inherited ground; reject patch seams in diagnostic.
# Small clumps of narrow blades and sparse natural leaf litter at shrub margins.
for k in range(4800):
    sh=rng.choice(shrubs);a=rng.uniform(0,math.tau);r=rng.uniform(.6,1.8);x=sh['x']+r*math.cos(a);y=sh['y']+r*math.sin(a);z=ground(x,y,.08)
    if z is None:continue
    for j in range(5):
        a=rng.uniform(0,math.tau);h=rng.uniform(.035,.11);dx=math.cos(a)*h*.45;dy=math.sin(a)*h*.45;w=.003
        add('GV3 groundcover blades',[(x-w,y,z+.004),(x+w,y,z+.004),(x+dx+w*.3,y+dy,z+h*.65),(x+dx,y+dy,z+h)],[(0,1,2),(0,2,3)],rng.choice([0,1,1,3]))
    if k%5==0:leaf('GV3 scattered fallen leaves',(x,y,z+.008),rng.uniform(.025,.055),rng.choice([6,7]),tilt=.015,width=.47)
flush()

assert all(fingerprint(bpy.data.objects[n])==v for n,v in baseline.items() if n not in changed)
assert all(bpy.data.objects[n].hide_render==v for n,v in baseline_visibility.items() if n not in hidden)
assert hashlib.sha256(BASE.read_bytes()).hexdigest()==source_hash
S['garden_vegetation_v3']='Dense layered shrubs, fine oval leaves, irregular mature trees, garden-only ground cover. Paths and front planters retained.'
S.camera=views['east-exit'];S.render.resolution_x=1600;S.render.resolution_y=1200
bpy.context.preferences.filepaths.use_file_compression=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
report=dict(source=str(BASE),source_sha256=source_hash,source_unchanged=True,protected_meshes=len(baseline)-len(changed),protected_mesh_geometry_uv_materials_unchanged=True,modified_foliage_materials=changed,hidden_old_garden_plants=hidden,trees=trees,shrubs=shrubs,generated_leaf_count=leaf_count,scope='East and west gardens only. No roads, front planter geometry/materials, main lawn or buildings edited.',dimensions='Plant positions and sizes inferred from appearance; extra understory density requested by user',render_views=[])
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('CHECKPOINT_SAVED',len(trees),len(shrubs),leaf_count,flush=True)
for key in (['east-exit','west-platform','west-garden','east-garden'] if DIAG else list(views)):
    render(('diagnostic2-' if SECOND else 'diagnostic-' if DIAG else 'final-')+key,views[key],1000 if DIAG else 1800,16 if DIAG else 36)
    report['render_views'].append(key);(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('GARDEN_RENDER_COMPLETE',flush=True)
