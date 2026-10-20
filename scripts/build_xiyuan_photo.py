"""Independent Xi garden photo study. Layout beyond pond/bridge/pavilion inferred."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from photo_scene_common import *
ROOT=Path(__file__).resolve().parents[1];reset()
stone=[mat('granite '+str(i),c,grain=75) for i,c in enumerate([(.38,.40,.38),(.49,.48,.45),(.31,.34,.33),(.55,.53,.51)])]
white=mat('aged white plaster',(.78,.80,.75),grain=80);red=mat('oxblood lattice',(.24,.035,.045));wood=mat('dark timber bridge',(.065,.075,.068),grain=9);bark=mat('grey brown bark',(.18,.16,.12),grain=12)
greens=[mat('leaf '+str(i),c) for i,c in enumerate([(.10,.20,.09),(.16,.28,.12),(.24,.34,.15),(.11,.24,.17),(.27,.38,.20)])]
lawn=mat('yellow green autumn lawn',(.35,.40,.19),grain=95);soil=mat('dark planting soil',(.09,.12,.065));water=mat('deep green still water',(.045,.115,.085),.17);pink=mat('pink impatiens',(.71,.075,.26));silver=mat('painted pale metal',(.57,.63,.61),.4)
box('ground',0,2,-.18,39,39,.3,lawn)
# Oval pool, coping, irregular stone lining. Bowl above surrounding paving follows photo.
px,py=4,-3;rx,ry=8.6,5.8
ellipse('pond water',px,py,rx-.30,ry-.30,.24,water)
ring('pool masonry',px,py,rx,ry,.36,.08,.55,stone[2])
ring('pool granite coping',px,py,rx+.12,ry+.12,.57,.63,.12,stone[0])
for i in range(112):
    a=i*math.tau/112
    for k in range(2):
        x=px+(rx-.37)*math.cos(a);y=py+(ry-.37)*math.sin(a)
        rock('irregular pool lining',x,y,.22+k*.24,(.31,.15,.15),R.choice(stone))
# Square slabs with exposed pebble joints surrounding pond; preserve the pool hole.
for i in range(38):
    for j in range(29):
        x=-10+i*.72;y=-12+j*.72;q=((x-px)/rx)**2+((y-py)/ry)**2
        if q<1.14 or q>2.4 and not (-7<x<-4):continue
        box('stone paving slabs',x,y,.035,.65,.65,.06,R.choice(stone[:2]))
        for k in range(6):
            rock('pebble paving joints',x-.35,y-.30+k*.12,.035,(.045,.055,.022),R.choice(stone))
            rock('pebble paving joints',x-.30+k*.12,y-.35,.035,(.055,.045,.022),R.choice(stone))
# Low irregular stone ridge separating lotus and clear water.
for i in range(24):
    x=-3.4+i*.61;y=-3.8+.35*math.sin(i*.4);rock('low stone water divider',x,y,.30,(R.uniform(.35,.55),.30,R.uniform(.12,.23)),R.choice(stone))
# Lotus leaves, raised and floating, scalloped radial mesh with folded profiles.
lotus=[mat('lotus '+str(i),c) for i,c in enumerate([(.15,.38,.22),(.25,.45,.25),(.37,.42,.12),(.43,.36,.16)])]
for i in range(155):
    x=R.uniform(-3.5,11);y=R.uniform(-3,2)
    if ((x-px)/(rx-.8))**2+((y-py)/(ry-.8))**2>.93:continue
    z=R.uniform(.55,1.25) if i%3 else .28;s=R.uniform(.22,.52);rod('lotus stems',(x,y,.23),(x,y,z),.014,greens[1]);n=24
    vs=[(x,y,z-.06)]+[(x+s*(1+.025*math.sin(j*5))*math.cos(j*math.tau/n),y+s*(1+.025*math.sin(j*5))*math.sin(j*math.tau/n),z+.02*math.cos(j*3)+.04) for j in range(n)]
    mesh('scalloped lotus leaves',vs,[(0,j+1,(j+1)%n+1) for j in range(n)],R.choice(lotus))
# Short bridge runs across rear neck, with actual plank gaps and X braces.
for i in range(83):box('bridge planks',-2.8+i*.18,-.5,.85,.172,2.0,.12,wood)
for yy in [-1.47,.47]:
    box('bridge side beams',4.6,yy,.63,15.1,.17,.34,wood)
    for zz in [1.03,1.90]:box('bridge horizontal rails',4.6,yy,zz,15.1,.10,.14,wood)
    for i in range(12):
        x=-2.9+i*1.38;box('bridge posts',x,yy,1.40,.16,.16,1.55,wood);box('bridge post caps',x,yy,2.18,.20,.20,.09,wood)
        if i<11:
            rod('bridge X bracing',(x,yy,1.12),(x+1.38,yy,1.85),.055,wood,n=4)
            rod('bridge X bracing',(x,yy,1.85),(x+1.38,yy,1.12),.055,wood,n=4)
# White flat-roof pavilion at left edge of pool, red lintel fretwork.
box('pavilion stone platform',-5,1,.36,5.4,4.4,.32,stone[0]);box('pavilion rear sill',-5,2.7,.95,5,.25,1.2,white)
box('pavilion rear upper wall',-5,2.7,3.35,5,.25,.6,white)
for xx in [-7,-3]:box('pavilion rear side piers',xx,2.7,2.25,1,.25,1.4,white)
for side in [-1,1]:
    x=-5+side*1.5;mesh('fan opening splayed sides',[(x,2.55,1.55),(x-side*.55,2.55,1.55),(x,2.55,2.95)],[(0,1,2)],white)
box('pavilion left return',-7.3,1.2,2.0,.24,3.2,3.1,white)
# Opening in front is genuine open space; freestanding stone column.
rod('pavilion stone column',(-2.8,-.6,.5),(-2.8,-.6,3.9),.16,stone[2],n=20)
box('pavilion broad flat roof',-5,1.0,4.0,6.0,4.7,.22,white)
box('pavilion grey green fascia',-5,-1.30,4.15,6,.13,.30,stone[2])
for yy in [-.72,2.35]:
    box('pavilion red lintel',-5,yy,3.37,4.5,.09,.10,red)
    for i in range(18):
        x=-7.12+i*.25;box('pavilion lattice uprights',x,yy,3.65,.025,.04,.46,red)
        box('pavilion alternating fretwork',x+.12,yy,3.55+(i%2)*.20,.23,.04,.025,red)
# Two stone-clad screen panels with narrow opening; terrace benches.
for x in [-2.1,.0]:
    box('pavilion screen wall',x,1.35,1.7,1.3,.20,2.45,stone[0])
    for i in range(5):
        for j in range(8):rock('screen mosaic stones',x-.5+i*.25,1.22,.65+j*.28,(.14,.06,.17),R.choice(stone))
for yy in [-1.1,1.8]:
    box('waterside stone bench',-2.0,yy,.95,3.2,.45,.14,stone[2])
    for x in [-3,-1]:box('stone bench legs',x,yy,.65,.20,.32,.5,stone[2])
for i in range(16):
    a=R.random()*math.tau;r=R.random()*1.4
    rock('Taihu rockery',-3.2+r*math.cos(a),-2.8+r*math.sin(a),.4+R.random()*1.25,(R.uniform(.3,.6),R.uniform(.25,.5),R.uniform(.4,1.1)),R.choice(stone))
# Raised curved flower bed.
ellipse('flowerbed soil',12,6,4,1.5,.38,soil);ring('flowerbed stone rim',12,6,4.2,1.7,.25,.1,.36,stone[0])
for i in range(900):
    a=R.random()*math.tau;r=R.random()**.5;x=12+3.9*r*math.cos(a);y=6+1.4*r*math.sin(a);z=R.uniform(.48,.7)
    leaf('impatiens foliage',x,y,z,.14,R.choice(greens))
    if i%3==0:
        for j in range(5):leaf('pink flowers',x+.045*math.cos(j*1.26),y+.045*math.sin(j*1.26),z+.10,.055,pink)
# Open flag lawn study, spatial relation to pond is explicitly approximate.
ellipse('flag lawn',-8,11,8.2,6.4,.015,lawn)
for i in range(3):box('flagpole red granite steps',-8,11,.12+i*.10,2.5-i*.35,2.1-i*.3,.12,red)
rod('flag pole',(-8,11,.35),(-8,11,10.5),.055,silver,.035,n=16)
for i in range(25):
    for j in range(5):box('red brick entry path',-9+i*.15,4.7+j*.25,.04,.14,.24,.05,stone[i%3])
# Silver lamps and CCTV, timber benches.
for x,y in [(13,2),(-1,8),(-11,-5)]:
    rod('garden light pole',(x,y,.05),(x,y,3.5),.06,silver,n=12)
    ring('lamp circular shade',x,y,.32,.32,.06,3.5,.06,stone[0],n=32)
    rod('lamp diffuser',(x,y,3.18),(x,y,3.48),.11,white,.20,n=12)
for x,y in [(11,-10),(-3,-10)]:
    for k in range(5):box('bench seat slats',x,y+k*.09,.55,1.9,.075,.07,stone[1])
    for k in range(4):box('bench back slats',x,y+.44,.75+k*.13,1.9,.07,.10,stone[1])
    for xx in [x-.7,x+.7]:rod('bench iron legs',(xx,y,.05),(xx,y,.58),.04,wood);rod('bench supports',(xx,y+.43,.05),(xx,y+.43,1.2),.04,wood)
for x,y,h,kind in [(-10,-3,9,'willow'),(13,-5,10,'willow'),(-2,7,11,'willow'),(-16,4,11,'broadleaf'),(16,10,10,'broadleaf'),(-16,16,12,'cedar')]:tree(x,y,h,kind,bark,greens)
for i in range(16):tree(-17+i*2.1,19+R.uniform(-1,1),R.uniform(10,14),'cedar',bark,greens)
for i in range(12):shrub(15+R.uniform(-1,1),10+i*.65,2,1,1.0,greens,350)
for i in range(650):
    x=R.uniform(-18,18);y=R.uniform(-15,20)
    if ((x-px)/(rx+2.5))**2+((y-py)/(ry+2.5))**2>1 and ((x+8)/8.5)**2+((y-11)/6.5)**2>1:grass(x,y,R.choice(greens))
finish(ROOT/'field-review/xiyuan-photo-v1','xiyuan',[('overview',(31,-39,31),(0,3,0)),('pond',(19,-22,9),(1,-1,2)),('pavilion',(10,-12,4.4),(-3,1,2))])
