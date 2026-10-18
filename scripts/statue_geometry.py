"""58: reference-guided sculptural study; front is Blender -Y (campus south).

Dimensions are inferred, not surveyed. The cropped crown and unseen rear are
conservative reconstructions. Geometry only: no photographic image billboard.
"""
import math
from pathlib import Path
import bpy
from mathutils import Vector


def build_statue(x=0, y=0):
    objects = []
    def material(name, color):
        m = bpy.data.materials.new(name)
        m.diffuse_color = (*color, 1)
        m.use_nodes = True
        next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Base Color'].default_value = (*color, 1)
        next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED').inputs['Roughness'].default_value = .92
        return m
    stone = material('58 · weathered grey stone', (.19,.18,.165))
    light = material('58 · cut stone planes', (.215,.202,.184))
    dark = material('58 · recessed stone', (.145,.14,.13))
    pedestal = material('58 · grey granite pedestal', (.25,.26,.25))
    plaque = material('58 · pale inscription panel', (.75,.77,.70))
    gold = material('58 · ochre gold inscription', (.60,.405,.105))
    def mesh(name, vs, faces, mat=stone):
        data=bpy.data.meshes.new(name); data.from_pydata(vs, [], faces); data.update()
        obj=bpy.data.objects.new('毛主席像 · '+name,data)
        bpy.context.scene.collection.objects.link(obj); obj.location=(x,y,0)
        obj.data.materials.append(mat); obj['landmark_id']='58'; obj['landmark_name']='毛主席像'
        objects.append(obj); return obj
    def box(name,c,size,mat=stone):
        vs=[(c[0]+a*size[0]/2,c[1]+b*size[1]/2,c[2]+d*size[2]/2)
            for a,b,d in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
        return mesh(name,vs,[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)],mat)
    def rings(name, levels, n=16, mat=stone, phase=0):
        # z, centre x/y, half width/depth. Front facets carry subtle cloth folds.
        vs=[]
        for z,cx,cy,rx,ry in levels:
            for j in range(n):
                a=math.tau*j/n+phase
                vs.append((cx+rx*math.cos(a),cy+ry*math.sin(a),z))
        fs=[tuple(range(n-1,-1,-1)),tuple((len(levels)-1)*n+j for j in range(n))]
        for k in range(len(levels)-1):
            for j in range(n):
                a=k*n+j;b=k*n+(j+1)%n;c=b+n;d=a+n
                fs.extend([(a,b,c),(a,c,d)])
        return mesh(name,vs,fs,mat)
    def ellipsoid(name,center,scale,mat=stone,segments=12,rings_count=7):
        levels=[]
        for k in range(rings_count+1):
            a=-math.pi/2+.015+(math.pi-.03)*k/rings_count
            levels.append((center[2]+scale[2]*math.sin(a),center[0],center[1],scale[0]*math.cos(a),scale[1]*math.cos(a)))
        return rings(name,levels,segments,mat)
    def limb(name, points, radii):
        vs=[];n=10
        for i,(p,r) in enumerate(zip(points,radii)):
            tangent=Vector(points[min(i+1,len(points)-1)])-Vector(points[max(i-1,0)])
            tangent.normalize();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
            for j in range(n):
                q=Vector(p)+r*(u*math.cos(math.tau*j/n)+v*math.sin(math.tau*j/n));vs.append(tuple(q))
        fs=[tuple(range(n-1,-1,-1)),tuple((len(points)-1)*n+j for j in range(n))]
        for k in range(len(points)-1):
            for j in range(n):fs.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
        return mesh(name,vs,fs)
    box('lower square step',(0,0,.12),(4.3,3.8,.24),pedestal)
    rings('sloping upper step',[(.24,0,0,2,1.72),(.49,0,0,1.58,1.35)],4,pedestal,math.pi/4)
    box('upper step',(0,0,.36),(3.65,3.05,.22),pedestal)
    box('granite square monument',(0,0,1.71),(2.42,1.92,2.5),pedestal)
    box('statue foot slab',(0,0,3.10),(2.17,1.64,.28),stone)
    box('pale front tablet',(0,-.969,2.20),(1.49,.045,.76),plaque)
    # Close-set shoes and exposed trouser legs under the long coat.
    for sign in [-1,1]:
        ellipsoid('shoe', (sign*.35,-.16,3.36),(.32,.53,.17),segments=12)
        rings('trouser leg',[(3.37,sign*.35,.04,.27,.28),(3.70,sign*.35,.03,.25,.27),(4.13,sign*.34,.02,.29,.29)],10)
        mesh('trouser crease',[(sign*.35,-.267,3.44),(sign*.32,-.285,4.12),(sign*.38,-.295,3.74)],[(0,1,2)],light)
    # Broad, gently flared hem; narrow hips; upright chest and sloping shoulders.
    coat=rings('long double breasted overcoat',[
        (4.02,-.07,0,1.01,.49),(4.17,-.08,0,1.00,.49),
        (4.65,-.04,.01,.91,.46),(5.2,0,.02,.80,.435),
        (5.82,0,.015,.69,.40),(6.25,0,0,.72,.41),
        (6.82,0,0,.79,.415),(7.20,0,.01,.77,.37),
        (7.35,0,.025,.57,.31),(7.43,0,.035,.31,.25)],20)
    for v in coat.data.vertices:
        if v.co.y < 0 and v.co.z < 5.9:
            v.co.y -= .035*math.cos(v.co.x*15)*(5.9-v.co.z)/1.9
    # Deliberate low-poly creases, same stone, rather than drawn black outlines.
    for sign in [-1,1]:
        limb('sleeve with elbow behind',[(sign*.60,.06,7.19),(sign*.76,.045,7.02),(sign*.86,.06,6.65),(sign*.94,.13,6.07),(sign*.76,.37,5.70),(sign*.45,.52,5.62)],[.22,.25,.24,.215,.17,.14])
        mesh('slanted pocket flap',[(sign*.57,-.32,5.94),(sign*.78,-.26,5.88),(sign*.79,-.29,5.67),(sign*.57,-.38,5.73)],[(0,1,2,3)],light)
        mesh('pointed collar',[(sign*.035,-.25,7.43),(sign*.30,-.21,7.43),(sign*.46,-.365,7.22),(sign*.25,-.425,7.08)],[(0,1,2),(0,2,3)],light)
    ellipsoid('hands clasped behind',(0,.55,5.66),(.40,.17,.15),segments=10)
    for sign in [-1,1]:
        for z in [5.97,6.34,6.71,7.04]:
            ellipsoid('double row coat button',(sign*.30,-.414,z),(.052,.025,.052),light,10,4)
    mesh('overlap seam',[(-.12,-.415,5.95),(-.11,-.419,6.93),(-.095,-.422,6.93),(-.10,-.418,5.95)],[(0,1,2,3)],dark)
    neck=rings('neck',[(7.34,0,.025,.20,.20),(7.65,0,.015,.22,.21)],48)
    for poly in neck.data.polygons:poly.use_smooth=True
    for obj in objects:
        if any(word in obj.name for word in ['overcoat','sleeve','trouser leg','shoe','hands clasped']):
            for poly in obj.data.polygons:poly.use_smooth=True
            mod=obj.modifiers.new('Soft sculpted cloth','SUBSURF');mod.levels=2;mod.render_levels=2
    # Head: broad cheeks and forehead, receding swept-back hair, sculpted nose and lips.
    head_start=len(objects)
    # Continuous sculpted surface: features displace the same facial mesh.
    # Coordinates remain compatible with the campus statue's neck and scale.
    def g(x,z,cx,cz,wx,wz):
        return math.exp(-((x-cx)/wx)**2-((z-cz)/wz)**2)
    vs=[];fs=[];nu=128;nv=104
    for k in range(nv+1):
        t=math.pi*(.001+.998*k/nv)
        z=7.985+.465*math.cos(t)
        jaw=1-.14*math.exp(-((z-7.59)/.13)**2)
        rx=.332*math.sin(t)*jaw
        for j in range(nu):
            a=math.tau*j/nu
            xx=rx*math.cos(a); yy=.045+.285*math.sin(t)*math.sin(a)
            front=max(0,-math.sin(a))**4
            d=0
            # Fuller cheek pads, broad chin and recessed eye sockets.
            for sign in [-1,1]:
                d+=.042*g(xx,z,sign*.19,7.91,.105,.115)
                d-=.027*g(xx,z,sign*.135,8.075,.083,.038)
                d+=.032*g(xx,z,sign*.13,8.126,.10,.035)
                d+=.014*g(xx,z,sign*.13,8.035,.075,.025)
                d+=.037*g(xx,z,sign*.068,7.958,.042,.028)
                d-=.014*g(xx,z,sign*.071,7.938,.019,.012)
                d-=.010*g(xx,z,sign*.12,7.88,.024,.059)
            d+=.052*g(xx,z,0,7.657,.15,.065)
            # Nose bridge and rounded tip, integrated into the cheeks.
            d+=.063*g(xx,z,0,8.048,.037,.102)
            d+=.115*g(xx,z,0,7.969,.056,.042)
            d+=.018*g(xx,z,0,7.855,.12,.065)
            d+=.020*g(xx,z,0,7.826,.109,.014)
            d+=.025*g(xx,z,0,7.797,.108,.018)
            d-=.017*g(xx,z,0,7.813,.13,.006)
            d-=.009*g(xx,z,0,7.757,.10,.018)
            yy-=front*d
            vs.append((xx,yy,z))
    for k in range(nv):
        for j in range(nu):
            a=k*nu+j;b=k*nu+(j+1)%nu
            fs.append((a,b,b+nu,a+nu))
    fs.extend([tuple(range(nu-1,-1,-1)),tuple(nv*nu+j for j in range(nu))])
    head=mesh('continuous sculpted portrait',vs,fs)
    for poly in head.data.polygons:poly.use_smooth=True
    def facial_y(xx,zz):
        candidates=[v for v in vs if v[1]<0]
        return min(candidates,key=lambda v:(v[0]-xx)**2+(v[2]-zz)**2)[1]
    def ridge(name,points,radius,mat):
        curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.bevel_depth=radius;curve.bevel_resolution=3
        spline=curve.splines.new('POLY');spline.points.add(len(points)-1)
        for i,(p,co) in enumerate(zip(spline.points,points)):
            p.co=(*co,1);p.radius=.15+.85*math.sin(math.pi*i/(len(points)-1))
        ob=bpy.data.objects.new('毛主席像 · '+name,curve);bpy.context.scene.collection.objects.link(ob);ob.location=(x,y,0);ob.data.materials.append(mat)
        bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob;bpy.ops.object.convert(target='MESH')
        ob['landmark_id']='58';ob['landmark_name']='毛主席像';objects.append(ob)
    for sign in [-1,1]:
        for upper in [True,False]:
            points=[]
            for j in range(25):
                t=j/24;xx=sign*(.067+.142*t)
                zz=8.068+( .013 if upper else -.008)*math.sin(math.pi*t)-.006*t
                points.append((xx,facial_y(xx,zz)-.006,zz))
            ridge('sculpted upper eyelid' if upper else 'sculpted lower eyelid',points,.006 if upper else .004,stone)
        ear=ellipsoid('rounded ear',(sign*.319,.034,7.978),(.049,.064,.109),stone,24,16)
        for poly in ear.data.polygons:poly.use_smooth=True
        inner=ellipsoid('ear concha',(sign*.344,-.012,7.977),(.016,.018,.060),stone,20,12)
        for poly in inner.data.polygons:poly.use_smooth=True
    ellipsoid('chin mole',(.032,-.237,7.718),(.007,.005,.007),stone,12,8)
    # Receding temples and broad swept-back mass, with restrained combed grooves.
    hair_vs=[];hair_faces=[];n=128;rows=32
    for k in range(rows+1):
        t=k/rows
        for j in range(n):
            a=math.tau*j/n;front=max(0,-math.sin(a))
            bottom=7.995+.365*front**.55+.018*math.cos(a)*front
            z=bottom+(8.468-bottom)*math.sin(t*math.pi/2)
            radius=math.sqrt(max(.00001,1-((z-8.005)/.464)**2))
            groove=.0012*math.sin(35*a+8*t)*(math.sin(math.pi*t)**.5)
            hair_vs.append((((.332+.012*math.sin(math.pi*t))*radius+groove)*math.cos(a),.045+((.285+.012*math.sin(math.pi*t))*radius+groove)*math.sin(a),z))
    for k in range(rows):
        for j in range(n):hair_faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    hair_faces.append(tuple(rows*n+j for j in range(n)))
    hair=mesh('swept back receding hair',hair_vs,hair_faces,stone)
    for poly in hair.data.polygons:poly.use_smooth=True
    # Slight turn, without exaggerating the pose inferred from oblique photos.
    for obj in objects[head_start:]:
        for v in obj.data.vertices:
            v.co.z=7.53+(v.co.z-7.53)*.88
            a=math.radians(-7);vx,vy=v.co.x,v.co.y;v.co.x=vx*math.cos(a)-vy*math.sin(a);v.co.y=vx*math.sin(a)+vy*math.cos(a)
    def text(body,z,size):
        curve=bpy.data.curves.new('Inscription','FONT');curve.body=body;curve.align_x='CENTER';curve.size=size;curve.extrude=.0015;curve.resolution_u=2
        font=Path('/System/Library/Fonts/Supplemental/Songti.ttc')
        if font.exists():curve.font=bpy.data.fonts.load(str(font))
        obj=bpy.data.objects.new('毛主席像 · '+body,curve);bpy.context.scene.collection.objects.link(obj)
        obj.location=(x,y-.997,z);obj.rotation_euler=(math.pi/2,0,0);obj.data.materials.append(gold)
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH')
        obj['landmark_id']='58';obj['landmark_name']='毛主席像';objects.append(obj)
    text('毛 泽 东',2.25,.29);text('1893.12—1976.9',2.03,.13)
    return objects

