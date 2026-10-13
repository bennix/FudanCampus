"""Generate independently authored footprints and closed stone/planting meshes.

All coordinates are inherited scene units and photographic estimates, not survey data.
Run with .local/road-venv/Scripts/python.exe (Shapely 2.1).
"""
import json, math
from pathlib import Path
from collections import defaultdict
import numpy as np
from shapely import Polygon, Point, LineString, box, constrained_delaunay_triangles
from shapely.ops import split, unary_union

O=Path(__file__).resolve().parent
Y0=109.08; RUN=.36; RISE=(3.45-.035)/22
SPECS={
    'west':dict(label='左坛（西侧，面向楼）',inner=(-46.00,99.45),outer=(-53.60,99.52),
        front=[(-46.00,99.45),(-36.3,98.80),(-17.05,100.25),(-17.05,109.08)],
        side_x=-17.05,side_end=(-17.05,116.12),
        back=[(-17.05,116.12),(-17.05,116.64),(-17.50,116.64),(-18.40,116.64)],
        rear_end=(-31.70,116.64),
        turn=[(-31.70,116.64),(-32.65,116.64),(-33.02,116.20),(-33.48,115.66)],
        outer_path=[(-53.60,99.52),(-53.49,100.05),(-44.70,111.4),(-37.17,120)],
        red_width=3.15,green_height=.50,red_height=.69),
    'east':dict(label='右坛（东侧，面向楼）',inner=(85.70,99.82),outer=(93.47,99.90),
        front=[(85.70,99.82),(76.8,99.13),(57.12,101.02),(57.12,109.30)],
        side_x=57.12,side_end=(57.12,116.06),
        back=[(57.12,116.06),(57.12,116.60),(57.76,116.60),(58.52,116.60)],
        rear_end=(70.94,116.60),
        turn=[(70.94,116.60),(71.97,116.60),(72.63,116.19),(73.52,115.86)],
        outer_path=[(93.47,99.90),(93.16,100.64),(84.32,111.78),(77.16,120)],
        red_width=2.72,green_height=.47,red_height=.65),
}

