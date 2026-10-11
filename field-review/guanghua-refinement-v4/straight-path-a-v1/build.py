"""Bounded photo-referenced edit. Run with Blender 4.4; see edit-contract.md."""
import sys, json, math, hashlib
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-refinement-v4/forecourt-refined-v4.blend'
OUT=O/'east-straight-path-a-v1.blend'
sys.path.insert(0,str(O.parent/'forecourt-refinement-v4'))
import common as C
C.O=O
X0=63.50211715698242; X1=67.10211944580078
Y0=14.; Y1=77.85448455810547
BAND=.33; XA=63.83211898803711; XB=66.7721176147461
COUNT=99; PITCH=(Y1-Y0)/COUNT
BREAKS=[Y0,15.699999809265137,16.35,Y1-2*PITCH,Y1]
ZB=-.035; DEPTH=.018
COL='11_A east straight path'

def ztop(y):
    if y<=BREAKS[1]:return .05
    if y<BREAKS[2]:return .05-.005*(y-BREAKS[1])/(BREAKS[2]-BREAKS[1])
    if y<=BREAKS[3]:return .045
    return .045-.01*(y-BREAKS[3])/(Y1-BREAKS[3])

def fingerprint(ob):
    h=hashlib.sha256()
    for attr,prop,n in [(ob.data.vertices,'co',3),(ob.data.loops,'vertex_index',1),(ob.data.polygons,'material_index',1)]:
        a=np.empty(len(attr)*n,np.float32 if prop=='co' else np.int32)
        attr.foreach_get(prop,a);h.update(a.tobytes())
    h.update(str([tuple(p.vertices) for p in ob.data.polygons]).encode())
    h.update(str([list(r) for r in ob.matrix_world]).encode())
    h.update(str([m.name if m else None for m in ob.data.materials]).encode())
    h.update(str([(m.name,m.type) for m in ob.modifiers]).encode())
    for uv in ob.data.uv_layers:
        a=np.empty(len(uv.data)*2,np.float32);uv.data.foreach_get('uv',a);h.update(a.tobytes())
    return h.hexdigest()

def snapshots():return {o.name:fingerprint(o) for o in bpy.context.scene.objects if o.type=='MESH'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def tag(ob,kind):
    ob['feature_id']='E_WALK';ob['source_photos']=[4492,4493]
    ob['component']=kind;ob['visible_relationship']='confirmed / 照片可见关系确认'
    ob['dimension_status']='推定 / photographic estimate, not measured'
    ob['geometry_confidence']='inferred'
    ob['groove_depth_status']='推定' if kind=='arc border' else 'not applicable'
    ob['groove_function_status']='推定；用途未确认，不指定排水功能' if kind=='arc border' else 'not applicable'
    target=C.collection(COL)
    for coll in list(ob.users_collection):coll.objects.unlink(ob)
    target.objects.link(ob)
    return ob

def stone(name,color):
    m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
    n=m.node_tree.nodes;l=m.node_tree.links;p=n['Principled BSDF']
    p.inputs['Roughness'].default_value=.85
    tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=150
    noise.inputs['Detail'].default_value=2.1;noise.inputs['Roughness'].default_value=.7
    l.new(tc.outputs['Object'],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.22
    ramp.color_ramp.elements[0].color=(*(v*.57 for v in color),1)
    ramp.color_ramp.elements[1].position=.79;ramp.color_ramp.elements[1].color=(*(min(.8,v*1.22) for v in color),1)
    l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],p.inputs['Base Color'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.0008
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],p.inputs['Normal'])
    m['source_photos']=[4492,4493];m['scale_status']='推定';return m

def surface_solid(name,x0,x1,ys,heights,mat):
    """Closed rectangular surface with shared row vertices, exact endpoint levels."""
    vs=[]
    for y,h in zip(ys,heights):vs.extend([(x0,y,ZB),(x1,y,ZB),(x1,y,h),(x0,y,h)])
    fs=[(3,2,1,0),tuple(range(len(vs)-4,len(vs)))]
    for i in range(len(ys)-1):
        for k in range(4):fs.append((4*i+k,4*i+(k+1)%4,4*(i+1)+(k+1)%4,4*(i+1)+k))
    return tag(C.mesh(name,vs,fs,mat,'E_WALK',[4492,4493]),'paving bed')

