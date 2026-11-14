"""Photo-derived teaching building 4. Local metres, front faces -Y.

Six floors and visible facade details follow the supplied October 2026 photos.
Footprint follows the campus map; dimensions and concealed surfaces are inferred.
"""
import bpy, math, random
from pathlib import Path
from mathutils import Vector

def build_teaching4():
    rng = random.Random(17)
    batches = {}
    def mat(name, color, rough=.75):
        m=bpy.data.materials.new('T4 '+name); m.diffuse_color=(*color,1);m.use_nodes=True
        p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        p.inputs['Base Color'].default_value=(*color,1);p.inputs['Roughness'].default_value=rough
        return m
    plaster=mat('warm grey plaster',(.72,.725,.69)); frame=mat('charcoal aluminium',(.075,.065,.06),.38)
    glass=[mat('glass '+str(i),c,.3) for i,c in enumerate([(.25,.31,.30),(.28,.34,.33),(.23,.29,.28),(.30,.35,.34)])]
    brick=[mat('rose sandstone '+str(i),c) for i,c in enumerate([(.38,.25,.21),(.45,.31,.27),(.48,.34,.29)])]
    grey=mat('paving',(.57,.58,.55)); seam=mat('joints',(.30,.32,.30)); roof=mat('roof',(.35,.38,.37))
    stone=mat('weathered book covers',(.20,.23,.22)); pages=mat('stone page edges',(.39,.41,.38)); base=mat('rough granite',(.48,.49,.44))
    white=mat('clock markers',(.85,.86,.79)); gold=mat('bronze lettering',(.38,.25,.10),.4)
    greens=[mat('foliage '+str(i),c) for i,c in enumerate([(.13,.25,.055),(.21,.34,.08),(.28,.39,.10),(.10,.20,.09)])]
    pink=mat('red flowers',(.65,.055,.17)); purple=mat('violet flowers',(.43,.19,.38))
    soil=mat('flowerbed soil',(.10,.12,.065))
    curtain=mat('curtain',(.43,.47,.43)); dark=mat('entry shadow',(.055,.065,.06))
    lamp=mat('diffuse light covers',(.84,.84,.74))
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
    # Split the ground storey around a real recess rather than painting a door on a solid box.
    box('six storey structure',0,0,11.225,40.8,13.6,15.75,plaster)
    box('ground left structure',-10.375,0,1.825,20.05,13.6,3.05,plaster)
    box('ground right structure',14.075,0,1.825,12.65,13.6,3.05,plaster)
    box('entry recess back structure',3.7,.65,1.825,8.1,12.3,3.05,dark)
    box('flat roof',0,0,19.15,40.3,13.1,.16,roof)
    for y in [-6.65,6.65]:box('roof parapet',0,y,19.55,40.2,.3,1.0,plaster)
    for x in [-20.25,20.25]:box('end parapet',x,0,19.55,.3,13.6,1.0,plaster)
    for side in [-1,1]:
        y=side*6.84
        for row in range(6):
            z=1.95+row*3.02
            bays = [(-18.5+i*3.36,2.94) for i in range(12)]
            if side == -1:
                bays = [(x,2.94) for x in [-18.5,-15.14,-11.78,-8.42,-5.06,-1.70]]
                if row > 0: bays += [(3.70,7.05)]
                bays += [(12.85,3.55),(17.05,3.55)]
            for col,(x,w) in enumerate(bays):
                if side==1 and 4.0<x<10.5:continue
                h=1.98
                box('window glass',x,y,z,w,.08,h,rng.choice(glass))
                divisions = 6 if w>6 else 3
                for j in range(divisions+1):
                    dx=-w/2+j*w/divisions
                    box('window mullions',x+dx,y+side*.06,z,.045,.10,h,frame)
                for dz in [-h/2,.40,h/2]:box('window transoms',x,y+side*.06,z+dz,w,.10,.055,frame)
                box('projecting sills',x,y,z-h/2-.07,w+.13,.25,.10,grey)
                # Narrow quiet curtain strips sit on the front of opaque proxy glazing.
                if (row+col)%3 != 1:
                    for dx in [-w*.40,w*.40]:
                        box('curtain panels',x+dx,y+side*.047,z-.08,w*.12,.012,1.70,curtain)
        for row in range(4):
            for col in range(59):
                x=-20.1+col*.69+(row%2)*.30
                if x>20.3:continue
                if side==-1 and -.7<x<8.1:continue
                box('sandstone plinth',x,y,.25+row*.19,.66,.16,.175,rng.choice(brick))
    # Projecting balconies above the entrance through the top storey.
    for level in range(1,6):
        z=.7+level*3.02
        box('balcony slab',3.7,-7.8,z,8.1,2.35,.24,plaster)
        box('balcony front',3.7,-8.9,z+.49,8.1,.22,.82,plaster)
        for x in [-.24,7.64]:box('balcony returns',x,-7.85,z+.49,.22,2.1,.82,plaster)
        rail('balcony handrails',(-.24,-8.92,z+1.15),(7.64,-8.92,z+1.15),.035,frame)
        for i in range(17):rail('balcony posts',(-.24+i*.49,-8.92,z+.9),(-.24+i*.49,-8.92,z+1.15),.025,frame)
        for x in [-.24,7.64]:
            rail('balcony side handrails',(x,-8.92,z+1.15),(x,-6.9,z+1.15),.035,frame)
            box('balcony return glazing',x,-7.05,z+1.60,.075,.62,2.25,glass[1])
            for yy in [-7.38,-6.73]:box('balcony return frames',x,yy,z+1.6,.10,.045,2.25,frame)
        for x in [1.4,5.7]:box('balcony soffit lights',x,-7.9,z-.135,1.2,.12,.025,lamp)
    # Sheet-clad vertical shaft to the right of the entrance.
    box('front shaft',9.25,-7.1,10.35,2.45,1.1,20.1,plaster)
    for z in [i*.9+.4 for i in range(23)]:box('shaft horizontal joints',9.25,-7.665,z,2.45,.014,.018,seam)
    for x in [8.07,9.25,10.43]:box('shaft vertical joints',x,-7.67,10.35,.018,.015,20.1,seam)
    for z in [i*.9+.4 for i in range(23)]:
        for x in [8.015,10.485]:box('shaft side joints',x,-7.1,z,.018,1.1,.018,seam)
    rail('balcony drainpipe',(7.86,-7.4,.9),(7.86,-7.4,19.2),.045,grey)
    box('shaft top vent',9.25,-7.69,19.5,1.48,.05,.65,frame)
    for i in range(8):box('vent louvers',9.25,-7.73,19.23+i*.075,1.45,.04,.025,grey)
    # Rear stair tower: four tall slots per floor, roof guardrail.
    box('rear stair tower',6.8,7.0,10.85,5.7,.9,21.1,plaster)
    for row in range(5):
        for col in range(4):
            x=4.9+col*1.25;z=4.95+row*3.02
            box('stair slot frames',x,7.48,z,.43,.09,2.30,frame)
            box('stair slot glazing',x,7.54,z,.34,.045,2.18,glass[(row+col)%4])
            for dz in [-.36,.38]:box('stair slot transom',x,7.58,z+dz,.4,.05,.045,frame)
        box('stair sill ledges',6.8,7.5,3.73+row*3.02,5.5,.23,.10,grey)
    for i in range(23):rail('roof stair guardrail',(4.05+i*.25,7.35,21.4),(4.05+i*.25,7.35,22.1),.02,frame)
    rail('roof stair guardrail',(4.05,7.35,22.1),(9.55,7.35,22.1),.03,frame)
    for x in [-19.25,19.25]:
        rail('roof perimeter rail',(x,-6.3,20.12),(x,6.3,20.12),.024,frame)
    for row in range(3):
        box('rear small end windows',-19.15,6.94,7.0+row*3.02,.85,.09,.48,frame)
        box('rear small end glazing',-19.15,7.0,7.0+row*3.02,.72,.045,.36,glass[1])
    # Main door, steps and wheelchair ramp.
    box('entry glazing',3.7,-6.10,1.95,6.5,.13,2.65,glass[2])
    box('entry recess floor',3.7,-6.65,.70,8.1,2.3,.16,grey)
    for x in [.5,2.1,3.7,5.3,6.9]:box('entry door frames',x,-6.20,1.95,.065,.10,2.65,frame)
    for x in [3.45,3.95]:rail('entry door handles',(x,-6.30,1.3),(x,-6.30,1.85),.022,grey)
    box('entry door transom',3.7,-6.20,2.75,6.5,.1,.055,frame)
    for x in [-.24,7.64]:box('entry portal columns',x,-7.7,1.98,.22,2.1,2.7,plaster)
    for i in range(4):box('entry steps',3.7,-8.0-i*.31,.5925-i*.1175,8.1,.62,.14,grey)
    mesh('accessible ramp',[(-10,-7.2,.30),(-.5,-7.2,.75),(-.5,-8.3,.75),(-10,-8.3,.30)],[(0,1,2,3)],grey)
    for y in [-7.2,-8.3]:
        rail('ramp handrail',(-10,y,1.2),(-.5,y,1.65),.035,frame)
        for i in range(7):rail('ramp posts',(-10+i*1.58,y,.32+i*.075),(-10+i*1.58,y,1.2+i*.075),.025,frame)
    # Rear entrance canopy and blank end walls from the side photograph.
    box('rear door',6.8,7.56,1.7,3.2,.1,2.8,glass[2])
    box('rear canopy',6.8,8.0,3.25,5.8,1.7,.14,frame)
    # Right end entrance photographed behind the sculpture; no extra annex inferred.
    box('side entrance door',20.46,-4.45,1.8,.08,1.75,2.55,glass[2])
    for y in [-5.34,-4.45,-3.56]:box('side entrance frames',20.52,y,1.8,.1,.045,2.55,frame)
    box('side entrance transom',20.53,-4.45,2.65,.1,1.8,.06,frame)
    box('side canopy roof',21.18,-4.45,3.28,1.65,2.7,.09,grey)
    for y in [-5.65,-5.05,-4.45,-3.85,-3.25]:
        box('side canopy ribs',21.18,y,3.18,1.65,.065,.14,frame)
        rail('side canopy braces',(20.52,y,2.7),(21.65,y,3.18),.025,frame)
    for i in range(4):box('side entrance steps',20.68+i*.30,-4.45,.59-i*.13,.95,2.5,.16,grey)
    box('side entrance paving',21.65,-4.45,.24,2.6,3.7,.14,grey)
    for y in [-5.65,-3.25]:
        rail('side stair handrail',(20.55,y,1.63),(22.05,y,1.05),.03,grey)
        for i in range(3):rail('side stair posts',(20.65+i*.65,y,.60-i*.22),(20.65+i*.65,y,1.59-i*.25),.025,grey)
    for x in [-20.43,20.43]:
        for row in range(4):
            for col in range(19):
                y=-6.45+col*.69
                if x>0 and -5.7<y<-3.2:continue
                box('side sandstone plinth',x,y,.25+row*.19,.16,.66,.175,brick[(row+col)%3])
    box('sandstone plinth coping',0,6.96,.94,40.8,.30,.12,brick[1])
    for x,w in [(-10.375,20.05),(14.075,12.65)]:box('sandstone plinth coping',x,-6.96,.94,w,.30,.12,brick[1])
    box('forecourt paving',0,-10.9,.24,41.5,8.2,.14,grey)
    for i in range(42):box('paving joints',-20.5+i,-10.9,.316,.012,8.2,.006,seam)
    for j in range(9):box('paving joints',0,-14.9+j,.317,41.5,.012,.006,seam)
    # Connected two-lobed raised bed, with a slightly pinched waist.
    def outline(t):
        r=1+.17*math.cos(2*t)+.07*math.cos(3*t)
        return (9+5.9*r*math.cos(t),-11.7+2.65*r*math.sin(t))
    n=112; pts=[outline(i*math.tau/n) for i in range(n)]
    mesh('flowerbed soil',[(9,-11.7,.53)]+[(x,y,.53) for x,y in pts],[(0,i+1,(i+1)%n+1) for i in range(n)],soil)
    for i,(x,y) in enumerate(pts):
        nx,ny=pts[(i+1)%n];angle=math.atan2(ny-y,nx-x)
        for row in range(2):
            box('dark stone flowerbed edging',(x+nx)/2,(y+ny)/2,.34+row*.16,math.hypot(nx-x,ny-y)*.96,.23,.15,stone,angle)
        box('flowerbed coping',(x+nx)/2,(y+ny)/2,.59,math.hypot(nx-x,ny-y)*.99,.29,.07,pages,angle)
    def leaf(x,y,z,size,m):
        a=rng.random()*math.tau;c=math.cos(a)*size;s=math.sin(a)*size
        mesh('flowerbed foliage',[(x-c,y-s,z),(x-s*.4,y+c*.4,z+.06),(x+c,y+s,z+.03),(x+s*.4,y-c*.4,z-.02)],[(0,1,2),(0,2,3)],m)
    for i in range(4200):
        t=rng.random()*math.tau;r=math.sqrt(rng.random());bx,by=outline(t);x=9+(bx-9)*r;y=-11.7+(by+11.7)*r
        if (x-11.7)**2+(y+10.8)**2<1.55:continue
        z=.64+rng.random()*.16
        for j in range(3):leaf(x+rng.uniform(-.12,.12),y+rng.uniform(-.12,.12),z+j*.045,rng.uniform(.10,.18),rng.choice(greens))
        if r>.88 and i%5==0 or x>10 and i%19==0:
            for j in range(4):leaf(x+rng.uniform(-.05,.05),y+rng.uniform(-.05,.05),z+.19,.043,pink if r>.78 else purple)
    # Sculpture: rough plinth, seven offset books, upright clock volume.
    sx,sy=11.7,-10.8
    box('sculpture black footing',sx,sy,.68,2.95,2.25,.18,stone)
    box('sculpture granite pedestal',sx,sy,1.29,2.42,1.8,1.08,base)
    for i in range(7):
        z=1.96+i*.43;a=math.radians([0,-10,7,-14,11,-7,4][i]);w=[2.5,2.75,2.65,2.9,2.6,2.85,2.5][i]
        dx=[0,-.14,.18,-.25,.18,.09,-.15][i]
        # Concave page fore-edges give the stone books their distinctive profile.
        verts=[]
        for k in range(7):
            inset=.27*math.sin(k*math.pi/6)
            for xx,yy in [(-(w-.14)/2,-.79+inset),((w-.14)/2,-.79+inset),((w-.14)/2,.79),(-(w-.14)/2,.79)]:
                verts.append((sx+dx+xx*math.cos(a)-yy*math.sin(a),sy+xx*math.sin(a)+yy*math.cos(a),z-.15+k*.05))
        faces=[(3,2,1,0),(24,25,26,27)]+[(k*4+j,k*4+(j+1)%4,(k+1)*4+(j+1)%4,(k+1)*4+j) for k in range(6) for j in range(4)]
        mesh('curved book page blocks',verts,faces,pages)
        for dz in [-.1775,.1775]:box('overhanging book covers',sx+dx,sy,z+dz,w,1.78,.055,stone,a)
        box('book rear spine',sx+dx-.82*math.sin(a),sy+.82*math.cos(a),z,w-.05,.14,.32,stone,a)
        for dz in [-.10,-.05,0,.05,.10]:
            yy=-.805+.27*math.cos(dz/.15*math.pi/2)
            box('engraved page strata',sx+dx-yy*math.sin(a),sy+yy*math.cos(a),z+dz,w-.2,.018,.010,stone,a)
    clock_z=5.645
    box('upright clock book',sx,sy,clock_z,1.32,.48,1.80,stone)
    box('clock spine',sx-.69,sy,clock_z,.09,.55,1.83,pages)
    for i in range(12):
        a=i*math.tau/12;cx=sx+.48*math.sin(a);cz=clock_z+.59*math.cos(a)
        rail('clock hour marks',(cx,sy-.26,cz),(sx+.38*math.sin(a),sy-.26,clock_z+.47*math.cos(a)),.035,white)
    rail('clock minute hand',(sx,sy-.29,clock_z),(sx+.48,sy-.29,clock_z),.035,white)
    rail('clock hour hand',(sx,sy-.30,clock_z),(sx-.30,sy-.30,clock_z+.22),.045,white)
    objects=[]
    for (name,m),(vs,fs) in batches.items():
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update()
        o=bpy.data.objects.new('T4 '+name,me);bpy.context.scene.collection.objects.link(o);o['building_id']='17';objects.append(o)
    # Real lettering on the first balcony, converted to geometry for GLB.
    fontpath=next((str(p) for p in [Path('C:/Windows/Fonts/simkai.ttf'),Path('/System/Library/Fonts/STHeiti Medium.ttc')] if p.exists()),None)
    if not fontpath:raise RuntimeError('Chinese font required for teaching4 lettering')
    font=bpy.data.fonts.load(fontpath)
    c=bpy.data.curves.new('第四教学楼','FONT');c.body='第 四 教 学 楼';c.align_x='CENTER';c.size=.45;c.extrude=.012
    if font:c.font=font
    o=bpy.data.objects.new('T4 entrance lettering',c);bpy.context.scene.collection.objects.link(o);o.location=(3.7,-9.03,4.02);o.rotation_euler=(math.pi/2,0,0);c.materials.append(gold)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object;o['building_id']='17';objects.append(o)
    return objects