def bez(q,n=100):
    a,b,c,d=np.array(q,float)
    return [tuple((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*c+t**3*d) for t in np.linspace(0,1,n+1)]
def line(a,b,n=30): return [tuple(np.array(a)*(1-t)+np.array(b)*t) for t in np.linspace(0,1,n+1)]
def polygons(g):
    if g.is_empty:return []
    if g.geom_type=='Polygon':return [g]
    return [p for q in g.geoms for p in polygons(q)]
def clean(g):
    g=g.buffer(0)
    assert g.is_valid and not g.is_empty
    return g
def rounded(g,r=.25):return clean(g.buffer(r,quad_segs=5).buffer(-r,quad_segs=5))

class Plan:
    def __init__(self,key,s):
        self.key=key;self.s=s;self.front=bez(s['front'],110)
        self.side=line(self.front[-1],s['side_end'],50)
        self.rear=bez(s['back'],14)+line(s['back'][-1],s['rear_end'],40)[1:]+bez(s['turn'],18)[1:]
        self.ramp=line(self.rear[-1],s['inner'],70)
        self.loop=self.front+self.side[1:]+self.rear[1:]+self.ramp[1:]
        self.poly=clean(Polygon(self.loop))
        self.parts=[LineString(q) for q in (self.front,self.side,self.rear,self.ramp)]
        self.front_line=self.parts[0];self.stair_line=self.parts[1]
        self.border=LineString(self.loop)
        self.inner=Point(s['inner']);self.outer=Point(s['outer'])
        self.ramp_z=lambda y: .035+3.415*min(1,max(0,(y-100)/20))
        self.rear_z0=.035+(min(21,max(0,int((s['side_end'][1]-Y0)/RUN)))+1)*RISE+.75
        self.rear_z1=self.ramp_z(self.rear[-1][1])+.75
    def distance(self,xy):return [l.distance(Point(xy)) for l in self.parts]
    def wall_height(self,x,y,ymid=None):
        p=Point(x,y);ds=self.distance((x,y));k=min(range(4),key=lambda k:ds[k])
        if k==0:
            t=self.front_line.project(p)/self.front_line.length
            z=.785+(.035+RISE+.75-.785)*(t*t*(3-2*t))+.065*math.sin(math.pi*t)
        elif k==1:
            sy=y if ymid is None else ymid
            stair=.035+(min(21,max(0,int(math.floor((sy-Y0)/RUN))))+1)*RISE
            z=stair+.75
        elif k==2:
            t=self.parts[2].project(p)/self.parts[2].length
            z=self.rear_z0*(1-t)+self.rear_z1*t
        else:z=self.ramp_z(y)+.75
        d=p.distance(self.inner)
        if d<3.0:
            f=min(1,max(0,(d-1.85)/1.15));f=f*f*(3-2*f)
            z=.785+(z-.785)*f
        return z
    def cap_thickness(self,x,y):
        d=self.stair_line.distance(Point(x,y))
        return .13+.05*max(0,1-d/.9)
    def soil_height(self,x,y):
        # Interpolate the low plaza rim, stepped stair side and higher ramp side.
        ds=self.distance((x,y));weights=[1/max(.30,d)**2.8 for d in ds]
        zs=[]
        for k,l in enumerate(self.parts):
            q=l.interpolate(l.project(Point(x,y)))
            if k==0:
                t=l.project(q)/l.length
                z=.785+(.035+RISE+.75-.785)*(t*t*(3-2*t))+.065*math.sin(math.pi*t)
            elif k==1:z=.035+min(22,max(1,(q.y-Y0)/RUN+1))*RISE+.75
            elif k==2:
                t=l.project(q)/l.length;z=self.rear_z0*(1-t)+self.rear_z1*t
            else:z=self.ramp_z(q.y)+.75
            zs.append(z-.11)
        return sum(w*z for w,z in zip(weights,zs))/sum(weights)

def make_solid(name,regions,top,bottom,role,side,mat):
    """Surface union of polygon prisms, including vertical step returns.

    Shared cell walls are removed. Vertical edge subdivision prevents T junctions
    where step levels meet the exterior boundary. No Boolean overlaps are needed.
    """
    verts=[];index={};faces=[];edges=defaultdict(list);zs=defaultdict(set)
    def vi(x,y,z):
        key=(round(x,7),round(y,7),round(z,7))
        if key not in index:index[key]=len(verts);verts.append(key);zs[key[:2]].add(key[2])
        return index[key]
    def levels(x,y,mid):return (bottom(x,y,mid),top(x,y,mid))
    for poly,mid in regions:
        for tr in constrained_delaunay_triangles(poly).geoms:
            xy=list(tr.exterior.coords)[:-1]
            faces.append([vi(x,y,levels(x,y,mid)[1]) for x,y in xy])
            faces.append([vi(x,y,levels(x,y,mid)[0]) for x,y in reversed(xy)])
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)
            for a,b in zip(coords,coords[1:]):
                a=tuple(round(t,7) for t in a);b=tuple(round(t,7) for t in b)
                if a==b:continue
                la,ha=levels(*a,mid);lb,hb=levels(*b,mid)
                row=(a,b,vi(*a,la),vi(*b,lb),vi(*a,ha),vi(*b,hb))
                edges[tuple(sorted((a,b)))].append(row)
    for key,rows in edges.items():
        if len(rows)==1:
            a,b,la,lb,ha,hb=rows[0];faces.append([la,lb,hb,ha]);continue
        assert len(rows)==2,(name,key,len(rows))
        a,b,la,lb,ha,hb=rows[0];r=rows[1]
        if r[0]!=a:r=(r[1],r[0],r[3],r[2],r[5],r[4])
        _,_,lc,ld,hc,hd=r
        if ha!=hc or hb!=hd:faces.append([ha,hb,hd,hc])
        if la!=lc or lb!=ld:faces.append([la,lc,ld,lb])
    expanded=[]
    for f in faces:
        f=list(dict.fromkeys(f))
        if len(f)<3:continue
        q=[]
        for a,b in zip(f,f[1:]+f[:1]):
            q.append(a);va,vb=verts[a],verts[b]
            if va[:2]==vb[:2] and va[2]!=vb[2]:
                order=sorted((z for z in zs[va[:2]] if min(va[2],vb[2])+1e-8<z<max(va[2],vb[2])-1e-8),reverse=va[2]>vb[2])
                q.extend(index[(*va[:2],z)] for z in order)
        expanded.append(q)
    return dict(name=name,vertices=verts,faces=expanded,role=role,side=side,material=mat)