def append_tile(vs,fs,slots,x0,x1,ya,yb,slot):
    ys=[ya]+[y for y in BREAKS if ya+1e-7<y<yb-1e-7]+[yb]
    start=len(vs)
    for y in ys:vs.extend([(x0,y,ztop(y)-.0025),(x1,y,ztop(y)-.0025),(x1,y,ztop(y)),(x0,y,ztop(y))])
    faces=[(start+3,start+2,start+1,start),tuple(range(len(vs)-4,len(vs)))]
    for i in range(len(ys)-1):
        for k in range(4):faces.append((start+4*i+k,start+4*i+(k+1)%4,start+4*(i+1)+(k+1)%4,start+4*(i+1)+k))
    fs.extend(faces);slots.extend([slot]*len(faces))

def create_paving():
    mats=[stone('A rectangular granite tone %02d'%i,(.37+.011*i,.359+.011*i,.341+.01*i)) for i in range(7)]
    grout=stone('A filled narrow stone joints',(.185,.177,.165))
    bed=surface_solid('E_WALK continuous filled paving bed',XA,XB,BREAKS,[ztop(y)-.0025 for y in BREAKS],grout)
    vs=[];fs=[];slots=[];rows=213;rowpitch=(Y1-Y0)/rows;tilew=(XB-XA)/5;gap=.004
    for row in range(rows):
        ya=Y0+row*rowpitch+(gap/2 if row else 0)
        yb=Y0+(row+1)*rowpitch-(gap/2 if row<rows-1 else 0)
        phase=tilew/2*(row%2)
        edges=[XA]+[XA+phase+k*tilew for k in range(7) if XA+1e-6<XA+phase+k*tilew<XB-1e-6]+[XB]
        for i,(a,b) in enumerate(zip(edges,edges[1:])):
            a+=gap/2 if i else 0;b-=gap/2 if i<len(edges)-2 else 0
            append_tile(vs,fs,slots,a,b,ya,yb,(row*17+i*11)%7)
    new=C.mesh('A replacement rectangular pavers',vs,fs,mats[0],'E_WALK',[4492,4493])
    for m in mats[1:]:new.data.materials.append(m)
    for p,slot in zip(new.data.polygons,slots):p.material_index=slot
    old=bpy.data.objects['E_WALK central staggered paving'];old.data=new.data
    bpy.data.objects.remove(new,do_unlink=True);tag(old,'staggered rectangular slabs')
    old['estimated_slab_module']=[tilew,rowpitch];old['estimated_joint_width']=gap
    return [bed,old],dict(rows=rows,tile_module=[tilew,rowpitch],joint_width=gap)

def create_borders():
    mat=stone('A arc border neutral granite',(.485,.477,.453));obs=[]
    nx=24;radius=.225
    offsets=[-.044,-.032,-.025,-.019,-.012,-.006,0,.006,.012,.019,.025,.032,.044]
    for side,(a,b) in enumerate([(X0,XA),(XB,X1)]):
        for i in range(COUNT):
            ya=Y0+i*PITCH;yb=Y0+(i+1)*PITCH;cx=(a+b)/2;vs=[];fs=[]
            # Rows follow the exact arc, preventing the faceted cusp of the old Cartesian grid.
            for j in range(len(offsets)+2):
                for k in range(nx+1):
                    x=a+(b-a)*k/nx
                    arc=ya+.16+math.sqrt(radius**2-(x-cx)**2)-math.sqrt(radius**2-((b-a)/2)**2)
                    y=ya if j==0 else yb if j==len(offsets)+1 else arc+offsets[j-1]
                    d=0 if j in (0,len(offsets)+1) else offsets[j-1]
                    drop=DEPTH*.5*(1+math.cos(math.pi*d/.032)) if j not in (0,len(offsets)+1) and abs(d)<.032 else 0
                    vs.append((x,y,ztop(y)-drop))
            ny=len(offsets)+1
            for j in range(ny):
                for k in range(nx):q=j*(nx+1)+k;fs.append((q,q+1,q+nx+2,q+nx+1))
            edge=list(range(nx+1))+[j*(nx+1)+nx for j in range(1,ny+1)]+[ny*(nx+1)+k for k in range(nx-1,-1,-1)]+[j*(nx+1) for j in range(ny-1,0,-1)]
            topcount=len(vs);vs.extend([(vs[q][0],vs[q][1],ZB) for q in edge])
            fs.append(tuple(reversed(range(topcount,len(vs)))))
            for k,q in enumerate(edge):fs.append((q,topcount+k,topcount+(k+1)%len(edge),edge[(k+1)%len(edge)]))
            ob=tag(C.mesh('E_WALK recessed arc band %d %03d'%(side,i),vs,fs,mat,'E_WALK',[4492,4493]),'arc border')
            ob['estimated_groove_depth']=DEPTH;ob['estimated_band_width']=b-a;ob['estimated_pitch']=PITCH
            ob['profile_note']='可见弧形确认；余弦圆顺浅凹截面、0.018 深度均推定，用途未知'
            # Smooth within the top surface only; stone sides retain a sharp perimeter.
            for p in list(ob.data.polygons)[:ny*nx]:p.use_smooth=True
            obs.append(ob)
    return obs

