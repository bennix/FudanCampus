"""Deterministic XY road domains and conforming meshes. No Blender dependency."""
from collections import Counter,defaultdict
import math
import numpy as np
import shapely as S
from shapely.geometry import Polygon,LineString,Point

GRID=1e-5
def clean(poly):
    if not poly.is_valid:raise ValueError('Invalid input domain: '+S.is_valid_reason(poly))
    out=S.set_precision(poly,GRID)
    if out.is_empty or not out.is_valid:raise ValueError('Domain collapsed at precision grid')
    return out

def road_domain(points,width):
    if isinstance(width,(int,float)):
        return clean(LineString(points).buffer(width/2,cap_style='flat',join_style='round',quad_segs=16))
    if len(width)!=len(points):raise ValueError('Width station count mismatch')
    pieces=[]
    for i,(a,b) in enumerate(zip(points,points[1:])):
        dx,dy=b[0]-a[0],b[1]-a[1];d=math.hypot(dx,dy)
        if d<1e-8:raise ValueError('Repeated station')
        nx,ny=-dy/d,dx/d;wa,wb=width[i]/2,width[i+1]/2
        pieces.append(Polygon([(a[0]+nx*wa,a[1]+ny*wa),(a[0]-nx*wa,a[1]-ny*wa),(b[0]-nx*wb,b[1]-ny*wb),(b[0]+nx*wb,b[1]+ny*wb)]))
    return clean(S.union_all(pieces))

def network_domains(edges):
    """Merge only graph-connected edges on the same surface layer; reject accidental joins."""
    pending=list(edges);groups=[]
    while pending:
        chosen=[pending.pop(0)];nodes=set(chosen[0]['nodes']);layer=chosen[0]['layer']
        again=True
        while again:
            again=False
            for e in pending[:]:
                if e['layer']==layer and nodes.intersection(e['nodes']):
                    chosen.append(e);nodes.update(e['nodes']);pending.remove(e);again=True
        domain=clean(S.union_all([road_domain(e['points'],e['width']) for e in chosen]))
        if domain.geom_type!='Polygon':raise ValueError('Declared connected graph has disjoint geometry')
        groups.append((layer,domain))
    for i,(la,a) in enumerate(groups):
        for lb,b in groups[i+1:]:
            if la==lb and a.intersection(b).area>GRID*GRID:raise ValueError('Undeclared same-layer intersection')
    return groups

def triangulate(poly,max_edge=.25):
    poly=S.segmentize(clean(poly),max_edge*.95)
    raw=S.constrained_delaunay_triangles(poly)
    vertices=[];lookup={};faces=[]
    def vi(p):
        k=(round(float(p[0]),10),round(float(p[1]),10))
        if k not in lookup:lookup[k]=len(vertices);vertices.append(k)
        return lookup[k]
    def orient(f):
        a,b,c=[vertices[i] for i in f]
        return f if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0 else (f[0],f[2],f[1])
    for t in raw.geoms:faces.append(orient(tuple(vi(p) for p in list(t.exterior.coords)[:3])))
    for _ in range(20):
        mids={}
        for f in faces:
            for a,b in zip(f,f[1:]+f[:1]):
                key=tuple(sorted((a,b)))
                if key not in mids and math.dist(vertices[a],vertices[b])>max_edge*(1+1e-8):
                    mids[key]=vi(((vertices[a][0]+vertices[b][0])/2,(vertices[a][1]+vertices[b][1])/2))
        if not mids:break
        new=[]
        for f in faces:
            a,b,c=f;ab=mids.get(tuple(sorted((a,b))));bc=mids.get(tuple(sorted((b,c))));ca=mids.get(tuple(sorted((c,a))))
            n=sum(v is not None for v in (ab,bc,ca))
            if n==0:new.append(f)
            elif n==3:new.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
            else:
                # Rotate to normalize one split AB, or two splits AB and BC.
                while (n==1 and ab is None) or (n==2 and (ab is None or bc is None)):
                    a,b,c=b,c,a;ab,bc,ca=bc,ca,ab
                if n==1:new.extend([(a,ab,c),(ab,b,c)])
                else:new.extend([(ab,b,bc),(a,ab,c),(ab,bc,c)])
        faces=[orient(f) for f in new]
    else:raise ValueError('Refinement did not converge')
    return vertices,faces,poly

def topology(vertices,faces,domain=None):
    edges=Counter();directed={};areas=[];adj=defaultdict(set)
    for f in faces:
        a,b,c=[vertices[i] for i in f]
        areas.append(((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2)
        for u,v in zip(f,f[1:]+f[:1]):
            edges[tuple(sorted((u,v)))]+=1;directed[tuple(sorted((u,v)))]=(u,v);adj[u].add(v);adj[v].add(u)
    todo=set(adj);components=0
    while todo:
        components+=1;stack=[todo.pop()]
        while stack:
            for j in adj[stack.pop()]:
                if j in todo:todo.remove(j);stack.append(j)
    boundary=[directed[e] for e,n in edges.items() if n==1]
    result={'vertices':len(vertices),'triangles':len(faces),'components':components,'nonmanifold_edges':sum(n>2 for n in edges.values()),'degenerate_or_reversed_faces':sum(a<=1e-12 for a in areas),'duplicate_faces':len(faces)-len({tuple(sorted(f)) for f in faces}),'boundary_edges':len(boundary)}
    if domain is not None:
        tris=[Polygon([vertices[i][:2] for i in f]) for f in faces]
        covered=S.union_all(tris)
        result['coverage_error_area']=covered.symmetric_difference(domain).area
        result['overlap_area']=sum(t.area for t in tris)-covered.area
        result['internal_open_edges']=sum(LineString([vertices[a][:2],vertices[b][:2]]).distance(domain.boundary)>2e-7 for a,b in boundary)
    return result,boundary

def extrude(vertices,faces,bottom=-.03):
    _,boundary=topology(vertices,faces)
    n=len(vertices);vs=[list(v) for v in vertices]+[[v[0],v[1],bottom] for v in vertices]
    fs=[list(f) for f in faces]+[[c+n,b+n,a+n] for a,b,c in faces]
    for a,b in boundary:fs.extend([[a,a+n,b+n],[a,b+n,b]])
    return vs,fs

def check_solid(vs,fs):
    counts=Counter(tuple(sorted((a,b))) for f in fs for a,b in zip(f,f[1:]+f[:1]))
    v=np.asarray(vs);f=np.asarray(fs);volume=float(np.einsum('ij,ij->i',v[f[:,0]],np.cross(v[f[:,1]],v[f[:,2]])).sum()/6)
    return {'open_edges':sum(n==1 for n in counts.values()),'nonmanifold_edges':sum(n>2 for n in counts.values()),'signed_volume':volume}

def smoothstep(t):
    t=max(0.,min(1.,t));return t*t*(3-2*t)

def profile(s,stations):
    for (a,za),(b,zb) in zip(stations,stations[1:]):
        if s<=b:return za+(zb-za)*smoothstep((s-a)/(b-a))
    return stations[-1][1]
