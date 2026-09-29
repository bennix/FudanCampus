"""58: low-poly photo study; front is Blender -Y (campus south).

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
        m.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*color, 1)
        m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .92
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
    # Deliberate low-poly creases, same stone, rather than drawn black outlines.
    for sign in [-1,1]:
        mesh('long coat fold',[(sign*.48,-.38,5.91),(sign*.69,-.40,4.05),(sign*.44,-.48,4.04),(sign*.31,-.408,5.17)],[(0,1,2),(0,2,3)],light)
        limb('sleeve with elbow behind',[(sign*.60,.06,7.19),(sign*.76,.045,7.02),(sign*.86,.06,6.65),(sign*.94,.13,6.07),(sign*.76,.37,5.70),(sign*.45,.52,5.62)],[.22,.25,.24,.215,.17,.14])
        mesh('slanted pocket flap',[(sign*.57,-.32,5.94),(sign*.78,-.26,5.88),(sign*.79,-.29,5.67),(sign*.57,-.38,5.73)],[(0,1,2,3)],light)
        mesh('pointed collar',[(sign*.035,-.25,7.43),(sign*.30,-.21,7.43),(sign*.46,-.365,7.22),(sign*.25,-.425,7.08)],[(0,1,2),(0,2,3)],light)
    ellipsoid('hands clasped behind',(0,.55,5.66),(.40,.17,.15),segments=10)
    for sign in [-1,1]:
        for z in [5.97,6.34,6.71,7.04]:
            ellipsoid('double row coat button',(sign*.30,-.414,z),(.052,.025,.052),light,10,4)
    mesh('overlap seam',[(-.12,-.415,5.95),(-.11,-.419,6.93),(-.095,-.422,6.93),(-.10,-.418,5.95)],[(0,1,2,3)],dark)
    rings('neck',[(7.34,0,.025,.20,.20),(7.65,0,.015,.22,.21)],12)
    # Head: broad cheeks and forehead, receding swept-back hair, sculpted nose and lips.
    head_start=len(objects)
    head=rings('broad rounded face',[(7.53,0,-.005,.17,.17),
        (7.60,0,-.025,.245,.235),(7.69,0,-.005,.29,.265),
        (7.81,0,.005,.325,.275),(7.94,0,.018,.325,.272),
        (8.06,0,.025,.31,.273),(8.18,0,.03,.302,.272),
        (8.30,0,.038,.285,.255),(8.38,0,.045,.235,.21),
        (8.425,0,.055,.12,.115),(8.44,0,.06,.018,.02)],24)
    # Flatten the central face continuously into the cheek planes. No separate
    # spherical cheek attachments: they made the earlier face look mechanical.
    for v in head.data.vertices:
        if v.co.y < -.08:
            v.co.y -= .025*(abs(v.co.x)/.325)
    for sign in [-1,1]:
        ellipsoid('ear',(sign*.315,.025,7.94),(.04,.068,.118),segments=10,rings_count=5)
        mesh('soft brow arch',[(sign*.052,-.253,8.125),(sign*.12,-.272,8.143),(sign*.195,-.241,8.131),(sign*.238,-.204,8.10),(sign*.17,-.253,8.105),(sign*.085,-.272,8.105)],[(0,1,5),(1,2,4,5),(2,3,4)],stone)
        mesh('upper eyelid',[(sign*.065,-.258,8.066),(sign*.115,-.273,8.088),(sign*.165,-.26,8.087),(sign*.215,-.226,8.059),(sign*.158,-.267,8.064),(sign*.11,-.275,8.066)],[(0,1,5),(1,2,4,5),(2,3,4)],stone)
        mesh('eye slit',[(sign*.07,-.263,8.063),(sign*.12,-.278,8.073),(sign*.167,-.263,8.07),(sign*.21,-.23,8.058),(sign*.157,-.268,8.054),(sign*.115,-.279,8.053)],[(0,1,5),(1,2,4,5),(2,3,4)],dark)
        ellipsoid('lower eyelid',(sign*.136,-.244,8.040),(.075,.018,.022),stone,10,4)
    mesh('broad nose',[(-.035,-.256,8.10),(.035,-.256,8.10),
        (-.045,-.31,8.01),(.045,-.31,8.01),(-.055,-.366,7.943),(.055,-.366,7.943),
        (-.103,-.301,7.918),(.103,-.301,7.918),(0,-.379,7.935),(0,-.315,7.898)],
        [(0,2,3,1),(2,4,8),(2,8,5,3),(4,6,9,8),(8,9,7,5),(0,6,4,2),(1,3,5,7),(6,7,9)],stone)
    for sign in [-1,1]:
        ellipsoid('nose wing',(sign*.077,-.30,7.927),(.044,.037,.032),stone,10,4)
        ellipsoid('nostril recess',(sign*.068,-.323,7.906),(.021,.011,.009),dark,8,3)
    mesh('closed upper lip',[(-.15,-.239,7.798),(-.083,-.279,7.815),(-.035,-.29,7.827),(0,-.298,7.817),(.035,-.29,7.827),(.083,-.279,7.815),(.15,-.239,7.798),(.075,-.291,7.79),(0,-.309,7.793),(-.075,-.291,7.79)],
         [(0,1,9),(1,2,3,8,9),(3,4,5,7,8),(5,6,7)],stone)
    mesh('quiet mouth line',[(-.145,-.244,7.797),(-.07,-.295,7.796),(0,-.312,7.798),(.07,-.295,7.796),(.145,-.244,7.797),(.07,-.294,7.785),(0,-.308,7.788),(-.07,-.294,7.785)],[(0,1,7),(1,2,6,7),(2,3,5,6),(3,4,5)],dark)
    ellipsoid('full lower lip',(0,-.267,7.765),(.124,.039,.032),stone,14,4)
    ellipsoid('small chin mole',(.029,-.269,7.707),(.009,.006,.009),stone,8,3)
    # A receding front hairline with fuller swept-back sides, not a tall cap.
    hair_vs=[];hair_faces=[];n=32
    for k in range(5):
        t=k/4
        for j in range(n):
            a=math.tau*j/n
            front=max(0,-math.sin(a))
            bottom=8.015+.388*front**3
            z=bottom+(8.454-bottom)*t
            radius=math.sqrt(max(.003,1-((z-8.105)/.355)**2))
            hair_vs.append((.345*radius*math.cos(a),.067+.278*radius*math.sin(a),z))
    for k in range(4):
        for j in range(n):hair_faces.append((k*n+j,k*n+(j+1)%n,(k+1)*n+(j+1)%n,(k+1)*n+j))
    hair_faces.append(tuple(4*n+j for j in range(n)))
    mesh('receding hairline swept side hair',hair_vs,hair_faces,dark)
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