def snap_cut_planes(ob):
    # Boolean intersection points may move by one float32 unit. Snap only cut planes.
    inv=ob.matrix_world.inverted()
    for v in ob.data.vertices:
        q=ob.matrix_world@v.co
        for axis,planes in [(0,[X0,X1]),(1,[Y0,Y1,80.])]:
            for plane in planes:
                if abs(q[axis]-plane)<1e-5:q[axis]=plane
        v.co=inv@q
        # The lawn's inherited -25 X translation makes this world plane halfway
        # between two local float32 values. Choose the exterior value, never an overlap.
        if ob.get('feature_id')=='LAWN' and abs((ob.matrix_world@v.co).x-X0)<1e-5:
            while (ob.matrix_world@v.co).x>X0:
                v.co.x=float(np.nextafter(np.float32(v.co.x),np.float32(-np.inf)))
    ob.data.update()

def difference(ob,cutter):
    if ob.data.users>1:ob.data=ob.data.copy()
    bpy.context.view_layer.objects.active=ob
    m=ob.modifiers.new('A remove only occupied corridor','BOOLEAN');m.operation='DIFFERENCE';m.solver='EXACT';m.object=cutter
    bpy.ops.object.modifier_apply(modifier=m.name)
    snap_cut_planes(ob)
    return C.solid_check(ob)

def cams():
    return {
      '4492':C.camera('A approximate IMG4492',(65.4,81,1.7),(65.4,34,.9),lens=26),
      '4493':C.camera('A approximate IMG4493',(66.8,80.4,1.7),(66.8,37,1.0),lens=29),
      'border':C.camera('A edge detail',(66.08,79.25,1.02),(66.97,76.7,.025),lens=53),
      'junction':C.camera('A plaza junction low',(65.9,80.10,.29),(65.4,77.60,.02),lens=34),
      'top':C.camera('A corridor orthographic',(65.3,47,110),(65.3,47,0),94),
    }

def render(name,cam,width=1200,samples=24,top=False,ratio=.75):
    C.render(name,cam,top=top,width=width,samples=samples,ratio=ratio)

