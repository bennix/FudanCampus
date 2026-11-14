"""Read-only checks of round-2 user corrections on a loaded blend."""
import bpy
import json
from mathutils import Vector

meshes=[o for o in bpy.data.objects if o.type=='MESH']


def named(text):
    return [o for o in meshes if text in o.name]


def verts(objects):
    return [o.matrix_world @ v.co for o in objects for v in o.data.vertices]


soil=verts(named('flowerbed soil'))
door=verts(named('side entrance door'))
main_windows=verts(named('window glass'))
small_windows=verts(named('rear small end glazing'))
checks={
    'entry_side_walls_removed':not named('entry portal columns'),
    # Allow 0.20 m for photographed projecting sills beyond the -3.6 m facade.
    'upper_east_notch_clear':not any(v.x>10.6 and v.y<-3.8 and v.z>7 for v in verts(meshes)),
    'flowerbed_west_aligned_entry':bool(soil) and abs(min(v.x for v in soil)-7.75)<.005,
    'flowerbed_east_aligned_building':bool(soil) and abs(max(v.x for v in soil)-20.4)<.005,
    'west_lawn_present':bool(named('west forecourt lawn')),
    'side_door_moves_with_wing':bool(door) and abs((min(v.y for v in door)+max(v.y for v in door))/2+1.25)<.005,
    'rear_small_window_strip_no_large_window':not any(v.y>6.7 and v.x<-18.3 for v in main_windows),
    'rear_small_windows_between_floors':bool(small_windows) and all(any(abs(v.z-(c+d))<.005 for c in [9.50,12.52,15.54] for d in [-.18,.18]) for v in small_windows),
    'rear_glass_door_details':bool(named('rear glass door handles')),
    'rear_landing_present':bool(named('rear entrance landing')),
}
# A sideways ray across the porch must pass through both formerly closed sides.
origin=Vector((-1.2,-7.4,1.8));direction=Vector((1,0,0))
obstructions=[]
for ob in meshes:
    inv=ob.matrix_world.inverted()
    hit,*_=ob.ray_cast(inv @ origin,(inv.to_3x3() @ direction).normalized(),distance=8.9)
    if hit:obstructions.append(ob.name)
checks['porch_sideways_clear']=not obstructions
dark_ground=[]
for ob in named('window mullions')+named('window transoms'):
    color=ob.data.materials[0].diffuse_color
    if max(color[:3])>.2:continue
    if any(v.y>6.7 and v.z<3.0 for v in verts([ob])):dark_ground.append(ob.name)
checks['rear_ground_no_black_frames']=not dark_ground
coplanar_treads=[]
for ob in named('entry steps')+named('rear entrance steps'):
    for face in ob.data.polygons:
        points=[ob.matrix_world @ ob.data.vertices[i].co for i in face.vertices]
        if face.normal.z>.9 and all(abs(v.z-.31)<1e-5 for v in points):coplanar_treads.append(ob.name)
checks['no_steps_flush_over_paving']=not coplanar_treads
parapets=named('parapet')
# Existing name batches may include separate wall runs; inspect disconnected components separately below.
def component_bounds(ob):
    adjacency={v.index:set() for v in ob.data.vertices}
    for edge in ob.data.edges:
        a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
    unseen=set(adjacency);result=[]
    while unseen:
        todo=[unseen.pop()];indices=[]
        while todo:
            current=todo.pop();indices.append(current)
            for other in adjacency[current]:
                if other in unseen:unseen.remove(other);todo.append(other)
        points=[ob.matrix_world @ ob.data.vertices[j].co for j in indices]
        result.append(([min(v[k] for v in points) for k in range(3)],[max(v[k] for v in points) for k in range(3)]))
    return result
parts=[(ob.name,lo,hi) for ob in parapets for lo,hi in component_bounds(ob)]
parapet_overlaps=[]
for i,(name,lo,hi) in enumerate(parts):
    for other,olo,ohi in parts[i+1:]:
        if all(min(hi[k],ohi[k])-max(lo[k],olo[k])>1e-5 for k in range(3)):parapet_overlaps.append([name,other])
checks['parapets_butt_without_volume_overlap']=not parapet_overlaps
result={'checks':checks,'porch_obstructions':obstructions,'rear_dark_ground_frames':dark_ground,
        'coplanar_treads':coplanar_treads,'parapet_overlaps':parapet_overlaps}
print('ROUND2_CHECKS',json.dumps(result))
assert all(checks.values()), 'Round2 failures: '+', '.join(k for k,v in checks.items() if not v)
