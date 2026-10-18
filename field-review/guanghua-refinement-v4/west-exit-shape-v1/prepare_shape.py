"""One local photo-led shape edit, using the existing mesh helper only."""
import sys,json,math
from pathlib import Path
import shapely as S
from shapely.geometry import LineString,Polygon,box,mapping
O=Path(__file__).resolve().parent;OLD=O.parent/'road-rebuild-v1'
sys.path.insert(0,str(OLD))
from road_geometry import triangulate,extrude,smoothstep

# IMG_4568/4572: move forward off the stair, then bend left around the skylight.
controls=[(84.95,47.8),(83.2,47.8),(82.2,46.7),(82.0,45.0),(81.2,42.8),(78.6,40.9),(75.3,40.0),(73.8,40.0)]
def curve(points):
    out=[];p=[points[0]]+points+[points[-1]]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for j in range(20):
            t=j/20
            out.append(tuple(.5*(2*b[k]+(-a[k]+c[k])*t+(2*a[k]-5*b[k]+4*c[k]-d[k])*t*t+(-a[k]+3*b[k]-3*c[k]+d[k])*t*t*t) for k in [0,1]))
    return out+[points[-1]]
pts=curve(controls);line=LineString(pts)
road=line.buffer(.82,cap_style='flat',join_style='round').intersection(box(73.8,35,84.95,60))
# Local garden level is continuous across road and planted ground, not a narrow road mound.
# Existing eastern entry stairs are retained; absolute terrain registration remains inferred.
def level(x,y):
    if x<77.0:z=.045+1.205*smoothstep((x-73.8)/3.2)
    elif x<=81.8:z=1.25
    else:z=1.25+.50*smoothstep((x-81.8)/(84.95-81.8))
    if x>84.95:
        z=z*(1-smoothstep((x-84.95)/(95.5-84.95)))
        z*=1-smoothstep((x-84.95)/3)*(1-smoothstep((y-37)/7))
    fade=smoothstep((y-35)/5)*smoothstep((59-y)/5)
    return -.005+(z+.005)*fade
baseline=json.loads((OLD/'baseline-geometry.json').read_text())
DX=-6.697882438088101
exclude=[]
for o in baseline:
    if o['id']=='EOPEN_S' and 'coping' in o['name']:
        b=o['bounds'];exclude.append(box(b[0][0]-DX-.04,b[1][0]-.04,b[0][1]-DX+.04,b[1][1]+.04))
    elif o['id']=='ESKY' and 'plinth' in o['name']:
        b=o['bounds'];exclude.append(box(b[0][0]-DX,b[1][0],b[0][1]-DX,b[1][1]))
ground=box(73.8,35,95.5,59).difference(S.union_all(exclude)).difference(road)
payload={'road':{},'ground':{},'controls':controls,'registration_x':DX,'lift_skylight_and_opening':1.25,'source_photos':[4568,4572,4574,4567],'uncertainty':'Local garden datum and distant connections remain inferred; not a final integrated model.'}
for name,domain in [('road',road),('ground',ground)]:
    v,f,_=triangulate(domain,.35)
    vv,ff=extrude([(x,y,level(x,y)-(0 if name=='road' else .025)) for x,y in v],f,bottom=-.09)
    payload[name]={'vertices':vv,'faces':ff}
payload['removals']=json.loads((OLD/'diagnostic-03/mesh-payload.json').read_text())['removals']
(O/'shape.json').write_text(json.dumps(payload),encoding='utf-8')
print('SHAPE_READY')
