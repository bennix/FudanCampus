import bpy, bmesh, json, hashlib, math, sys
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / 'scripts'))
from export_visible_glb import export_visible_glb
from mathutils import Vector

O=Path(__file__).resolve().parent
BASE=O.parent/'forecourt-v2/forecourt-complete-v2.blend'
R=O.parents[2]
INFO=json.loads((O.parent/'forecourt-v2/build-info.json').read_text())
Y=INFO['entry_line']; PY=INFO['urn_centres'][0][1]; AX=-27.0
DY=Y-87
basehash=hashlib.sha256(BASE.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
C=bpy.data.collections.new('09_West_entry_alignment');s.collection.children.link(C)

def digest(ob):
 a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a)
 return hashlib.sha256(a.tobytes()+str(list(ob.matrix_world)).encode()+str([tuple(p.vertices) for p in ob.data.polygons]).encode()).hexdigest()

def mesh(name,vs,fs,mat,fid='W_ENTRY'):
 me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();me.materials.append(mat)
 ob=bpy.data.objects.new(name,me);C.objects.link(ob);ob['feature_id']=fid;ob['geometry_confidence']='User requested matching entrance alignment; dimensions inferred';ob['source_photos']=[4469,4491,4492];return ob

def uv(ob,scale=1):
 layer=ob.data.uv_layers.get('FORECOURT_metric') or ob.data.uv_layers.new(name='FORECOURT_metric');ob.data.uv_layers.active=layer;layer.active_render=True
 for p in ob.data.polygons:
  axis=max(range(3),key=lambda k:abs(p.normal[k]));axes=(1,2) if axis==0 else (0,2) if axis==1 else (0,1)
  for li in p.loop_indices:
   co=ob.matrix_world@ob.data.vertices[ob.data.loops[li].vertex_index].co;layer.data[li].uv=(co[axes[0]]/scale,co[axes[1]]/scale)

