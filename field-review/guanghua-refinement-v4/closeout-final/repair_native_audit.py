"""Bounded repairs from the independent closeout audit, with source guards."""
import bpy,bmesh,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read,solid
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,snapshot,write,plain
T=O/'guanghua-closeout-final.blend';pack=read(O/'ground-trim-pack.json');source_sha=sha(T);assert source_sha==pack['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(T));s=bpy.context.scene;bpy.context.preferences.filepaths.save_version=0
assert not s.get('closeout_independent_native_audit_repaired'),'Rebuild earlier stages before repeating this repair'
before=snapshot();changed=set();records={}
def coords(me):
 a=np.empty(len(me.vertices)*3,np.float32);me.vertices.foreach_get('co',a);return a.reshape(-1,3)
ground=bpy.data.objects['GROUND__terrain__FIN_garden_grass'];original=ground.data
me=bpy.data.meshes.new('Independent audit exact ground cutter');me.from_pydata(pack['vertices'],[],pack['faces']);me.update()
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
cutter=bpy.data.objects.new('Independent audit temporary ground cutter',me);s.collection.objects.link(cutter)
for mat in original.materials:me.materials.append(mat)
ground.data=original.copy();bpy.context.view_layer.objects.active=ground;ground.select_set(True)
modifier=ground.modifiers.new('Remove only actual C04 planting projection','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
ground.data.update();check=solid(ground)
assert check['nonmanifold']==0 and check['zero_area']==0 and check['volume']>0 and check['finite'],check
uv=ground.data.uv_layers.active;output_loops=set()
for p in ground.data.polygons:
 for li in p.loop_indices:
  v=ground.matrix_world@ground.data.vertices[ground.data.loops[li].vertex_index].co
  output_loops.add((tuple(round(q,5) for q in v),p.material_index,tuple(round(q,5) for q in uv.data[li].uv) if uv else None))
unmatched=[]
for row in pack['protected_existing_loops']:
 signature=(tuple(round(q,5) for q in row['position']),row['material'],tuple(round(q,5) for q in row['uv']) if row['uv'] else None)
 if signature not in output_loops:unmatched.append(row)
assert not unmatched,('Original exterior loops not preserved',unmatched[:10])
ground['closeout_task']='C04';ground['closeout_note']='Original terrain trimmed by actual C04 ground upward-face projection; original holes and domain-exterior loops retained'
changed.add(ground.name)
records['ground_trim']=dict(solid=check,removed_duplicate_projected_area=pack['overlap_removed_area'],protected_original_loops=len(pack['protected_existing_loops']),unmatched_original_loops=unmatched,method=pack['method'])

# Only garden broadleaf blades grow. South avenue, conifers and open exit crowns retain their exact meshes.
canopies=[]
for ob in s.objects:
 if ob.type!='MESH' or ob.get('feature_id')!='TREE_CANOPY_V6' or 'leaves' not in ob.name:continue
 if ob.name.startswith(('V6 south avenue','V6 East spreading')):continue
 ob.data=ob.data.copy();a=coords(ob.data);assert len(a)%4==0;q=a.reshape(-1,4,3);center=q.mean(axis=1,keepdims=True)
 old_lo=a.min(axis=0);old_hi=a.max(axis=0);q[:]=center+(q-center)*1.35
 np.clip(a,old_lo,old_hi,out=a)
 assert np.all(np.isfinite(a));assert np.max(np.abs(q.mean(axis=1)-center[:,0]))<.013
 ob.data.vertices.foreach_set('co',a.ravel());ob.data.update();ob['closeout_audit_leaf_adjustment']='1.35 blade scale about retained centers, clipped to original crown bounds; no added trees or leaf clouds'
 changed.add(ob.name);canopies.append(dict(name=ob.name,leaf_count=len(q),scale=1.35,original_local_bounds=[old_lo.tolist(),old_hi.tolist()],final_local_bounds=[a.min(axis=0).tolist(),a.max(axis=0).tolist()],center_shift_max=float(np.max(np.linalg.norm(q.mean(axis=1)-center[:,0],axis=1)))))
records['garden_blades']=canopies

# Reconstruct the ring-seat tree's low fork while keeping the entire crown and root XY fixed.
wood=bpy.data.objects['V6 East ring-seat mature tree wood'];wood.data=wood.data.copy();bm=bmesh.new();bm.from_mesh(wood.data);bm.verts.ensure_lookup_table()
todo=set(bm.verts);components=[]
while todo:
 v=todo.pop();stack=[v];component=[v]
 while stack:
  a=stack.pop()
  for e in a.link_edges:
   b=e.other_vert(a)
   if b in todo:todo.remove(b);stack.append(b);component.append(b)
 components.append(sorted(component,key=lambda v:v.index))
components.sort(key=lambda q:q[0].index);primary=components[0];assert len(primary)==56
primary_points=[sum((v.co.copy() for v in primary[j*14:(j+1)*14]),Vector())/14 for j in range(4)]
assert primary_points[0].z<.05 and 3<primary_points[-1].z<6.5,primary_points
leaf=bpy.data.objects['V6 East ring-seat mature tree leaves'];leaf_floor=float(coords(leaf.data)[:,2].min());fade_top=leaf_floor-.20
assert fade_top>primary_points[-1].z+.40,(fade_top,primary_points)
axis=Vector((.82,.57,0)).normalized();top_z=primary_points[-1].z
def smooth(t):t=max(0.,min(1.,t));return t*t*(3-2*t)
def shift(z):
 stations=[(primary_points[0].z,0),(.25,.10),(.60,.22),(1.4,.36),(3.0,.55),(top_z,.74)]
 for (a,x),(b,y) in zip(stations,stations[1:]):
  if z<=b:return x+(y-x)*smooth((z-a)/(b-a))
 return .74
def fade(z):return 1-smooth((z-top_z)/(fade_top-top_z))
def centerline(z):
 for a,b in zip(primary_points,primary_points[1:]):
  if z<=b.z:return a.lerp(b,max(0,min(1,(z-a.z)/(b.z-a.z))))
 return primary_points[-1].copy()
processed=[];connections=[];root_positions=[];branch_points_unchanged=0
for comp in components[1:]:
 assert len(comp) in {24,40},len(comp)
 rings=[sum((v.co.copy() for v in comp[j:j+8]),Vector())/8 for j in range(0,len(comp),8)]
 start,end=rings[0],rings[-1]
 if len(comp)==24:
  side=1 if start.dot(axis)>=0 else -1
  for v in comp:
   if v.co.z<=.25:root_positions.append(list(v.co))
   else:v.co+=axis*side*shift(v.co.z)*smooth((v.co.z-.25)/.7)
 else:
  nearest=min(((start-p).length,side,p) for p,side in processed) if processed else None
  if nearest and nearest[0]<.005:side=nearest[1];connections.append(dict(original_join_gap=nearest[0],source_start=list(start),parent_ring=list(nearest[2]),side=side))
  else:side=1 if (end-centerline(end.z)).dot(axis)>=0 else -1
  for v in comp:
   if v.co.z>=fade_top:branch_points_unchanged+=1
   else:v.co+=axis*side*shift(v.co.z)*fade(v.co.z)
  processed.extend((p,side) for p in rings)
bmesh.ops.delete(bm,geom=primary,context='VERTS')
stem_records=[]
for side,radius in [(-1,.235),(1,.215)]:
 zs=[primary_points[0].z,.25,.60,1.4,2.3,3.0,4.0,top_z]
 points=[centerline(z)+axis*side*shift(z) for z in zs]
 points[0]=primary_points[0].copy();rings=[];sides=16
 for j,p in enumerate(points):
  tangent=(points[min(j+1,len(points)-1)]-points[max(0,j-1)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u)
  rad=radius+(radius*.58-radius)*j/(len(points)-1);row=[]
  for k in range(sides):
   angle=k*math.tau/sides;vertex=bm.verts.new(p+(math.cos(angle)*u+math.sin(angle)*v)*rad*(1+.025*math.sin(k*3+j)))
   row.append(vertex)
  rings.append(row)
 for a,b in zip(rings,rings[1:]):
  for k in range(sides):bm.faces.new((a[k],a[(k+1)%sides],b[(k+1)%sides],b[k]))
 bm.faces.new(tuple(reversed(rings[0])));bm.faces.new(tuple(rings[-1]));stem_records.append(dict(side=side,centers=[list(p) for p in points],root_radius=radius,upper_radius=radius*.58))
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(wood.data);bm.free();wood.data.update()
for p in wood.data.polygons:p.use_smooth=True
wood['closeout_task']='C14';wood['source_photos']=[4547,4550];wood['closeout_note']='Photo-supported low unequal twin-stem fork; root origin, root feet, seating clearance and canopy anchors retained. Unseen upper branching remains inferred.'
changed.add(wood.name);wood_check=solid(wood);assert wood_check['nonmanifold']==0 and wood_check['zero_area']==0 and wood_check['volume']>0,wood_check
records['ring_tree_fork']=dict(solid=wood_check,root_origin=list(wood.location),original_primary_centers=[list(p) for p in primary_points],new_stems=stem_records,unchanged_crown_branch_vertices=branch_points_unchanged,root_foot_vertices_preserved=len(root_positions),branch_attachment_inheritance=connections,unseen_branching='inferred',crown_transformation_unchanged=True)
for name in ['C14 connected vine stems','C14 attached vine leaves']:
 ob=bpy.data.objects[name];ob['source_photos']=[4547,4550];changed.add(name)
s['closeout_independent_native_audit_repaired']=True;bpy.context.view_layer.update();after=snapshot();drift=[n for n,h in before.items() if n not in changed and after.get(n)!=h];assert not drift,drift
assert set(after)==set(before)
# Export top projection for independent Shapely overlap and old-hole preservation proof.
ground.data.calc_loop_triangles();top=[]
for tri in ground.data.loop_triangles:
 q=[ground.matrix_world@ground.data.vertices[i].co for i in tri.vertices]
 if (q[1]-q[0]).cross(q[2]-q[0]).z>1e-8 and all(abs(p.z+.005)<1e-5 for p in q):top.append([list(p) for p in q])
write(O/'ground-trim-native-top.json',top)
checks=[]
for x,y in [(70.060989,69.007263),(68.789238,72.228401),(74,67)]:
 bvh=BVHTree.FromPolygons([ground.matrix_world@v.co for v in ground.data.vertices],[tuple(p.vertices) for p in ground.data.polygons]);p=bvh.ray_cast(Vector((x,y,30)),Vector((0,0,-1)),80)[0];assert p is None,(x,y,p);checks.append(dict(x=x,y=y,old_terrain_hit_after_trim=None))
records['old_ground_black_region_probes']=checks
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'final-snapshot.json',after);bpy.ops.wm.open_mainfile(filepath=str(T));assert snapshot()==after
report=dict(source_sha256=source_sha,final_sha256=sha(T),reopened_snapshot_equal=True,changed=sorted(changed),nonwhitelist_meshes_unchanged=len(before)-len(changed),same_objects=True,records=records,baseline_sha256=sha(O.parent/'scene-closeout-v7/guanghua-unified-closeout-v7.blend'))
assert report['baseline_sha256']=='641a3ab8f02443ef98ce1bc2dcb2e8a6fdb63ba194dd6fffbec7a92aeeb146a2'
write(O/'independent-native-repair.json',report);print('INDEPENDENT_NATIVE_REPAIR_REOPENED',report['final_sha256'],len(changed),flush=True)
