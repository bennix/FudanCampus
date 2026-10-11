"""Finish only a float32 cut-boundary failure; does not reapply tree edits."""
import bpy,bmesh,sys
from pathlib import Path
from mathutils import Vector
O=Path(__file__).resolve().parent;sys.path.insert(0,str(O));from assemble import read,solid
sys.path.insert(0,str(O.parent/'scene-unified-v5'));from scene_fingerprints import sha,snapshot,write
T=O/'guanghua-closeout-final.blend';p=read(O/'ground-trim-pack.json');assert sha(T)==p['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(T));bpy.context.preferences.filepaths.save_version=0;before=snapshot();g=bpy.data.objects['GROUND__terrain__FIN_garden_grass'];g.data=g.data.copy()
me=bpy.data.meshes.new('Float32 trim boundary cutter');me.from_pydata(p['vertices'],[],p['faces']);me.update()
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();c=bpy.data.objects.new('Temporary float32 trim boundary',me);bpy.context.scene.collection.objects.link(c)
for m in g.data.materials:me.materials.append(m)
bpy.context.view_layer.objects.active=g;mod=g.modifiers.new('Finish float32 cut boundary','BOOLEAN');mod.solver='EXACT';mod.operation='DIFFERENCE';mod.object=c;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(c,do_unlink=True)
# Merge only sub-tolerance cut slivers into their coplanar neighbor, retaining UVs/vertices.
bm=bmesh.new();bm.from_mesh(g.data);slivers=0
degenerate_vertices=list({v for f in bm.faces if f.calc_area()<1e-9 for v in f.verts})
if degenerate_vertices:
 bmesh.ops.remove_doubles(bm,verts=degenerate_vertices,dist=1e-7)
 bad_edges=list({e for f in bm.faces if f.calc_area()<1e-9 for e in f.edges})
 if bad_edges:bmesh.ops.dissolve_degenerate(bm,edges=bad_edges,dist=1e-7)
for _ in range(12):
 bad=[f for f in bm.faces if f.calc_area()<1e-9]
 if not bad:break
 merged=False
 for f in bad:
  candidates=[e for e in f.edges if len(e.link_faces)==2 and any(q!=f and q.calc_area()>1e-8 and q.normal.dot(f.normal)>.999 for q in e.link_faces)]
  if candidates:
   edge=max(candidates,key=lambda e:e.calc_length());bmesh.ops.dissolve_edges(bm,edges=[edge],use_verts=False,use_face_split=False);slivers+=1;merged=True;break
 assert merged,('Could not merge cut sliver',[(f.calc_area(),[list(v.co) for v in f.verts]) for f in bad])
bm.to_mesh(g.data);bm.free();g.data.update()
check=solid(g);assert not check['nonmanifold'] and not check['zero_area'] and check['volume']>0,check
uv=g.data.uv_layers.active;signatures=set()
for f in g.data.polygons:
 for li in f.loop_indices:
  pt=g.matrix_world@g.data.vertices[g.data.loops[li].vertex_index].co
  signatures.add((tuple(round(x,5) for x in pt),f.material_index,tuple(round(x,5) for x in uv.data[li].uv) if uv else None))
for row in p['protected_existing_loops']:
 assert (tuple(round(x,5) for x in row['position']),row['material'],tuple(round(x,5) for x in row['uv']) if row['uv'] else None) in signatures,row
g['closeout_float32_cut_allowance']=p['cut_boundary_padding'];bpy.context.view_layer.update();after=snapshot();assert all(after.get(n)==h for n,h in before.items() if n!=g.name)
g.data.calc_loop_triangles();top=[]
for t in g.data.loop_triangles:
 q=[g.matrix_world@g.data.vertices[i].co for i in t.vertices]
 if (q[1]-q[0]).cross(q[2]-q[0]).z>1e-8 and all(abs(pt.z+.005)<1e-5 for pt in q):top.append([list(pt) for pt in q])
write(O/'ground-trim-native-top.json',top)
bpy.ops.wm.save_as_mainfile(filepath=str(T));write(O/'final-snapshot.json',after);bpy.ops.wm.open_mainfile(filepath=str(T));assert snapshot()==after
repair=read(O/'independent-native-repair.json');repair['final_sha256']=sha(T);repair['records']['ground_trim'].update(solid=check,cut_boundary_padding=p['cut_boundary_padding'],protected_original_loops=len(p['protected_existing_loops']),float32_followup_source_sha256=p['source_sha256'],coplanar_cut_slivers_merged=slivers);write(O/'independent-native-repair.json',repair)
print('GROUND_FLOAT32_BOUNDARY_REOPENED',sha(T),flush=True)
