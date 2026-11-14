"""Geometry checks for user round-3 corrections, against a loaded blend."""
import bpy,json
from mathutils import Vector
meshes=[o for o in bpy.data.objects if o.type=='MESH']
def named(s):return [o for o in meshes if s in o.name]
def points(objects):return [o.matrix_world@v.co for o in objects for v in o.data.vertices]
lawn=points(named('west forecourt lawn'))
target=named('rear unframed entry-adjacent glazing')
trees=named('Trunk T4')
canopies=named('Canopy T4')
checks={
 'lawn_west_matches_building':bool(lawn) and abs(min(v.x for v in lawn)+20.4)<.005,
 'lawn_east_matches_entry_west':bool(lawn) and abs(max(v.x for v in lawn)+.35)<.005,
 'lawn_depth_enlarged':bool(lawn) and max(v.y for v in lawn)-min(v.y for v in lawn)>3.1,
 'rear_target_unframed_glazing':bool(target),
 'rear_window_surround_matches_plaster':bool(named('entry recess back structure')) and min(named('entry recess back structure')[0].data.materials[0].diffuse_color[:3])>.5,
 'four_photo_supported_tree_trunks':len(trees)==4,
 'tree_canopies_present':len(canopies)>=4,
 'tree_toggle_metadata':bool(trees+canopies) and all(o.get('campusVegetation') is True for o in trees+canopies),
}
# Probe only the perimeter of the marked ground window; its internal light grid stays.
hits=[]
for x,z in [(.625,1.95),(3.375,1.95),(2,2.94),(2,.96)]:
 for o in named('window mullions')+named('window transoms'):
  inv=o.matrix_world.inverted()
  hit,*_=o.ray_cast(inv@Vector((x,7.4,z)),Vector((0,-1,0)),distance=.6)
  if hit:hits.append(o.name)
checks['marked_window_outer_frame_removed']=not hits
tree_height=max((v.z for v in points(trees+canopies)),default=0)
checks['trees_larger_than_small_placeholders']=tree_height>8
print('ROUND3_CHECKS',json.dumps({'checks':checks,'perimeter_hits':hits,'tree_max_height':tree_height}))
assert all(checks.values()),'Round3 failures: '+', '.join(k for k,v in checks.items() if not v)