def build():
    bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
    before=snapshots();source_sha=sha(BASE);fids=sorted(set(o.get('feature_id') for o in s.objects if o.get('feature_id')))
    allowed=[n for n in before if n.startswith('E_WALK')]
    allowed+=['LAWN | satellite-fixed concave north edge','LAWN_EDGE segmented granite 177','EDGE_PATHS__south-walk__FIN_pavers','FORECOURT photo grid plaza']
    allowed+=['LAWN_EDGE segmented granite %03d'%i for i in range(104,177)]
    for n in list(before):
        if n.startswith('E_WALK recessed') or n in allowed and n.startswith('LAWN_EDGE') and n!='LAWN_EDGE segmented granite 177':
            bpy.data.objects.remove(bpy.data.objects[n],do_unlink=True)
    cut=C.box('A temporary footprint cut',((X0+X1)/2,47,0),(X1-X0,66,2),bpy.data.materials['FC_light_band'],'E_WALK',[4492,4493])
    local_checks=[]
    for name in ['LAWN | satellite-fixed concave north edge','LAWN_EDGE segmented granite 177']:
        local_checks.append(difference(bpy.data.objects[name],cut))
    bpy.data.objects.remove(cut,do_unlink=True)
    # The inherited plaza has a 0.001867-unit² triangle over the west band tip.
    # Partition that real overlap at the existing path endpoint, retaining the plaza height/material.
    cut=C.box('A temporary plaza footprint cut',((X0+X1)/2,(Y0+Y1)/2,0),(X1-X0,Y1-Y0,2),bpy.data.materials['FC_light_band'],'E_WALK',[4492,4493])
    local_checks.append(difference(bpy.data.objects['FORECOURT photo grid plaza'],cut))
    bpy.data.objects.remove(cut,do_unlink=True)
    # Only split the occupied corner of the perpendicular south path.
    south=bpy.data.objects['EDGE_PATHS__south-walk__FIN_pavers'];mat=south.data.materials[0]
    new=C.prism('A south corner temporary',[(-28,11.90000057220459),(67.30211639404297,11.90000057220459),
      (67.30211639404297,15.699999809265137),(X1,15.699999809265137),(X1,Y0),(X0,Y0),(X0,15.699999809265137),(-28,15.699999809265137)],-.02,.05,mat,'EDGE_PATHS',[4492,4493])
    south.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
    local_checks.append(C.solid_check(south))
    changed,modules=create_paving();changed+=create_borders()
    checks=[C.solid_check(o) for o in changed]
    after=snapshots();protected={n:h for n,h in before.items() if n not in allowed}
    assert all(after.get(n)==h for n,h in protected.items()),[n for n,h in protected.items() if after.get(n)!=h]
    assert sha(BASE)==source_sha
    newfids=set(o.get('feature_id') for o in s.objects if o.get('feature_id'));assert set(fids)<=newfids
    camera=cams();s.camera=camera['4492'];s['active_checkpoint']='Subtask A: east lawn straight path, independent staggered stone, flush inferred arc border'
    s['A_reference_photos']=[4492,4493];s['A_groove_depth_and_function']='推定；0.018 场景单位；用途未确认'
    s['A_baseline_file']=str(BASE);s['A_baseline_sha256']=source_sha
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
    report=dict(baseline=str(BASE),source_sha256=source_sha,baseline_unchanged=True,
      protected_meshes_unchanged=len(protected),original_feature_ids_retained=True,
      unchanged_urns=[n for n in protected if n.startswith('E_ENTRY')],
      plaza_local_junction_cut_only=True,plaza_material_and_height_retained=True,
      removed_plaza_projection_overlap_area=.0018669019386834407,
      bounds=[X0,X1,Y0,Y1],centerline=(X0+X1)/2,total_width=X1-X0,
      dimensions_status='推定 / scene units, not survey dimensions',modules=modules,
      border_count=198,groove_depth=DEPTH,groove_depth_confidence='inferred / 推定',groove_function='unconfirmed / 推定',
      changed_baseline_objects=allowed,deleted_redundant_lawn_curbs=list(range(104,177)),
      local_cleanup_checks=local_checks,edited_solids=checks,protected_fingerprints=protected,
      endpoint_heights=dict(south=.05,north=.035,plaza=.035,central=.045),
      north_transition_length=2*PITCH,source_feature_ids=fids)
    (O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    for k in ['4492','border','junction','top']:render('diagnostic-'+k+'.png',camera[k],width=1000,samples=10,top=k=='top')
    print('BUILD_OK',len(changed),len(protected),flush=True)

def final():
    for phase,path in [('before',BASE),('after',OUT)]:
        bpy.ops.wm.open_mainfile(filepath=str(path));camera=cams()
        for k in ['4492','4493','junction']:
            render(phase+'-'+k+'.png',camera[k],width=1800,samples=32)
        if phase=='after':
            render('after-border.png',camera['border'],width=1800,samples=40)
            render('after-top.png',camera['top'],width=1800,samples=28,top=True)
            section()
    print('FINAL_RENDERS_OK',flush=True)

def section():
    # This is a render-only section of actual checkpoint meshes, with no exaggerated depth.
    s=bpy.context.scene
    for o in s.objects:
        if o.type=='MESH':o.hide_render=True
    sel=[bpy.data.objects['E_WALK recessed arc band 1 %03d'%i] for i in [96,97]]
    capmat=stone('A section cut face',(.29,.19,.095));cutx=(XB+X1)/2
    for o in sel:
        cp=o.copy();cp.data=o.data.copy();C.collection('12_A review section only').objects.link(cp);cp.hide_render=False
        bm=bmesh.new();bm.from_mesh(cp.data)
        result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(cutx,0,0),plane_no=(1,0,0),clear_inner=True,clear_outer=False)
        es=[e for e in bm.edges if e.is_boundary]
        if es:
            fill=bmesh.ops.holes_fill(bm,edges=es,sides=0)
            cp.data.materials.append(capmat)
            for f in fill['faces']:f.material_index=len(cp.data.materials)-1;f.smooth=False
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(cp.data);bm.free();cp.data.update()
    cy=Y0+97*PITCH
    cam=C.camera('A actual border section low',(cutx-1.08,cy+1.4,.36),(cutx+.083,cy,.012),lens=42)
    render('low-angle-section.png',cam,width=1800,samples=48,ratio=.58)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    if args and args[0]=='final':final()
    else:build()
