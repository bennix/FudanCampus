"""Evidence-linked local survey frame. Units are provisional metres, not survey measurements."""
from pathlib import Path
import json,math,statistics
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'field-review/guanghua-lawn-survey-v1'
rows=json.loads((OUT/'photos.json').read_text(encoding='utf-8'))
segments=[
 ('S0','南侧入口与边界',4312,4322,'南侧道路、树带、草坪边步道与主楼定位','context', [4312,4315,4320,4322]),
 ('SW0','西南角与玻璃入口',4323,4335,'鼎形雕塑远景、南侧玻璃罩、外围步道','context',[4323,4329,4332,4335]),
 ('W1','西花园南段曲径',4336,4365,'曲径、鼎形雕塑、长椅、采光顶、支路','geometry',[4338,4348,4354,4363]),
 ('W2','西花园高台与双采光顶',4366,4398,'两段台阶、X形栏杆、拼石平台、绿篱和玻璃采光顶','geometry',[4368,4378,4384,4395,4398]),
 ('W3','西路与自行车库',4399,4437,'西侧路口、玻璃入口、两处自行车库门、挡土墙','geometry',[4400,4409,4416,4424,4433]),
 ('NW','西北广场与花园连接',4438,4470,'北广场、采光顶、围栏开口、踏步石、花钵、建筑雕塑','geometry',[4445,4453,4455,4464,4467]),
 ('N0','楼前高处俯拍',4471,4479,'南向总览；用于约束草坪与广场布局','primary',[4474,4475,4479]),
 ('NE','北广场东端',4480,4496,'广场转角、花钵、东侧建筑雕塑、草坪起点','geometry',[4482,4484,4492,4496]),
 ('E0','东侧草坪边步道',4497,4521,'东边界、采光顶、围栏开口、东南角','geometry',[4498,4505,4514,4518,4519]),
 ('SE','东南外侧道路',4522,4533,'外围行道树、路口、标识、园路出口','context',[4523,4529,4533]),
 ('E1','东侧藤架车库入口',4534,4554,'下行车道、藤架、挡墙、树池环形座椅','geometry',[4539,4547,4553]),
 ('E2','东花园阶梯高台',4555,4571,'外侧台阶、错层平台、弧形花池、长椅、内侧园路','geometry',[4556,4562,4566,4568]),
 ('E3','东花园内侧曲径',4572,4587,'采光顶、围栏、灌木与曲径接草坪边','geometry',[4574,4578,4582,4585]),
 ('S1','南边界回程',4588,4602,'东南角至南中央；草坪全景、花坛、行道树','context',[4590,4597,4600,4602]),
 ('S2','南中央标识与花坛',4603,4616,'FUDAN装置、石球、倾斜花架、树下座椅','geometry',[4603,4605,4609,4613])]
zones=[]
for zid,name,start,end,desc,role,keys in segments:
    group=[r for r in rows if start<=r['number']<=end]
    zones.append(dict(id=zid,name=name,start=start,end=end,description=desc,role=role,primary_photos=keys,count=len(group),confidence='inferred spatial assignment; visually reviewed sequence'))
    for r in group:
        e=(r['lon']-121.50113)*111320*math.cos(math.radians(31.3))
        n=(r['lat']-31.30070)*111320;t=math.radians(18)
        r.update(zone=zid,zone_name=name,subject_group=desc,role='primary' if r['number'] in keys else role,
                 review='contact-sheet reviewed',x=round(math.cos(t)*e+math.sin(t)*n,3),y=round(-math.sin(t)*e+math.cos(t)*n,3),
                 local_heading=(r['heading']+18)%360,
                 position_status='raw EXIF GPS projected; not snapped to a path',subject_position_status='zone-level association, not an exact object coordinate')