def prism(name,pts,z0,z1,mat,fid='W_ENTRY'):
 if sum(pts[i][0]*pts[(i+1)%len(pts)][1]-pts[(i+1)%len(pts)][0]*pts[i][1] for i in range(len(pts)))<0:pts=list(reversed(pts))
 n=len(pts);ob=mesh(name,[(x,y,z) for z in [z0,z1] for x,y in pts],[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat,fid)
 bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free();uv(ob,9.6 if mat.name=='FC_plaza_grid' else 1);return ob

def box(name,centre,size,mat):
 x,y,z=centre;w,d,h=size
 return prism(name,[(x-w/2,y-d/2),(x+w/2,y-d/2),(x+w/2,y+d/2),(x-w/2,y+d/2)],z-h/2,z+h/2,mat)

old_urns=[ob for ob in s.objects if ob.type=='MESH' and (ob.name.startswith('FURNITURE__') and any(k in ob.name for k in ['urn-plinth','plinth-cap','geometry__pale','urn-planting','urn-flowers']) or ob.name=='V2 leaves FURNITURE')]
assert len(old_urns)==6
for ob in old_urns:
 points=[ob.matrix_world@v.co for v in ob.data.vertices]
 assert all(-32<p.x<-21 and 87<p.y<91 for p in points),ob.name
changed_names={o.name for o in old_urns}
changed_names.update(o.name for o in s.objects if o.get('feature_id')=='WOPEN' or o.name=='V2 leaves WOPEN')
changed_names.update(['GROUND__landscape-slab__soil','FORECOURT photo grid plaza','EDGE_PATHS__edge-walk__FIN_pavers','WPATH__west-garden__stone','WPATH__curb-west-garden__pale'])
ground=next(ob for ob in s.objects if ob.type=='MESH' and ob.get('feature_id')=='GROUND');changed_names.add(ground.name)
protected={o.name:digest(o) for o in s.objects if o.type=='MESH' and o.name not in changed_names}
stone=bpy.data.materials['FC_warm_granite'];paving=bpy.data.materials['FC_plaza_grid'];soil=bpy.data.materials['FIN_garden_grass']

for ob in old_urns:bpy.data.objects.remove(ob,do_unlink=True)
# Clone accepted east components as rigid groups, retaining their UVs and materials.
copies=[]
for idx,cx in enumerate([AX-3.5,AX+3.5]):
 sources=[ob for ob in s.objects if ob.name.startswith(f'E_ENTRY {idx} ')]
 assert len(sources)>=10
 for src in sources:
  ob=src.copy();ob.name=src.name.replace('E_ENTRY','W_ENTRY',1);C.objects.link(ob)
  ob.location.x+=cx-INFO['urn_centres'][idx][0];ob['feature_id']='W_ENTRY';ob['source_component']=src.name;ob['position_evidence']='User-requested west entrance alignment';copies.append(ob.name)

# Move each hierarchy once; moving both its root and children would double the retreat.
opening=[ob for ob in s.objects if ob.get('feature_id')=='WOPEN']
opening_before={ob.name:ob.matrix_world.copy() for ob in opening if ob.type=='MESH'}
for ob in opening:
 if ob.parent not in opening:
  matrix=ob.matrix_world.copy();matrix.translation.y+=DY;ob.matrix_world=matrix;ob['west_entry_alignment_dy']=DY
leafskin=bpy.data.objects.get('V2 leaves WOPEN')
if leafskin:
 matrix=leafskin.matrix_world.copy();matrix.translation.y+=DY;leafskin.matrix_world=matrix
bpy.context.view_layer.update()
assert all(abs(bpy.data.objects[name].matrix_world.translation.y-matrix.translation.y-DY)<1e-5 for name,matrix in opening_before.items())
patch=box('W_ENTRY old stair hole infill',(-32,81,-.94),(3.22,4.22,1.88),soil)
cutter=box('W_ENTRY temporary stair hole',(-32,81+DY,-1),(3.2,4.2,4),soil)
bpy.context.view_layer.objects.active=ground
mod=ground.modifiers.new('West north opening relocated','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cutter,do_unlink=True)

walk=bpy.data.objects['EDGE_PATHS__edge-walk__FIN_pavers']
walk_unchanged=[tuple(v.co) for v in walk.data.vertices if (walk.matrix_world@v.co).x>0 or (walk.matrix_world@v.co).y<70]
for v in walk.data.vertices:
 p=walk.matrix_world@v.co
 if p.x<0 and p.y>Y:v.co+=walk.matrix_world.inverted().to_3x3()@Vector((0,Y-p.y,0))
uv(walk,9.6)
assert walk_unchanged==[tuple(v.co) for v in walk.data.vertices if (walk.matrix_world@v.co).x>0 or (walk.matrix_world@v.co).y<70]

# Keep the south part of the west curve and curb; reconnect only its northern head.
path_south={}
joinx=None
for name in ['WPATH__west-garden__stone','WPATH__curb-west-garden__pale']:
 ob=bpy.data.objects[name];path_south[name]=sorted(tuple(round(c,6) for c in v.co) for v in ob.data.vertices if (ob.matrix_world@v.co).y<74.99)
 bm=bmesh.new();bm.from_mesh(ob.data)
 plane=ob.matrix_world.inverted()@Vector((0,75,0));normal=ob.matrix_world.to_3x3().transposed()@Vector((0,1,0))
 bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=plane,plane_no=normal,clear_outer=True)
 ends=[ob.matrix_world@v.co for v in bm.verts if abs((ob.matrix_world@v.co).y-75)<.001]
 if name=='WPATH__west-garden__stone':joinx=sum(p.x for p in ends)/len(ends)
 bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
 assert path_south[name]==sorted(tuple(round(c,6) for c in v.co) for v in ob.data.vertices if (ob.matrix_world@v.co).y<74.99)

def ribbon(name,points,width,z0,z1,mat):
 # Rounded centerline with bounded interpolants, closed stone strip.
 controls=[Vector(points[0])]+[Vector(p) for p in points]+[Vector(points[-1])];qs=[]
 for j in range(1,len(controls)-2):
  a,b,c,d=controls[j-1:j+3]
  for k in range(12):
   t=k/12;qs.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 qs.append(Vector(points[-1]));left=[];right=[]
 for i,q in enumerate(qs):
  tangent=(qs[min(i+1,len(qs)-1)]-qs[max(0,i-1)]).normalized();u=Vector((-tangent.y,tangent.x))*width/2;left.append(tuple(q+u));right.append(tuple(q-u))
 return prism(name,left+list(reversed(right)),z0,z1,mat)

points=[(joinx,74.97),(-38.8,74.6),(-37.4,75.2),(-35.7,75.9),(-32.1,76.1),(-28.8,76.1)]
ribbon('W_ENTRY recessed garden path border',points,1.74,.014,.084,bpy.data.materials['pale'])
newpath=ribbon('W_ENTRY recessed garden connection',points,1.50,.078,.094,bpy.data.materials['stone'])
assert max(v.co.y for v in newpath.data.vertices)<Y-.7

outline=json.loads((R/'field-review/guanghua-lawn-shape-v2/outline.json').read_text())
poly=[(x-25,y+16) for x,y in outline['polygon_xy']];north=list(reversed(poly[2:]))
westedge=[(-28.8,Y),(-32.69788244,Y),(-38.69788244,Y+.65),(-44.69788244,Y+3.4),(-52.69788244,87),(-80,87)]
eastedge=[(67.10211756,Y),(71,Y),(77,Y+.65),(83,Y+3.4),(91,87),(102.30211756,87)]
oldplaza=bpy.data.objects['FORECOURT photo grid plaza'];bpy.data.objects.remove(oldplaza,do_unlink=True)
newplaza=prism('FORECOURT photo grid plaza',list(reversed(westedge))+north+eastedge+[(102.30211756,113),(-80,113)],-.035,.035,paving,'FORECOURT')

def curb(points):
 pts=[Vector(p) for p in points];lengths=[0]
 for a,b in zip(pts,pts[1:]):lengths.append(lengths[-1]+(b-a).length)
 def at(t):
  import bisect
  i=min(len(pts)-2,max(0,bisect.bisect_right(lengths,t)-1));return pts[i].lerp(pts[i+1],(t-lengths[i])/(lengths[i+1]-lengths[i]))
 count=math.ceil(lengths[-1]/.85)
 for i in range(count):
  a=at(lengths[-1]*i/count+.004);b=at(lengths[-1]*(i+1)/count-.004);u=Vector((-(b-a).y,(b-a).x)).normalized()*.12
  ob=prism(f'W_ENTRY aligned garden curb {i:03d}',[tuple(a-u),tuple(b-u),tuple(b+u),tuple(a+u)],.016,.15,stone)
  mod=ob.modifiers.new('small chamfer','BEVEL');mod.width=.014;mod.segments=2
curb(westedge)

def camera(name,loc,target,scale):
 data=bpy.data.cameras.new(name);ob=bpy.data.objects.new(name,data);C.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=scale;data.clip_end=1500;return ob

cameras={'west-oblique':camera('W3 west comparison',(-26.3,107,29),(-26.3,78,0),36),
 'west-front':camera('W3 west front',(AX,Y+19,10),(AX,Y-3,0),23),
 'west-top':camera('W3 west top',(AX,Y-3,55),(AX,Y-3,0),29),
 'paired-top':camera('W3 paired entrances top',(19.15,85,120),(19.15,85,0),120),
 'overall':bpy.data.objects['FINAL landscape']}
assert all(digest(bpy.data.objects[name])==value for name,value in protected.items())
assert all(math.isfinite(c) for ob in C.objects if ob.type=='MESH' for v in ob.data.vertices for c in v.co)
report=dict(source_sha256=basehash,protected_objects=len(protected),protected_geometry_unchanged=True,
 main_lawn_east_entry_statue_and_terraces_unchanged=True,west_axis=AX,entry_line=Y,urn_y=PY,
 urn_centres=[[AX-3.5,PY],[AX+3.5,PY]],urn_clear_width=4.7,walk_width=3.6,
 north_opening_translation_y=DY,original_west_urn_meshes_removed=6,copied_urn_components=copies,
 west_walk_south_and_east_vertices_unchanged=True,west_path_vertices_below_y75_unchanged=True,
 cameras={k:v.name for k,v in cameras.items()},source_photos=[4469,4491,4492],limits=['photo-proportion reconstruction, not measured','entrance tips aligned; whole gardens and original lawn curve are not mirrored'])
(O/'build-info.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
s.cycles.use_denoising=True;s.render.resolution_percentage=100
if '--diagnostic' in sys.argv:
 s.cycles.samples=12;s.render.resolution_x=1100;s.render.resolution_y=900
 for key in ['west-oblique','west-top']:
  s.camera=cameras[key];s.render.filepath=str(O/('diagnostic-'+key+'.png'));bpy.ops.render.render(write_still=True)
 bpy.ops.wm.save_as_mainfile(filepath=str(O/'diagnostic-west-entry.blend'))
 print('WEST_ENTRY_DIAGNOSTIC_COMPLETE',flush=True)
else:
 s.camera=cameras['west-front'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'west-entry-aligned-v3.blend'))
 bpy.ops.object.select_all(action='DESELECT')
 for ob in s.objects:
  if ob.type=='MESH' and not ob.hide_render:ob.hide_set(False);ob.select_set(True)
 export_visible_glb(filepath=str(O/'west-entry-aligned-v3.glb'),export_apply=True)
 s.cycles.samples=24;s.render.resolution_x=1400;s.render.resolution_y=1050
 for key,cam in cameras.items():
  s.camera=cam;s.render.filepath=str(O/('after-'+key+'.png'));bpy.ops.render.render(write_still=True)
 bpy.ops.wm.open_mainfile(filepath=str(O/'west-entry-aligned-v3.blend'))
 assert all(digest(bpy.data.objects[name])==value for name,value in protected.items())
 assert hashlib.sha256(BASE.read_bytes()).hexdigest()==basehash
 report.update(checkpoint_reopened=True,source_unchanged=True,opening_hierarchy_translated_once=True,export_bytes=(O/'west-entry-aligned-v3.glb').stat().st_size)
 (O/'validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print('WEST_ENTRY_FINAL_COMPLETE',flush=True)
