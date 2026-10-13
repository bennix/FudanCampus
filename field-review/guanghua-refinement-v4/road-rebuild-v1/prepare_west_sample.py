"""Prepare the bounded west-exit experiment; retained XY is explicitly provisional."""
import json,math,sys,hashlib,platform
from pathlib import Path
import numpy as np
import shapely as S
from shapely.geometry import Polygon,LineString,Point,box,mapping
from shapely.ops import nearest_points
from road_geometry import clean,triangulate,topology,extrude,check_solid,smoothstep,profile,road_domain

O=Path(__file__).resolve().parent
batch=O/(sys.argv[1] if len(sys.argv)>1 else 'diagnostic-01');batch.mkdir(exist_ok=True)
if (batch/'mesh-payload.json').exists():raise RuntimeError('Batch geometry exists; choose a new batch')
data=json.loads((O/'baseline-geometry.json').read_text())
C=json.loads((O/'sample-settings.json').read_text())
DX=-6.697882438088101
def components(o):
    adj={i:set() for i in range(len(o['vertices']))}
    for f in o['faces']:
        for v in f:adj[v].update(f)
    todo=set(adj);groups=[]
    while todo:
        root=min(todo);todo.remove(root);stack=[root];g={root}
        while stack:
            for i in adj[stack.pop()]:
                if i in todo:todo.remove(i);g.add(i);stack.append(i)
        groups.append(sorted(g))
    return groups
roads=[];old_terrain=[];removals={};main_centers=[];selected_ports=[];sources=[]
for o in data:
    if o['id']!='EPATH' or 'north-exit' in o['name']:continue
    for group in components(o):
        v=[o['vertices'][i] for i in group];x=sum(p[0] for p in v)/len(v);y=sum(p[1] for p in v)/len(v)
        selected='west-exit' in o['name'] or ('main-curve' in o['name'] and C['main_y_range'][0]<y<C['main_y_range'][1]) or ('lawn-connection' in o['name'] and C['lawn_connector_y_range'][0]<y<C['lawn_connector_y_range'][1])
        if not selected:continue
        removals.setdefault(o['name'],[]).extend(group)
        # Import original strip boundary stations, never inherit its damaged triangulation.
        top=[o['vertices'][i] for i in group if o['vertices'][i][2]>.005]
        xy=[(p[0],p[1]) for p in top]
        footprint=Polygon(xy).convex_hull
        if footprint.area<1e-9:continue
        if 'terrain' in o['name']:old_terrain.append(footprint)
        else:
            if 'west-exit-path__' not in o['name']:roads.append(footprint)
            sources.append({'source':o['name'],'source_vertices':group,'boundary_xy':list(footprint.exterior.coords)[:-1]})
            if 'main-curve' in o['name']:main_centers.append((min(group),(x,y)))
main=LineString([p for _,p in sorted(main_centers)]);L=main.length
junction=main.project(Point(C['stair_foot_xy']))
join=main.interpolate(junction)
# A single west connector terminates at the declared main-road junction.
# The previous nearly parallel loop is no longer a second overlapping road.
branch=[C['stair_foot_xy'],C['connector_approach_xy'],(join.x,join.y)]
branch_domain=road_domain(branch,C['connector_width'])
roads.append(branch_domain)
domain=clean(S.union_all(roads).intersection(box(C['sidewalk_interface_x'],-100,200,200)))
assert domain.geom_type=='Polygon','Unexpected disconnected input road domain'
assert len(domain.interiors)==0,'Unreviewed island in west sample'
stations=[(0,C['ground_road_z']),(C['flat_terminal_length'],C['ground_road_z']),(junction,C['junction_z']),(L-C['flat_terminal_length'],C['ground_road_z']),(L,C['ground_road_z'])]
assert 1<junction<L-1
left_terminal=domain.bounds[0]
def road_z(x,y):
    p=Point(x,y);s=main.project(p);q=main.interpolate(s)
    z=profile(s,stations)
    # Crossfall-free main strip; bounded interpolation on the declared west connector.
    half=C['main_half_width'];ground=C['ground_road_z']
    if x<q.x-half:
        z=C['sidewalk_interface_z']+(z-C['sidewalk_interface_z'])*smoothstep((x-left_terminal)/(q.x-half-left_terminal))
    if x>q.x+half and 42<y<49.5:
        weight=smoothstep((x-(q.x+half))/(C['stair_foot_xy'][0]-(q.x+half)))
        z=z+(C['stair_foot_z']-z)*weight
    return z

