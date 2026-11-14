"""Photo-derived teaching building 4. Local metres, front faces -Y.

Six floors and visible facade details follow the supplied October 2026 photos.
Footprint follows the campus map; dimensions and concealed surfaces are inferred.
"""
import bpy, math, random
from mathutils import Vector

def build_teaching4():
    rng = random.Random(17)
    batches = {}
    def mat(name, color, rough=.75):
        m=bpy.data.materials.new('T4 '+name); m.diffuse_color=(*color,1);m.use_nodes=True
        p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
        return m
    plaster=mat('warm grey plaster',(.69,.69,.64)); frame=mat('charcoal aluminium',(.075,.09,.09),.4)
    glass=[mat('glass '+str(i),c,.24) for i,c in enumerate([(.22,.30,.32),(.29,.36,.37),(.18,.25,.27),(.34,.39,.39)])]
    brick=[mat('rose sandstone '+str(i),c) for i,c in enumerate([(.38,.25,.21),(.45,.31,.27),(.48,.34,.29)])]
    grey=mat('paving',(.57,.58,.55)); seam=mat('joints',(.30,.32,.30)); roof=mat('roof',(.35,.38,.37))
    stone=mat('weathered book covers',(.20,.23,.22)); pages=mat('stone page edges',(.39,.41,.38)); base=mat('rough granite',(.48,.49,.44))
    white=mat('clock markers',(.85,.86,.79)); gold=mat('bronze lettering',(.38,.25,.10),.4)
    greens=[mat('foliage '+str(i),c) for i,c in enumerate([(.13,.25,.055),(.21,.34,.08),(.28,.39,.10),(.10,.20,.09)])]
    pink=mat('red flowers',(.65,.055,.17)); purple=mat('violet flowers',(.43,.19,.38))
    soil=mat('flowerbed soil',(.10,.12,.065))
    def mesh(name,v,f,m):
        vs,fs=batches.setdefault((name,m),([],[])); n=len(vs);vs.extend(v);fs.extend([tuple(n+i for i in face) for face in f])
    def box(name,x,y,z,w,d,h,m,angle=0):
        v=[]
        for a,b,c in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]:
            dx=a*w/2;dy=b*d/2;v.append((x+dx*math.cos(angle)-dy*math.sin(angle),y+dx*math.sin(angle)+dy*math.cos(angle),z+c*h/2))
        mesh(name,v,[(2,6,4,0),(5,7,3,1),(4,5,1,0),(3,7,6,2),(1,3,2,0),(6,7,5,4)],m)
    def rail(name,a,b,r,m):
        a,b=Vector(a),Vector(b);axis=(b-a).normalized();u=axis.cross(Vector((0,0,1)))
        if u.length<.01:u=axis.cross(Vector((0,1,0)))
        u.normalize();v=axis.cross(u)
        verts=[tuple(p+r*(u*math.cos(i*math.tau/8)+v*math.sin(i*math.tau/8))) for p in [a,b] for i in range(8)]
        mesh(name,verts,[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)],m)
    # Continuous body, inset glazing and horizontal plaster bands.
    box('six storey structure',0,0,9.7,40.8,13.6,18.8,plaster)
    box('flat roof',0,0,19.15,40.3,13.1,.16,roof)
    for y in [-6.65,6.65]:box('roof parapet',0,y,19.6,40.2,.3,.9,plaster)
    for x in [-20.25,20.25]:box('end parapet',x,0,19.6,.3,13.6,.9,plaster)
    for side in [-1,1]:
        y=side*6.84
        for row in range(6):
            z=1.95+row*3.02
            for col in range(12):
                x=-18.5+col*3.36
                if side==-1 and 8.2<x<11.5:continue
                if side==1 and 4.0<x<10.5:continue
                w=2.94;h=1.98
                box('window glass',x,y,z,w,.08,h,rng.choice(glass))
                for dx in [-w/2,-w/6,w/6,w/2]:box('window mullions',x+dx,y+side*.06,z,.055,.10,h,frame)
                for dz in [-h/2,.40,h/2]:box('window transoms',x,y+side*.06,z+dz,w,.10,.055,frame)
                box('projecting sills',x,y,z-h/2-.07,w+.13,.25,.10,grey)
        for row in range(4):
            for col in range(59):
                x=-20.1+col*.69+(row%2)*.30
                if x>20.3:continue
                box('sandstone plinth',x,y,.25+row*.19,.66,.16,.175,rng.choice(brick))
    # Projecting balconies above the entrance through the top storey.
    for level in range(1,6):
        z=.7+level*3.02
        box('balcony slab',3.7,-7.8,z,8.1,2.35,.24,plaster)
        box('balcony front',3.7,-8.9,z+.49,8.1,.22,.82,plaster)
        for x in [-.24,7.64]:box('balcony returns',x,-7.85,z+.49,.22,2.1,.82,plaster)
        rail('balcony handrails',(-.24,-8.92,z+1.15),(7.64,-8.92,z+1.15),.035,frame)
        for i in range(17):rail('balcony posts',(-.24+i*.49,-8.92,z+.9),(-.24+i*.49,-8.92,z+1.15),.025,frame)
    # Sheet-clad vertical shaft to the right of the entrance.
    box('front shaft',9.25,-7.1,10.35,2.45,1.1,20.1,plaster)
    for z in [i*.9+.4 for i in range(23)]:box('shaft horizontal joints',9.25,-7.665,z,2.45,.014,.018,seam)
    for x in [8.07,9.25,10.43]:box('shaft vertical joints',x,-7.67,10.35,.018,.015,20.1,seam)
    box('shaft top vent',9.25,-7.69,19.5,1.48,.05,.65,frame)
    for i in range(8):box('vent louvers',9.25,-7.73,19.23+i*.075,1.45,.04,.025,grey)
    # Rear stair tower: four tall slots per floor, roof guardrail.
    box('rear stair tower',6.8,7.0,10.35,5.7,.9,20.1,plaster)
    for row in range(6):
        for col in range(4):
            x=4.9+col*1.25;z=1.95+row*3.02
            box('stair slot frames',x,7.48,z,.43,.09,2.30,frame)
            box('stair slot glazing',x,7.54,z,.34,.045,2.18,glass[(row+col)%4])
            box('stair slot transom',x,7.58,z+.2,.4,.05,.055,frame)
        box('stair sill ledges',6.8,7.5,.73+row*3.02,5.5,.23,.10,grey)
    for i in range(23):rail('roof stair guardrail',(4.05+i*.25,7.35,20.4),(4.05+i*.25,7.35,21.1),.02,frame)
    rail('roof stair guardrail',(4.05,7.35,21.1),(9.55,7.35,21.1),.03,frame)
    # Main door, steps and wheelchair ramp.
    box('entry glazing',3.7,-6.95,1.9,6.5,.13,2.65,glass[2])
    for x in [.5,2.1,3.7,5.3,6.9]:box('entry door frames',x,-7.05,1.9,.08,.10,2.65,frame)
    for i in range(4):box('entry steps',3.7,-7.4-i*.31,.63-i*.13,8.1,1.1,.16,grey)
    mesh('accessible ramp',[(-10,-7.2,.30),(-.5,-7.2,.75),(-.5,-8.3,.75),(-10,-8.3,.30)],[(0,1,2,3)],grey)
    for y in [-7.2,-8.3]:
        rail('ramp handrail',(-10,y,1.2),(-.5,y,1.65),.035,frame)
        for i in range(7):rail('ramp posts',(-10+i*1.58,y,.32+i*.075),(-10+i*1.58,y,1.2+i*.075),.025,frame)
    # Rear entrance canopy and blank end walls from the side photograph.
    box('rear door',6.8,7.56,1.7,3.2,.1,2.8,glass[2])
    box('rear canopy',6.8,8.0,3.25,5.8,1.7,.14,frame)
    box('forecourt paving',0,-9.9,.24,41.5,6.2,.14,grey)
    for i in range(42):box('paving joints',-20.5+i,-9.9,.316,.012,6.2,.006,seam)
    for j in range(7):box('paving joints',0,-12.9+j,.317,41.5,.012,.006,seam)
    # Connected two-lobed raised bed, with a slightly pinched waist.
    def outline(t):
        r=1+.17*math.cos(2*t)+.07*math.cos(3*t)
        return (9+6.1*r*math.cos(t),-11.0+2.05*r*math.sin(t))
    n=112; pts=[outline(i*math.tau/n) for i in range(n)]
    mesh('flowerbed soil',[(9,-11,.68)]+[(x,y,.68) for x,y in pts],[(0,i+1,(i+1)%n+1) for i in range(n)],soil)
    for i,(x,y) in enumerate(pts):
        nx,ny=pts[(i+1)%n];angle=math.atan2(ny-y,nx-x)
        box('dark stone flowerbed edging',(x+nx)/2,(y+ny)/2,.50,math.hypot(nx-x,ny-y)*.98,.23,.46,stone,angle)
        box('flowerbed coping',(x+nx)/2,(y+ny)/2,.75,math.hypot(nx-x,ny-y)*.99,.29,.08,pages,angle)
    def leaf(x,y,z,size,m):
        a=rng.random()*math.tau;c=math.cos(a)*size;s=math.sin(a)*size
        mesh('flowerbed foliage',[(x-c,y-s,z),(x-s*.4,y+c*.4,z+.06),(x+c,y+s,z+.03),(x+s*.4,y-c*.4,z-.02)],[(0,1,2),(0,2,3)],m)
    for i in range(3100):
        t=rng.random()*math.tau;r=math.sqrt(rng.random());bx,by=outline(t);x=9+(bx-9)*r;y=-11+(by+11)*r
        if (x-11.7)**2+(y+10.8)**2<1.55:continue
        z=.79+rng.random()*.24
        for j in range(3):leaf(x+rng.uniform(-.12,.12),y+rng.uniform(-.12,.12),z+j*.045,rng.uniform(.10,.18),rng.choice(greens))
        if r>.78 and i%3==0 or x>10 and i%6==0:
            for j in range(4):leaf(x+rng.uniform(-.05,.05),y+rng.uniform(-.05,.05),z+.19,.043,pink if r>.78 else purple)
    # Sculpture: rough plinth, seven offset books, upright clock volume.
    sx,sy=11.7,-10.8
    box('sculpture black footing',sx,sy,.84,2.95,2.25,.18,stone)
    box('sculpture granite pedestal',sx,sy,1.38,2.42,1.8,.94,base)
    for i in range(7):
        z=1.96+i*.43;a=math.radians([0,-8,6,-12,9,-5,4][i]);w=[2.5,2.75,2.65,2.9,2.6,2.85,2.5][i]
        dx=[0,-.08,.10,-.12,.08,.04,-.1][i]
        # Concave page fore-edges give the stone books their distinctive profile.
        verts=[]
        for k in range(7):
            inset=.11*math.sin(k*math.pi/6)
            for xx,yy in [(-(w-.14)/2,-.79+inset),((w-.14)/2,-.79+inset),((w-.14)/2,.79),(-(w-.14)/2,.79)]:
                verts.append((sx+dx+xx*math.cos(a)-yy*math.sin(a),sy+xx*math.sin(a)+yy*math.cos(a),z-.15+k*.05))
        faces=[(3,2,1,0),(24,25,26,27)]+[(k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j) for k in range(6) for j in range(4)]
        mesh('curved book page blocks',verts,faces,pages)
        for dz in [-.19,.19]:box('overhanging book covers',sx+dx,sy,z+dz,w,1.78,.085,stone,a)
        for dz in [-.10,-.05,0,.05,.10]:
            yy=-.805+.11*math.cos(dz/.15*math.pi/2)
            box('engraved page strata',sx+dx-yy*math.sin(a),sy+yy*math.cos(a),z+dz,w-.2,.018,.010,stone,a)
    box('upright clock book',sx,sy,5.75,1.32,.48,1.80,stone)
    box('clock spine',sx-.69,sy,5.75,.09,.55,1.83,pages)
    for i in range(12):
        a=i*math.tau/12;cx=sx+.48*math.sin(a);cz=5.75+.59*math.cos(a)
        rail('clock hour marks',(cx,sy-.26,cz),(sx+.38*math.sin(a),sy-.26,5.75+.47*math.cos(a)),.027,white)
    rail('clock minute hand',(sx,sy-.29,5.75),(sx-.43,sy-.29,5.95),.033,white)
    rail('clock hour hand',(sx,sy-.30,5.75),(sx-.23,sy-.30,5.60),.043,white)
    objects=[]
    for (name,m),(vs,fs) in batches.items():
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update()
        o=bpy.data.objects.new('T4 '+name,me);bpy.context.scene.collection.objects.link(o);o['building_id']='17';objects.append(o)
    # Real lettering on the first balcony, converted to geometry for GLB.
    fontpath='/System/Library/Fonts/STHeiti Medium.ttc'
    try:font=bpy.data.fonts.load(fontpath)
    except RuntimeError:font=None
    c=bpy.data.curves.new('第四教学楼','FONT');c.body='第 四 教 学 楼';c.align_x='CENTER';c.size=.45;c.extrude=.012
    if font:c.font=font
    o=bpy.data.objects.new('T4 entrance lettering',c);bpy.context.scene.collection.objects.link(o);o.location=(3.7,-9.03,4.02);o.rotation_euler=(math.pi/2,0,0);c.materials.append(gold)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object;o['building_id']='17';objects.append(o)
    return objects
