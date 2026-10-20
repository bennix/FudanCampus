"""Third teaching building: photo-visible four-floor galleries and courtyard study."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from photo_scene_common import *
ROOT=Path(__file__).resolve().parents[1];reset()
brick=brickmat('red fired brick',(.49,.225,.18));white=mat('off white plaster',(.78,.79,.73),grain=100);grey=mat('concrete paving',(.47,.48,.43),grain=90);dark=mat('dark gallery ceiling',(.045,.055,.05));glass=mat('grey green window glass',(.24,.31,.30),.23);frame=mat('dark bronze window frames',(.10,.105,.09),.35);metal=mat('stainless handrails',(.52,.55,.52),.3);black=mat('black stair rails',(.035,.04,.035));pink=mat('pink paving bands',(.51,.33,.29));cream=mat('cream paving squares',(.62,.63,.51));grout=mat('dark paving joints',(.19,.21,.17));gold=mat('yellow guide lines',(.54,.39,.075));grassmat=mat('autumn lawn',(.29,.36,.16),grain=80);bark=mat('tree bark',(.18,.16,.11),grain=20)
greens=[mat('plant '+str(i),c) for i,c in enumerate([(.10,.22,.075),(.17,.30,.10),(.25,.37,.13),(.12,.23,.16)])]
# Principal gallery block: four storeys, long elevation facing courtyard -Y.
box('upper classroom block',0,5.5,8.8,40,8.8,9.8,brick)
box('ground classrooms left',-11,5.5,1.95,18,8.8,3.1,brick)
box('ground classrooms right',11,5.5,1.95,18,8.8,3.1,brick)
box('entry rear wall',0,8.5,1.95,4,2.8,3.1,white)
for xx in [-11,11]:box('white lower plinth',xx,5.5,.5,18,9,.6,white)
for row in range(4):
    z=.4+row*3.35
    box('open corridor floor',0,.05,z,40.5,2.5,.22,grey)
    box('deep charcoal ceiling',0,.05,z+3.15,40.5,2.5,.12,dark)
    # Actual corridor space between rear classroom wall and outer guard.
    for col in range(11):
        x=-18+col*3.6
        if row==0 and abs(x)<2:continue
        box('classroom glazing',x,1.04,z+1.65,2.8,.08,2.45,glass)
        for dx in [-1.4,-.5,.5,1.4]:box('corridor window mullions',x+dx,.97,z+1.65,.05,.08,2.45,frame)
        for dz in [.45,2.0,2.88]:box('corridor transoms',x,.96,z+dz,2.8,.08,.045,frame)
        if row>0 or abs(x)>3:
            box('white gallery solid balustrade',x,-1.17,z+.55,3.2,.22,1.0,white)
            box('balustrade raised panel',x,-1.30,z+.56,2.8,.035,.60,white)
            rod('gallery steel top rail',(x-1.6,-1.17,z+1.20),(x+1.6,-1.17,z+1.20),.027,metal)
            for k in range(9):rod('gallery rail posts',(x-1.6+k*.4,-1.17,z+1.0),(x-1.6+k*.4,-1.17,z+1.2),.017,metal)
        box('ceiling square downlights',x,-.3,z+3.075,.23,.23,.025,white)
        # Dark slat ceiling, rather than a flat black surface.
        for k in range(9):box('gallery ceiling grid',x-1.5+k*.375,-.05,z+3.07,.025,2.35,.05,frame)
for col in range(12):
    x=-19.8+col*3.6
    box('continuous red brick piers',x,-1.20,7.0,.42,.48,13.9,brick)
    rod('white rainwater pipes',(x+.29,-1.46,.35),(x+.29,-1.46,13.8),.045,white)
    for z in [3.8,7.15,10.5]:box('pipe clips',x+.29,-1.49,z,.12,.07,.04,metal)
box('main projecting cornice',0,4.25,14.0,41,12,.25,white)
for y in [-1.6,10.1]:box('roof parapet',0,y,14.35,40.5,.24,.5,white)
# End facade has long horizontal windows and white floor bands.
for x in [-20.04,20.04]:
    for row in range(4):
        z=2+row*3.35
        box('end horizontal glazing',x,5.4,z,.06,5.4,1.4,glass)
        for yy in [2.7,3.6,4.5,5.4,6.3,7.2,8.1]:box('end mullions',x+(.04 if x>0 else -.04),yy,z,.08,.045,1.4,frame)
        box('end white floor bands',x,5.4,z-1.4,.10,9.1,.25,white)
# Open end stair tower, two return flights per floor.
for x in [-24.8,-20.6]:box('stair red brick blade walls',x,3.6,7,.25,8.8,13.6,brick)
for row in range(3):
    base=.4+row*3.35
    for half in range(2):
        z0=base+half*1.675;x=-23.6+half*1.9;sign=1 if half==0 else -1
        for k in range(10):
            y=3.6+sign*(-1.65+k*.33);zz=z0+(k+1)*.1675
            box('exposed return stair treads',x,y,zz-.10,1.65,.34,.20,white)
        for xx in [x-.8,x+.8]:
            rod('stair steel handrail',(xx,3.6-sign*1.65,z0+1),(xx,3.6+sign*1.65,z0+2.675),.026,metal)
            for k in range(11):rod('stair upright balusters',(xx,3.6+sign*(-1.65+k*.33),z0+k*.1675),(xx,3.6+sign*(-1.65+k*.33),z0+k*.1675+1),.018,metal)
        box('stair half landing',-22.65,3.6+sign*2.3,z0+1.675,3.8,1.2,.22,white)
for x in [-24.7,-20.7]:box('stair front white columns',x,-.2,7,.20,.25,14,white)
box('stair tower flat canopy',-22.7,3.6,14.1,4.8,9,.22,white)
# Main entrance stair is recessed in a genuine opening; wall opening left in facade below.
# Remove the central rear classroom obstruction at ground level by splitting wall locally.
# Classroom body is set back behind the first flight, as in the photos.
for k in range(18):box('central entry stairs',0,-.1+k*.17,.30+k*.12,2.3,.18,.15,grey)
for x in [-1.2,1.2]:
    rod('entry black handrail',(x,-.4,1.1),(x,2.8,3.2),.027,black)
    for k in range(9):rod('entry balusters',(x,-.4+k*.4,.35+k*.26),(x,-.4+k*.4,1.1+k*.26),.018,black)
box('entry title plaque',0,-1.34,4.18,6.6,.06,.78,white);text_obj('第三教学楼',(0,-1.39,3.97),.55,frame)
# Transverse right classroom wing, with visible red piers/white spandrels.
box('right classroom wing',24,-6.3,7,8,24,13.4,brick)
box('right wing cornice',24,-6.3,14,8.6,24.6,.23,white)
for side in [-1,1]:
    x=24+side*4.03
    for row in range(4):
        z=2.1+row*3.35
        for col in range(7):
            y=-16.5+col*3.35
            box('wing white window surrounds',x,y,z,.08,2.9,3.0,white)
            box('wing broad windows',x+side*.055,y,z,.08,2.5,2.25,glass)
            for dy in [-1.25,-.42,.42,1.25]:box('wing vertical mullions',x+side*.11,y+dy,z,.07,.045,2.25,frame)
            box('wing transom',x+side*.11,y,z+.55,.07,2.5,.045,frame)
# Low left volume. User confirmed the modeled annex exterior stair does not exist.
box('two storey annex',-22,-12,3.8,8,17,7.2,brick);box('annex white cornice',-22,-12,7.5,8.5,17.5,.22,white)
for row in range(2):
    for j in range(5):
        y=-18.8+j*3.25;z=2+row*3.5
        box('annex windows',-17.94,y,z,.08,2,2.2,glass)
        box('annex window sills',-17.86,y,z-1.18,.2,2.2,.12,white)
# Square grid paving with pink rectangular motifs, and yellow lane guidance.
box('courtyard base',0,-12,-.1,57,36,.18,grout)
for i in range(142):
    for j in range(81):
        x=-28.2+i*.4;y=-28+j*.4
        if (x+9)**2/6.5**2+(y+17)**2/6**2<1 or (x-8)**2/6**2+(y+9)**2/3.1**2<1:continue
        if x>20 and y>-18 or x<-18 and y>-20:continue
        box('grid paving',x,y,.012,.377,.377,.035,pink if i%12==0 or j%12==0 else cream)
for x in [-.6,2.6]:box('yellow pedestrian guide',x,-18,.04,.10,19,.008,gold)
# Rounded planting islands, red vertical brick curbs.
for x,y,rx,ry in [(-9,-17,6.5,6),(8,-9,6,3.1)]:
    ellipse('planted island lawn',x,y,rx,ry,.18,grassmat)
    for i in range(180):
        a=i*math.tau/180;box('pink vertical brick curb',x+rx*math.cos(a),y+ry*math.sin(a),.14,.20,.12,.30,pink,a)
for x,y in [(4,-9),(8,-10),(11,-8),(7,-7)]:shrub(x,y,1.8,1.2,1.4,greens)
for i in range(34):
    a=i*math.tau/34;rock('garden rock edging',8+6*math.cos(a),-9+3.1*math.sin(a),.22,(.42,.35,.4),grey)
# User close-up confirms a full metal sphere, not a shallow disc.
box('sphere sculpture pedestal',8,-8.6,.95,1.1,.8,1.6,grey)
sphere_metal=mat('weathered silver sphere',(.52,.49,.43),.29)
next(n for n in sphere_metal.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Metallic'].default_value=.85
bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=.83,location=(8,-8.6,2.58))
sphere=bpy.context.object;sphere.name='metal sphere sculpture';sphere.data.materials.append(sphere_metal)
for face in sphere.data.polygons:face.use_smooth=True
sphere['basis']='Full sphere confirmed by user close-up, 2026-10-20; diameter inferred'
sphere.select_set(False)
# Convenience kiosk and gently arched cycle shelter.
box('convenience kiosk',-11,-4,1.5,5.0,3.4,2.8,metal);box('kiosk glass',-11,-5.74,1.5,4.7,.08,2.5,glass)
awning=mat('deep green shop awning',(.035,.17,.10));box('green kiosk fascia',-11,-6,2.7,5.7,.5,.3,awning);text_obj('全家 FamilyMart',(-11,-6.27,2.63),.23,white)
mesh('kiosk pitched canopy',[(-14,-6.3,2.8),(-8,-6.3,2.8),(-8,-2,2.8),(-14,-2,2.8),(-14,-4,3.5),(-8,-4,3.5)],[(0,1,5,4),(4,5,2,3)],awning)
for y in [-24,-21,-18]:
    for x in [-16,-12]:rod('cycle shelter columns',(x,y,0),(x,y,2.6),.04,metal)
    pts=[]
    for k in range(17):pts.append((-16+4*k/16,y,2.6+1.0*math.sin(k*math.pi/16)))
    for a,b in zip(pts,pts[1:]):rod('arched cycle shelter ribs',a,b,.035,metal)
for k in range(16):
    x=-16+4*k/16;nx=x+.25;z=2.6+math.sin(k*math.pi/16);nz=2.6+math.sin((k+1)*math.pi/16)
    mesh('translucent cycle shelter',[(x,-24,z),(nx,-24,nz),(nx,-18,nz),(x,-18,z)],[(0,1,2,3)],cream)
tree(-9,-17,12,'cedar',bark,greens)
for x,y,h in [(16,-15,7),(17,-10,8),(15,-19,6.5),(-15,-13,7),(-13,-19,6)]:tree(x,y,h,'palm',bark,greens)
for i in range(160):
    a=R.random()*math.tau;r=R.random()**.5;grass(-9+6*r*math.cos(a),-17+5.5*r*math.sin(a),R.choice(greens))
finish(ROOT/'field-review/teaching3-photo-v1','teaching3',[('courtyard',(-32,-45,23),(0,-3,4)),('gallery',(13,-27,9),(0,1,6)),('stairs',(-38,-12,12),(-22,2,6)),('sculpture',(12,-15,4.5),(8,-8.6,1.9))])
