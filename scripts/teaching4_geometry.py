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
    light_frame=mat('rear ground light aluminium',(.55,.56,.52),.45)
    lawn=mat('west lawn',(.19,.31,.075))
    bark=mat('tree bark',(.16,.12,.075))
    leaf_paths=[Path(__file__).resolve().parents[1]/'textures/campus-leaves.png',
                Path(__file__).resolve().parents[1]/'assets/vegetation/teaching4-leaf-cluster.png']
    leaf_path=next((p for p in leaf_paths if p.exists()),None)
    if leaf_path is None:raise RuntimeError('Missing reused campus leaf alpha texture')
    leaf_image=bpy.data.images.load(str(leaf_path));leaf_image.pack()
    tree_mats=[]
    for i,c in enumerate([(.12,.24,.055),(.19,.30,.075),(.25,.36,.10)]):
        m=mat('tree leaves '+str(i),c,1)
        shader=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
        texture=m.node_tree.nodes.new('ShaderNodeTexImage');texture.image=leaf_image
        clip=m.node_tree.nodes.new('ShaderNodeMath');clip.operation='GREATER_THAN';clip.inputs[1].default_value=.45
        m.node_tree.links.new(texture.outputs['Alpha'],clip.inputs[0])
        m.node_tree.links.new(clip.outputs[0],shader.inputs['Alpha'])
        m.use_backface_culling=False
        tree_mats.append(m)
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
    # User round-2 plan: the wing east of the front shaft is recessed 3.2 m.
    box('six storey structure',-4.95,0,11.225,30.9,13.6,15.75,plaster)
    box('setback east wing',15.45,1.6,11.225,9.9,10.4,15.75,plaster)
    box('ground left structure',-10.375,0,1.825,20.05,13.6,3.05,plaster)
    box('ground right structure',9.125,0,1.825,2.75,13.6,3.05,plaster)
    box('setback east ground structure',15.45,1.6,1.825,9.9,10.4,3.05,plaster)
    # This body also forms the rear exterior; dark entry fill caused the marked black surround.
    box('entry recess back structure',3.7,.65,1.825,8.1,12.3,3.05,plaster)
    box('flat roof',-4.825,0,19.15,30.65,13.1,.16,roof)
    box('setback east flat roof',15.325,1.6,19.15,9.65,9.9,.16,roof)
    box('roof parapet',0,6.65,19.55,40.2,.3,1.0,plaster)
    box('roof parapet',-4.95,-6.65,19.55,30.3,.3,1.0,plaster)
    box('setback front parapet',15.3,-3.45,19.55,9.6,.3,1.0,plaster)
    box('setback notch parapet',10.35,-5.05,19.55,.3,3.5,1.0,plaster)
    box('end parapet',-20.25,0,19.55,.3,13.6,1.0,plaster)
    box('end parapet',20.25,1.6,19.55,.3,10.4,1.0,plaster)
    for side in [-1,1]:
        y=side*6.84
        for row in range(6):
            z=1.95+row*3.02
            # Reserve a separate end strip for the three small half-level windows.
            bays = [(-16.8+i*(18.8/6),2.75) for i in range(7)] + [(x,2.9) for x in [11.5,14.9,18.3]]
            if side == -1:
                bays = [(x,2.94) for x in [-18.5,-15.14,-11.78,-8.42,-5.06,-1.70]]
                if row > 0: bays += [(3.70,7.05)]
                bays += [(12.85,3.55),(17.05,3.55)]
            for col,(x,w) in enumerate(bays):
                h=1.98
                wy=-3.64 if side==-1 and x>10.5 else y
                marked_window=side==1 and row==0 and abs(x-2.0)<.01
                if marked_window:wy=6.81
                window_frame=light_frame if side==1 and row==0 else frame
                frame_width=.028 if side==1 and row==0 else .045
                box('rear entry-adjacent glazing' if marked_window else 'window glass',x,wy,z,w,.018 if marked_window else .08,h,rng.choice(glass))
                divisions = 6 if w>6 else 3
                for j in range(divisions+1):
                    if marked_window and j in (0,divisions):continue
                    dx=-w/2+j*w/divisions
                    box('window mullions',x+dx,wy+side*(.027 if marked_window else .06),z,frame_width,.018 if marked_window else .10,h,window_frame)
                for dz in ([.40] if marked_window else [-h/2,.40,h/2]):box('window transoms',x,wy+side*(.027 if marked_window else .06),z+dz,w,.018 if marked_window else .10,frame_width,window_frame)
                if not marked_window:box('projecting sills',x,wy,z-h/2-.07,w+.13,.25,.10,grey)
                if marked_window:
                    # Pale aluminium perimeter; corners butt together without coplanar overlap.
                    for dx in [-w/2,w/2]:box('rear restored light perimeter',x+dx,6.855,z,.028,.09,h-.028,light_frame)
                    for dz in [-h/2,h/2]:box('rear restored light perimeter',x,6.855,z+dz,w+.028,.09,.028,light_frame)
                # Narrow quiet curtain strips sit on the front of opaque proxy glazing.
                if not marked_window and (row+col)%3 != 1:
                    for dx in [-w*.40,w*.40]:
                        box('curtain panels',x+dx,wy+side*.047,z-.08,w*.12,.012,1.70,curtain)
        for row in range(4):
            for col in range(59):
                x=-20.1+col*.69+(row%2)*.30
                if x>20.3:continue
                if side==-1 and -.7<x<8.1:continue
                py=-3.64 if side==-1 and x>10.5 else y
                box('sandstone plinth',x,py,.25+row*.19,.66,.16,.175,rng.choice(brick))
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
        rail('roof perimeter rail',(x,-3.1 if x>0 else -6.3,20.12),(x,6.3,20.12),.024,frame)
    for row in range(3):
        box('rear small end windows',-19.25,6.94,9.50+row*3.02,.85,.09,.48,frame)
        box('rear small end glazing',-19.25,7.0,9.50+row*3.02,.72,.045,.36,glass[1])
        box('rear small end divider',-19.25,7.04,9.50+row*3.02,.03,.03,.36,frame)
    # Main door, steps and wheelchair ramp.
    box('entry glazing',3.7,-6.10,1.95,6.5,.13,2.65,glass[2])
    box('entry recess floor',3.7,-6.65,.70,8.1,2.3,.16,grey)
    for x in [.5,2.1,3.7,5.3,6.9]:box('entry door frames',x,-6.20,1.95,.065,.10,2.65,frame)
    for x in [3.45,3.95]:rail('entry door handles',(x,-6.30,1.3),(x,-6.30,1.85),.022,grey)
    box('entry door transom',3.7,-6.20,2.75,6.5,.1,.055,frame)
    # The user confirms these porch sides are open; do not add enclosing panels.
    for i in range(3):box('entry steps',3.7,-8.0-i*.31,.5925-i*.1175,8.1,.62,.14,grey)
    mesh('accessible ramp',[(-10,-7.2,.30),(-.5,-7.2,.75),(-.5,-8.3,.75),(-10,-8.3,.30)],[(0,1,2,3)],grey)
    for y in [-7.2,-8.3]:
        rail('ramp handrail',(-10,y,1.2),(-.5,y,1.65),.035,frame)
        for i in range(7):rail('ramp posts',(-10+i*1.58,y,.32+i*.075),(-10+i*1.58,y,1.2+i*.075),.025,frame)
    # Rear entrance canopy and blank end walls from the side photograph.
    box('rear door',6.8,7.56,1.7,3.2,.1,2.8,glass[2])
    box('rear canopy',6.8,8.0,3.25,5.8,1.7,.14,frame)
    for x in [5.22,6.8,8.38]:box('rear glass door frames',x,7.64,1.7,.045,.055,2.8,frame)
    box('rear glass door transom',6.8,7.65,2.65,3.2,.06,.045,frame)
    for x in [6.62,6.98]:rail('rear glass door handles',(x,7.72,1.1),(x,7.72,1.65),.018,grey)
    box('rear entrance landing',6.8,8.05,.48,4.4,1.0,.14,grey)
    box('rear entrance steps',6.8,8.7,.36,4.4,.48,.14,grey)
    box('rear entrance paving',6.8,8.2,.24,6,2.7,.14,grey)
    # Right end entrance photographed behind the sculpture; no extra annex inferred.
    box('side entrance door',20.46,-1.25,1.8,.08,1.75,2.55,glass[2])
    for y in [-2.14,-1.25,-.36]:box('side entrance frames',20.52,y,1.8,.1,.045,2.55,frame)
    box('side entrance transom',20.53,-1.25,2.65,.1,1.8,.06,frame)
    box('side canopy roof',21.18,-1.25,3.28,1.65,2.7,.09,grey)
    for y in [-2.45,-1.85,-1.25,-.65,-.05]:
        box('side canopy ribs',21.18,y,3.18,1.65,.065,.14,frame)
        rail('side canopy braces',(20.52,y,2.7),(21.65,y,3.18),.025,frame)
    for i in range(4):box('side entrance steps',20.68+i*.30,-1.25,.59-i*.13,.95,2.5,.16,grey)
    box('side entrance paving',21.65,-1.25,.24,2.6,3.7,.14,grey)
    for y in [-2.45,-.05]:
        rail('side stair handrail',(20.55,y,1.63),(22.05,y,1.05),.03,grey)
        for i in range(3):rail('side stair posts',(20.65+i*.65,y,.60-i*.22),(20.65+i*.65,y,1.59-i*.25),.025,grey)
    for x in [-20.43,20.43]:
        for row in range(4):
            for col in range(19):
                y=-6.45+col*.69
                if x>0 and (y< -3.6 or -2.5<y<0):continue
                box('side sandstone plinth',x,y,.25+row*.19,.16,.66,.175,brick[(row+col)%3])
    box('sandstone plinth coping',0,6.96,.94,40.8,.30,.12,brick[1])
    for x,w in [(-10.375,20.05),(9.125,2.75)]:box('sandstone plinth coping',x,-6.96,.94,w,.30,.12,brick[1])
    box('sandstone plinth coping',15.45,-3.76,.94,9.9,.30,.12,brick[1])
    box('forecourt paving',0,-10.9,.24,41.5,8.2,.14,grey)
    for i in range(42):box('paving joints',-20.5+i,-10.9,.316,.012,8.2,.006,seam)
    for j in range(9):box('paving joints',0,-14.9+j,.317,41.5,.012,.006,seam)
    box('west forecourt lawn',-10.375,-12.5,.337,20.05,3.2,.035,lawn)
    for y in [-14.15,-10.85]:box('west lawn kerb',-10.375,y,.34,20.05,.10,.06,grey)
    # Connected two-lobed raised bed, with a slightly pinched waist.
    n=112
    raw_x=[(1+.17*math.cos(2*i*math.tau/n)+.07*math.cos(3*i*math.tau/n))*math.cos(i*math.tau/n) for i in range(n)]
    xmin,xmax=min(raw_x),max(raw_x)
    def outline(t):
        r=1+.17*math.cos(2*t)+.07*math.cos(3*t)
        return (7.75+(r*math.cos(t)-xmin)/(xmax-xmin)*12.65,-11.7+2.65*r*math.sin(t))
    pts=[outline(i*math.tau/n) for i in range(n)]
    mesh('flowerbed soil',[(14.075,-11.7,.53)]+[(x,y,.53) for x,y in pts],[(0,i+1,(i+1)%n+1) for i in range(n)],soil)
    for i,(x,y) in enumerate(pts):
        nx,ny=pts[(i+1)%n];angle=math.atan2(ny-y,nx-x)
        for row in range(2):
            box('dark stone flowerbed edging',(x+nx)/2,(y+ny)/2,.34+row*.16,math.hypot(nx-x,ny-y)*.96,.23,.15,stone,angle)
        box('flowerbed coping',(x+nx)/2,(y+ny)/2,.59,math.hypot(nx-x,ny-y)*.99,.29,.07,pages,angle)
    def leaf(x,y,z,size,m):
        a=rng.random()*math.tau;c=math.cos(a)*size;s=math.sin(a)*size
        mesh('flowerbed foliage',[(x-c,y-s,z),(x-s*.4,y+c*.4,z+.06),(x+c,y+s,z+.03),(x+s*.4,y-c*.4,z-.02)],[(0,1,2),(0,2,3)],m)
    for i in range(4200):
        t=rng.random()*math.tau;r=math.sqrt(rng.random());bx,by=outline(t);x=14.075+(bx-14.075)*r;y=-11.7+(by+11.7)*r
        if (x-16.5)**2+(y+10.8)**2<1.55:continue
        z=.64+rng.random()*.16
        for j in range(3):leaf(x+rng.uniform(-.12,.12),y+rng.uniform(-.12,.12),z+j*.045,rng.uniform(.10,.18),rng.choice(greens))
        if r>.88 and i%5==0 or x>16.5 and i%19==0:
            for j in range(4):leaf(x+rng.uniform(-.05,.05),y+rng.uniform(-.05,.05),z+.19,.043,pink if r>.78 else purple)
    # Sculpture: rough plinth, seven offset books, upright clock volume.
    sx,sy=16.5,-10.8
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
    # Photo-supported larger local trees, using the existing campus alpha-leaf asset.
    # Roots and heights are approximate, not surveyed; shared campus sources stay intact.
    tree_specs=[('front broadleaf',-5.0,-12.4,.35,13.5,4.2),
                ('west broadleaf',-16.0,-12.6,.35,10.0,3.0),
                ('east side',25.0,.6,0,9.0,2.8),
                ('rear west',-18.0,10.3,0,9.0,2.8)]
    for index,(label,tx,ty,tz,height,radius) in enumerate(tree_specs):
        tr=random.Random(17100+index)
        fork=tz+height*.37
        rail('Trunk T4 '+label,(tx,ty,tz),(tx+.12,ty-.08,fork),.24 if index==0 else .19,bark)
        for j in range(7):
            a=j*math.tau/7+tr.uniform(-.2,.2)
            mid=(tx+math.cos(a)*radius*.48,ty+math.sin(a)*radius*.38,tz+height*.57)
            end=(tx+math.cos(a)*radius*.83,ty+math.sin(a)*radius*.68,tz+height*tr.uniform(.72,.91))
            rail('Trunk T4 '+label,(tx+.12,ty-.08,fork),mid,.08 if index==0 else .065,bark)
            rail('Trunk T4 '+label,mid,end,.035,bark)
        for j in range(800 if index==0 else 600):
            q=tr.uniform(-1,1);a=tr.random()*math.tau;rr=math.sqrt(1-q*q)
            rad=.22+.78*tr.random()**(1/3)
            center=Vector((tx+math.cos(a)*rr*radius*rad,ty+math.sin(a)*rr*radius*.80*rad,tz+height*.72+q*height*.28*rad))
            normal=Vector((tr.uniform(-1,1),tr.uniform(-1,1),tr.uniform(.25,1))).normalized()
            right=normal.cross(Vector((0,0,1))).normalized();up=normal.cross(right).normalized()
            size=tr.uniform(.38,.60)
            vs=[tuple(center+right*(u*size)+up*(v*size)) for u,v in [(-1,-1),(1,-1),(1,1),(-1,1)]]
            mesh('Canopy T4 '+label,vs,[(0,1,2,3)],tr.choice(tree_mats))
    objects=[]
    for (name,m),(vs,fs) in batches.items():
        me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.materials.append(m);me.update()
        o=bpy.data.objects.new('T4 '+name,me);bpy.context.scene.collection.objects.link(o);o['building_id']='17';objects.append(o)
        if 'Canopy T4' in name or 'Trunk T4' in name:
            o['campusVegetation']=True
            o['photo_source']='teaching4 front, side and rear reference photographs; approximate placement'
        if 'Canopy T4' in name:
            uv=me.uv_layers.new(name='LeafUV')
            for face in me.polygons:
                for li,co in zip(face.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=co
    # Real lettering on the first balcony, converted to geometry for GLB.
    fontpath=next((str(p) for p in [Path('C:/Windows/Fonts/simkai.ttf'),Path('/System/Library/Fonts/STHeiti Medium.ttc')] if p.exists()),None)
    if not fontpath:raise RuntimeError('Chinese font required for teaching4 lettering')
    font=bpy.data.fonts.load(fontpath)
    c=bpy.data.curves.new('第四教学楼','FONT');c.body='第 四 教 学 楼';c.align_x='CENTER';c.size=.45;c.extrude=.012
    if font:c.font=font
    o=bpy.data.objects.new('T4 entrance lettering',c);bpy.context.scene.collection.objects.link(o);o.location=(3.7,-9.03,4.02);o.rotation_euler=(math.pi/2,0,0);c.materials.append(gold)
    bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH');o=bpy.context.object;o['building_id']='17';objects.append(o)
    return objects