features=[
 ('LAWN','主草坪',[22,50],'lawn',[4315,4474,4494,4519],[-25,16,70,87]),
 ('PLAZA','北广场',[20,97],'plaza',[4455,4474,4479,4480],[-83,87,110,105]),
 ('DING','鼎形雕塑',[-35,27],'sculpture',[4323,4347,4348,4349],None),
 ('WPATH','西花园曲径',[-45,43],'path',[4338,4345,4353,4363,4451],None),
 ('WTERR','西花园高台',[-59,57],'terrace',[4368,4377,4378,4380,4395],[-73,43,-47,70]),
 ('WB1','自行车库南门',[-77,48],'entrance',[4416,4419],None),
 ('WB2','自行车库北门',[-77,70],'entrance',[4421,4424,4434],None),
 ('WGLASS','西南玻璃罩',[-57,7],'glass',[4329,4332,4335],None),
 ('WGLASS2','西侧玻璃入口',[-72,28],'glass',[4409,4410],None),
 ('WSKY1','西侧采光顶南',[-34,43],'skylight',[4354,4357],None),
 ('WSKY2','西北并排双采光顶',[-56,83],'skylight',[4445,4448],None),
 ('WOPEN','西北围栏楼梯口',[-31,81],'opening',[4452,4453],None),
 ('EOPEN','东北围栏楼梯口',[79,78],'opening',[4492,4493],None),
 ('ESKY','东侧采光顶',[83,45],'skylight',[4574,4577],None),
 ('ETERR','东花园阶梯高台',[91,53],'terrace',[4556,4559,4562,4566,4568],[84,43,101,66]),
 ('ERAMP','东侧藤架车道',[97,29],'ramp',[4534,4539,4547,4550],[89,18,106,42]),
 ('EPATH','东花园内侧曲径',[80,34],'path',[4578,4582,4584,4585],None),
 ('SIGN','南中央FUDAN装置',[27,10],'sign',[4603,4604,4606],None),
 ('FLOWER','南侧倾斜花架',[38,4],'flower',[4607,4609,4611],None),
 ('WOPEN_S','西侧中段楼梯口',[-32,47],'opening',[4354,4357],None),
 ('EOPEN_S','东侧中段楼梯口',[78,49],'opening',[4505,4506,4574,4577],None)]
features=[dict(id=i,name=n,xy=p,type=k,photos=refs,bounds=b,existence='confirmed in current photos',geometry='inferred provisional dimensions and placement') for i,n,p,k,refs,b in features]
paths=[
 dict(id='west-inner',points=[[-29,16],[-29,78],[-26,87]],width=3.2,photos=[4320,4455]),
 dict(id='east-inner',points=[[73,16],[73,80],[70,87]],width=3.4,photos=[4492,4498,4518]),
 dict(id='south-inner',points=[[-29,13],[73,13]],width=3.2,photos=[4317,4519,4597]),
 dict(id='west-garden',points=[[-79,12],[-68,15],[-58,17],[-48,20],[-42,28],[-44,35],[-43,45],[-43,55],[-38,64],[-44,74],[-46,84],[-50,88]],width=1.7,photos=[4336,4338,4345,4353,4363,4447]),
 dict(id='ding-spur',points=[[-43,29],[-36,27],[-30,25]],width=1.4,photos=[4348,4349]),
 dict(id='west-terrace-link',points=[[-43,55],[-49,51],[-53,45]],width=1.8,photos=[4366,4368]),
 dict(id='west-main-link',points=[[-38,64],[-33,65],[-29,67]],width=1.6,photos=[4363,4364]),
 dict(id='east-garden',points=[[73,86],[85,81],[90,72],[88,64],[84,59],[80,53],[83,45],[84,39],[80,32],[84,24],[92,20],[103,18]],width=1.7,photos=[4488,4496,4572,4574,4578,4582,4584]),
 dict(id='east-terrace-link',points=[[80,53],[85,53],[88,54]],width=1.8,photos=[4568,4572]),
 dict(id='east-main-link',points=[[80,32],[76,30],[73,28]],width=1.8,photos=[4582,4585]),
]
data=dict(version=1,scope='South, west and east road enclosure; Guanghua Building along north boundary',frame=dict(origin_lat=31.30070,origin_lon=121.50113,rotation_deg=18,unit='provisional metres',scale_status='NOT MEASURED; GPS and visual proportions only'),bounds=[-88,-10,115,152],zones=zones,features=features,paths=paths,photos=rows)
(OUT/'survey.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
print(f'{len(rows)} photos; {len(zones)} reviewed sequence zones; {len(features)} evidenced features; {len(paths)} provisional path connections')