def bands(g,step=True):
    parts=polygons(g)
    if step:
        for i in range(23):
            y=Y0+i*RUN;nextparts=[]
            for p in parts:
                nextparts.extend(polygons(split(p,LineString([(-150,y),(150,y)]))))
            parts=nextparts
    return [(p,p.representative_point().y) for p in parts if p.area>1e-9]
def grid_regions(poly,step=.5):
    x0,y0,x1,y1=poly.bounds;rs=[]
    for x in np.arange(math.floor(x0/step)*step,x1,step):
        for y in np.arange(math.floor(y0/step)*step,y1,step):
            for p in polygons(poly.intersection(box(x,y,x+step,y+step))):
                if p.area>1e-8:rs.append((p,p.representative_point().y))
    return rs
def loops(g):
    return [dict(exterior=list(p.exterior.coords),holes=[list(r.coords) for r in p.interiors]) for p in polygons(g)]

pack=dict(dimensions='Inherited model coordinates / photographic proportion estimates; no measured dimensions',objects=[],plans={},checks={})
for side,spec in SPECS.items():
    P=Plan(side,spec);prefix='P5 '+side+' '
    W=rounded(P.border.buffer(.25,quad_segs=6).union(P.inner.buffer(1.38,quad_segs=32)),.23)
    C=rounded(P.border.buffer(.31,quad_segs=6).union(P.inner.buffer(1.50,quad_segs=32)),.27)
    mask=P.inner.buffer(1.85,quad_segs=36)
    for stem,g in [('wall',W),('coping',C)]:
        for component,geo in [('retaining',g.difference(mask)),('flower plinth',g.intersection(mask))]:
            top=lambda x,y,mid,P=P,stem=stem:P.wall_height(x,y,mid)+(P.cap_thickness(x,y) if stem=='coping' else 0)
            bottom=(lambda x,y,mid,P=P:P.wall_height(x,y,mid)) if stem=='coping' else (lambda x,y,mid:.035)
            pack['objects'].append(make_solid(prefix+component+' '+stem,bands(clean(geo)),top,bottom,stem,side,'cap' if stem=='coping' else 'stone'))
    # Outside ramp rail and its own plinth. Front and rear positions are authored
    # independently; clipping at y=120 meets the retained landing without intrusion.
    outerline=LineString(bez(spec['outer_path'],100))
    OM=P.outer.buffer(1.85,quad_segs=36)
    for stem,w,r in [('wall',.25,1.38),('coping',.31,1.5)]:
        g=rounded(outerline.buffer(w,quad_segs=6).union(P.outer.buffer(r,quad_segs=32)),.23).intersection(box(-150,70,150,120))
        def outer_top(x,y,mid,P=P,stem=stem):
            d=Point(x,y).distance(P.outer);t=min(1,max(0,(d-1.85)/1.15));t=t*t*(3-2*t)
            z=.785+(P.ramp_z(y)+.75-.785)*t
            return z+(.13 if stem=='coping' else 0)
        if stem=='coping':outer_coping=g
        for component,geo in [('outer rail',g.difference(OM)),('outer flower plinth',g.intersection(OM))]:
            pack['objects'].append(make_solid(prefix+component+' '+stem,bands(clean(geo),False),outer_top,(lambda x,y,mid,fn=outer_top:fn(x,y,mid)-.13) if stem=='coping' else (lambda x,y,mid:.035),stem,side,'cap' if stem=='coping' else 'stone'))
    soil=clean(P.poly.buffer(-.35,quad_segs=8).difference(mask.buffer(.06)))
    pack['objects'].append(make_solid(prefix+'planting surface',grid_regions(soil,.60),lambda x,y,mid:P.soil_height(x,y),lambda x,y,mid:.035,'planting_surface',side,'soil'))
    safe=clean(P.poly.buffer(-.86,quad_segs=8).difference(mask.buffer(.32)))
    red_path=P.front+P.side[1:]
    inward=[]
    for i,q in enumerate(red_path):
        a=np.array(red_path[max(0,i-1)]);b=np.array(red_path[min(len(red_path)-1,i+1)])
        v=b-a;v=v/np.linalg.norm(v);n=np.array([-v[1],v[0]])
        if not P.poly.covers(Point(np.array(q)+n*.45)):n=-n
        t=i/(len(red_path)-1);width=spec['red_width']+.50*math.sin(t*5.3)+.24*math.sin(t*12.2)
        inward.append(tuple(np.array(q)+n*width))
    red=rounded(clean(Polygon(red_path+list(reversed(inward)))).intersection(safe),.32)
    green=rounded(safe.difference(red.buffer(.58)),.30)
    yellow=clean(safe.difference(red).difference(green))
    zones=[('burgundy shrubs',red,spec['red_height'],'red'),('green shrubs',green,spec['green_height'],'green'),('yellow green transition',yellow,.34,'yellow')]
    for label,zone,height,mat in zones:
        def canopy(x,y,mid,zone=zone,height=height,P=P):
            d=Point(x,y).distance(zone.boundary)
            f=math.sin(min(1,d/.55)*math.pi/2)
            und=.042*math.sin(4.4*x+1.7*y)+.028*math.cos(2.2*x-4.9*y)+.027*math.sin(9.3*x+6.7*y)
            return P.soil_height(x,y)+.16+height*f+und*f
        pack['objects'].append(make_solid(prefix+label,grid_regions(zone,.36),canopy,lambda x,y,mid:P.soil_height(x,y)-.025,'vegetation',side,mat))
    # A protected central walking strip, verified geometrically in plan and by rays.
    if side=='west':A=(-50.,100.);B=(-34.,120.)
    else:A=(90.,100.);B=(74.,120.)
    corridor=LineString([A,B]).buffer(1.50,cap_style='flat')
    stonePlan=unary_union([C,W,outer_coping])
    checks=dict(corridor_stone_overlap_area=corridor.intersection(stonePlan).area,
        stairs_clearance=Polygon([(-16,109.08),(56,109.08),(56,117),(-16,117)]).distance(C),
        platform_overlap_area=C.intersection(box(-31.75,117,71.75,127.5)).area,
        outer_rail_landing_overlap_area=outer_coping.intersection(box(-150,120.001,150,150)).area,
        polygon_area=P.poly.area,front_arc_length=P.front_line.length)
    assert checks['corridor_stone_overlap_area']<1e-7,(side,checks)
    assert checks['platform_overlap_area']<1e-7,(side,checks)
    assert checks['stairs_clearance']>.60,(side,checks)
    pack['checks'][side]=checks
    pack['plans'][side]=dict(spec=spec,planter_centerline=loops(P.poly),wall=loops(W),coping=loops(C),planting=loops(soil),zones={k:loops(v) for k,v in [('red',red),('green',green),('yellow',yellow)]},corridor=loops(corridor))
    print('PREPARED',side,json.dumps(checks),flush=True)
(O/'geometry-pack.json').write_text(json.dumps(pack,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
print(json.dumps(dict(objects=len(pack['objects']),vertices=sum(len(o['vertices']) for o in pack['objects']),checks=pack['checks']),ensure_ascii=False),flush=True)