# Current local terrain footprint only; trim at fixed structures and the stair end.
protected=[]
for o in data:
    if o['id'] not in {'ESKY','EOPEN_S','ETERR'}:continue
    if not any(s in o['name'] for s in ['plinth','planter-wall','coping','side-wall','end-wall','support']):continue
    matrix=np.asarray(o['transform']);world=[matrix@np.array([*v,1]) for v in o['vertices']]
    projected=[]
    for face in o['faces']:
        p=Polygon([(world[i][0]-DX,world[i][1]) for i in face])
        if p.is_valid and p.area>1e-9:projected.append(p)
    region=S.union_all(projected)
    if o['id']=='EOPEN_S' and 'coping' in o['name']:region=region.convex_hull
    protected.append(region.buffer(C['protection_margin']))
protection=S.union_all(protected)
if domain.intersection(protection).area>=1e-5:
    print('PROTECTED_OVERLAP',domain.intersection(protection).area,domain.intersection(protection).wkt)
assert domain.intersection(protection).area<1e-5,'Road enters a protected structure'
outer=clean(domain.buffer(C['shoulder_width']).union(S.union_all(old_terrain))).intersection(box(*C['shoulder_clip_bounds']))
shoulder=clean(outer.difference(domain).difference(protection))
v,f,domain=triangulate(domain,C['max_triangle_edge'])
road_report,boundary=topology(v,f,domain)
assert road_report['components']==1
for k in ['nonmanifold_edges','degenerate_or_reversed_faces','duplicate_faces','internal_open_edges']:assert road_report[k]==0,(k,road_report[k])
assert road_report['coverage_error_area']<1e-5 and abs(road_report['overlap_area'])<1e-5
rv=[(x,y,road_z(x,y)) for x,y in v];rvs,rfs=extrude(rv,f)
road_solid=check_solid(rvs,rfs);assert road_solid['open_edges']==road_solid['nonmanifold_edges']==0 and road_solid['signed_volume']>0

# Terrain top never exists under road; the road boundary supplies the shoulder height.
terrain_outer=shoulder.boundary.difference(domain.boundary.buffer(.00002))
def terrain_z(x,y):
    p=Point(x,y);q=nearest_points(p,domain.boundary)[1];dr=p.distance(domain.boundary)
    dout=p.distance(terrain_outer)
    t=dout/(dr+dout) if dr+dout>1e-9 else 1.
    return -.045+(road_z(q.x,q.y)-.01+.045)*smoothstep(t)
tv,tf,tpoly=triangulate(shoulder,C['max_triangle_edge'])
terrain_report,_=topology(tv,tf,tpoly)
tvs,tfs=extrude([(x,y,terrain_z(x,y)) for x,y in tv],tf,bottom=-.08)
terrain_solid=check_solid(tvs,tfs)
assert terrain_solid['open_edges']==terrain_solid['nonmanifold_edges']==0 and terrain_solid['signed_volume']>0

network={'version':1,'source_checkpoint':'stage01-east.blend','coordinate_system':'east local; registration applied only by Blender parent','world_translation':[DX,0,0],
 'feature_id':'EPATH','scope':'west exit, its intersecting main-path span, and one lawn connector; no north exit rebuild',
 'primary_reference':'IMG_4568','secondary_references':['IMG_4565','IMG_4569'],
 'confidence':{'short_stair_to_curving_path':'confirmed','exact_plan_route':'inferred; one connector to main junction replaces overlapping near-parallel loop','absolute_heights':'inferred','junction_height':'inferred test only'},
 'nodes':{'stair_foot':{'xy':C['stair_foot_xy'],'z':C['stair_foot_z']},'main_junction':{'xy':list(main.interpolate(junction).coords)[0],'z':C['junction_z']},'north_boundary':{'xy':list(main.coords)[0],'z':C['ground_road_z']},'south_boundary':{'xy':list(main.coords)[-1],'z':C['ground_road_z']},'sidewalk_interface':{'x':C['sidewalk_interface_x'],'z':C['sidewalk_interface_z'],'source':'EDGE_PATHS inner border and top surface'}},
 'main_centerline':list(main.coords),'west_connector_centerline':branch,'west_connector_width':C['connector_width'],'main_profile_stations':stations,'source_strip_boundaries':sources,
 'limitations':['The 1.75 m stair-foot elevation is inherited, not measured.','The 1.20 m junction profile is a test hypothesis near the previous generated surface, not a photographic measurement.','Other EPATH sections retain old defects; this file is a local study only.']}
