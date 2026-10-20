"""75 Ye Yaozhen student activity centre: four supplied photos, inferred rear."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from photo_scene_common import *
ROOT=Path(__file__).resolve().parents[1];reset()
tiles=[mat('pink grey ceramic '+str(i),c,grain=120) for i,c in enumerate([(.49,.43,.39),(.56,.49,.45),(.53,.47,.43),(.58,.51,.47)])]
seam=mat('recessed ceramic joints',(.24,.23,.21));white=mat('cream concrete',(.70,.71,.63),grain=65);yellow=mat('pale yellow stair parapet',(.67,.64,.43));black=mat('charcoal frames',(.07,.08,.075),.4);glass=mat('shop glass',(.19,.29,.28),.24);silver=mat('brushed steel',(.47,.51,.49),.25);gold=mat('bronze characters',(.42,.37,.22),.34);red=mat('supermarket red fascia',(.38,.018,.04));paving=mat('grey brick forecourt',(.27,.29,.26),grain=80)
box('forecourt',0,-3,-.15,33,29,.25,paving)
# Semicircular front and shallow rear auditorium body. Front is -Y.
box('inferred rear volume',0,3.1,5.6,20,6.2,11.2,tiles[0])
for z,h,r in [(3.2,.55,10.1),(3.9,2.65,10.0),(6.8,2.65,10.0),(9.7,1.8,10.0)]:
    ring('curved ceramic facade',0,0,r,r,.30,z,h,tiles[1],n=128,start=math.pi,end=math.tau)
for z in [3.77,6.57,9.47]:ring('deep horizontal reveal',0,0,9.85,9.85,.18,z,.16,seam,n=128,start=math.pi,end=math.tau)
# Fine narrow tiles modeled as seams so they survive GLB export.
for k in range(73):
    z=3.25+k*.112
    if any(abs(z-q)<.13 for q in [3.80,6.65,9.55]):continue
    ring('horizontal tile grout',0,0,10.012,10.012,.013,z,.009,seam,n=128,start=math.pi,end=math.tau)
for i in range(490):
    a=math.pi+i*math.pi/490;x=10.014*math.cos(a);y=10.014*math.sin(a)
    for z,h in [(3.48,.43),(5.20,2.65),(8.10,2.65),(10.60,1.75)]:rod('vertical narrow tile joints',(x,y,z-h/2),(x,y,z+h/2),.004,seam,n=4)
# Recessed ground floor storefront behind three round ceramic columns.
box('ground floor shop back',0,-3.8,1.65,18.6,.3,3.3,white)
box('shop glass storefront',0,-6.6,1.5,14.0,.08,2.8,glass)
for x in [-6.8,-5.4,-4,-2.6,-1.2,.2,1.6,3,4.4,5.8,6.8]:
    box('shopfront mullions',x,-6.67,1.5,.045,.08,2.8,silver)
    box('glass door handles',x+.18,-6.76,1.35,.025,.035,.45,black)
for z in [.12,1.3,2.9]:box('shop transoms',0,-6.68,z,14,.08,.045,silver)
box('red safety stripe',0,-6.73,1.20,14,.015,.10,red)
for x,y in [(-7.2,-6.5),(2.6,-9),(8.4,-4.8)]:
    rod('round ceramic shop columns',(x,y,0),(x,y,3.27),.44,tiles[1],n=32)
    for k in range(25):ring('column tile joints',x,y,.446,.446,.012,k*.13,.009,seam,n=32)
    for k in range(30):
        a=k*math.tau/30;rod('column vertical joints',(x+.447*math.cos(a),y+.447*math.sin(a),0),(x+.447*math.cos(a),y+.447*math.sin(a),3.25),.004,seam,n=4)
box('red supermarket sign',-2.5,-7.25,2.72,7.9,.15,.65,red)
text_obj('复旦大学学生超市',(-2.5,-7.35,2.65),.37,white)
text_obj('FUDAN UNIVERSITY CAMPUS SUPERMARKET',(-2.5,-7.36,2.51),.085,white)
text_obj('勤工助学',(5.1,-6.85,2.94),.38,black)
# Bronze signage follows the curved front.
for label,z,spacing,size in [('叶耀珍',8.0,1.4,.58),('学生活动中心',5.25,1.25,.60)]:
    for i,ch in enumerate(label):
        x=(i-(len(label)-1)/2)*spacing;a=-math.pi/2+math.asin(x/10.05)
        text_obj(ch,(10.05*math.cos(a),10.05*math.sin(a),z),size,gold,a+math.pi/2)
# Roof parapet with photographed central open railing.
ring('roof parapet left',0,0,10.02,10.02,.3,11.45,.75,tiles[1],n=45,start=math.pi,end=4.48)
ring('roof parapet right',0,0,10.02,10.02,.3,11.45,.75,tiles[1],n=45,start=4.94,end=math.tau)
for z in [11.57,11.88,12.18]:ring('roof opening horizontal rails',0,0,10,10,.035,z,.035,silver,n=24,start=4.48,end=4.94)
for i in range(7):
    a=4.48+i*.46/6;rod('roof rail posts',(10*math.cos(a),10*math.sin(a),11.45),(10*math.cos(a),10*math.sin(a),12.20),.025,silver)
ellipse('roof deck',0,0,9.7,9.7,11.47,seam)
# Tall narrow left stair cylinder / glazed slot.
rod('left pale vertical stair tower',(-10.2,-.8,0),(-10.2,-.8,12.2),.78,white,n=48)
box('left glazed vertical slot',-9.3,-2,6.3,1.1,.12,9.5,glass)
for z in range(2,12):box('left slot transoms',-9.3,-2.08,z,1.15,.08,.06,silver)
# Right exterior stairs lead up to raised side entrance.
for i in range(22):box('side exterior staircase',12,-8+i*.30,(i+1)*.15/2,2.8,.31,(i+1)*.15,tiles[0])
box('upper stair landing',12,-.7,3.23,3,2,.16,white)
for x in [10.5,13.5]:
    vs=[(x,-8.2,0),(x,-8.2,.8),(x,-1.4,4.1),(x,-1.4,3.3)]
    mesh('sloping yellow stair parapets',vs,[(0,1,2,3)],yellow)
box('side connecting canopy',12,2,3.9,4.2,5.6,.30,yellow)
for x in [10.7,13.4]:rod('canopy round columns',(x,3,0),(x,3,3.8),.23,tiles[1],n=24)
# Small shop objects rather than temporary advertising content.
for x,m in [(7.0,yellow),(7.5,white)]:box('parcel vending lockers',x,-6.9,1.05,.45,.5,2.1,m)
for x in [-5,-.5]:
    box('A board frame',x,-8.1,.65,.65,.10,1.15,black);box('A board face',x,-8.16,.65,.58,.015,1.05,white)
for i in range(60):
    y=-15+i*.35
    for j in range(64):
        x=-16+j*.5
        if y>-8 and abs(x)<11:continue
        box('forecourt brick joints',x,y,-.018,.012,.34,.012,seam)
    box('forecourt horizontal joints',0,y,-.018,32,.012,.012,seam)
finish(ROOT/'field-review/yeyaozhen-photo-v1','yeyaozhen',[('front',(22,-35,9),(0,-1,5)),('front-close',(-15,-29,7),(0,-3,5.8)),('side',(29,-7,13),(4,0,5))])