# Keep the procedural study available; the published landmark uses the licensed scan.
_build_statue_study = build_statue

def build_statue(x=0, y=0):
    import bmesh
    from mathutils import Matrix
    source = Path(__file__).resolve().parents[1] / 'assets/landmarks/sources/mao-sketchfab.glb'
    if not source.exists():
        raise FileNotFoundError(f'Missing licensed statue source: {source}')
    old = _build_statue_study(x,y)
    pedestal = []
    for obj in old:
        if max(v.co.z for v in obj.data.vertices) <= 3.241:
            pedestal.append(obj)
        else:
            bpy.data.objects.remove(obj,do_unlink=True)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(source))
    imported=set(bpy.data.objects)-before
    parts=[o for o in imported if o.type=='MESH']
    empties=[o for o in imported if o.type=='EMPTY']
    for obj in parts:
        transform=obj.matrix_world.copy()
        obj.parent=None;obj.matrix_world=Matrix.Identity(4)
        obj.data.transform(transform)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in parts:obj.select_set(True)
    bpy.context.view_layer.objects.active=parts[0]
    bpy.ops.object.join();figure=bpy.context.object
    # Remove the scan's short plinth; the existing campus pedestal is retained.
    cut=.95
    bm=bmesh.new();bm.from_mesh(figure.data)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(0,0,cut),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
    boundary=[e for e in bm.edges if e.is_boundary and all(abs(v.co.z-cut)<.001 for v in e.verts)]
    if boundary:bmesh.ops.holes_fill(bm,edges=boundary,sides=0)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(figure.data);bm.free()
    vs=figure.data.vertices
    lo=[min(v.co[i] for v in vs) for i in range(3)];hi=[max(v.co[i] for v in vs) for i in range(3)]
    factor=5.10/(hi[2]-cut)
    for v in vs:
        v.co=Vector(((v.co.x-(lo[0]+hi[0])/2)*factor,(v.co.y-(lo[1]+hi[1])/2)*factor,3.24+(v.co.z-cut)*factor))
    figure.location=(x,y,0);figure.name='毛主席像 · Sketchfab 1821427398'
    figure['landmark_id']='58';figure['landmark_name']='毛主席像'
    figure['source']='https://sketchfab.com/3d-models/ef18c25e1e094cf99e2b377ad7377d05'
    figure['author']='1821427398';figure['license']='CC BY 4.0'
    figure['modifications']='Original plinth removed; scaled and placed on campus pedestal.'
    figure.data.materials.clear();figure.data.materials.append(bpy.data.materials.get('58 · weathered grey stone'))
    for poly in figure.data.polygons:poly.use_smooth=True
    for obj in empties:bpy.data.objects.remove(obj,do_unlink=True)
    return pedestal+[figure]