(O/'road-network.json').write_text(json.dumps(network,indent=2),encoding='utf-8')
(O/'road-protection.json').write_text(json.dumps({'allowed_feature_id':'EPATH','removed_vertex_indices':removals,'protected_geometry':mapping(protection)},indent=2),encoding='utf-8')
config={'algorithm':'xy-union-cdt-conforming-refinement-independent-profile-v1','grid':1e-5,'max_edge':C['max_triangle_edge'],'python':platform.python_version(),'shapely':S.__version__,'geos':S.geos_version_string,'numpy':np.__version__,'blender':'4.4.3','uv_metre_scale':C['uv_scale'],'settings':C}
(O/'road-generation-config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
for fname in ['road-network.json','road-protection.json','road-generation-config.json']:
    (batch/fname).write_bytes((O/fname).read_bytes())
payload={'registration':[DX,0,0],'removals':removals,'road':{'vertices':rvs,'faces':rfs,'top_faces':len(f)},'terrain':{'vertices':tvs,'faces':tfs,'top_faces':len(tf)},'network':network}
(batch/'mesh-payload.json').write_text(json.dumps(payload),encoding='utf-8')
report={'road_surface':road_report,'road_solid':road_solid,'terrain_surface':terrain_report,'terrain_solid':terrain_solid,'road_terrain_overlap_area':domain.intersection(shoulder).area,'protected_overlap_area':domain.intersection(protection).area,'status':'geometry_checks_passed_visual_pending','site_profile_status':'inferred_not_accepted'}
assert report['road_terrain_overlap_area']<1e-5 and report['protected_overlap_area']<1e-5
for k in ['nonmanifold_edges','degenerate_or_reversed_faces','duplicate_faces','internal_open_edges']:assert terrain_report[k]==0
report['step_interface_error']=max(abs(z-C['stair_foot_z']) for x,y,z in rv if abs(x-C['stair_foot_xy'][0])<1e-5)
report['sidewalk_interface_error']=max(abs(z-C['sidewalk_interface_z']) for x,y,z in rv if abs(x-C['sidewalk_interface_x'])<1e-5)
assert report['step_interface_error']<1e-5 and report['sidewalk_interface_error']<1e-5
(batch/'geometry-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(batch/'domains.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[{'type':'Feature','properties':{'kind':'road'},'geometry':mapping(domain)},{'type':'Feature','properties':{'kind':'terrain'},'geometry':mapping(shoulder)}]}),encoding='utf-8')
samples=[]
for s in np.linspace(0,L,151):
    q=main.interpolate(s);samples.append({'s':float(s),'x':q.x,'y':q.y,'z':road_z(q.x,q.y)})
slopes=[abs(b['z']-a['z'])/(b['s']-a['s']) for a,b in zip(samples,samples[1:])]
branchline=LineString(branch);branchsamples=[]
for s in np.linspace(0,branchline.length,101):
    q=branchline.interpolate(s);branchsamples.append({'s':float(s),'x':q.x,'y':q.y,'z':road_z(q.x,q.y)})
branchslopes=[abs(b['z']-a['z'])/(b['s']-a['s']) for a,b in zip(branchsamples,branchsamples[1:])]
(batch/'profile.json').write_text(json.dumps({'main_samples':samples,'branch_samples':branchsamples,'max_longitudinal_grade':max(slopes),'branch_max_grade':max(branchslopes),'warning':'Geometry experiment; inherited elevation and grade require independent site validation.'},indent=2),encoding='utf-8')
print(json.dumps(report,indent=2));print('PROFILE_MAX_GRADE',max(slopes))
