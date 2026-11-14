"""Check real geometry contacts, including regressions found by independent review."""
from pathlib import Path
import bpy
import json
from mathutils import Vector

HERE=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(HERE/'17-candidate.glb'))
bpy.context.view_layer.update()


def ob(label):
    return next(o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('T4 '+label))


def world_vertices(o):
    return [o.matrix_world @ v.co for v in o.data.vertices]


pages=world_vertices(ob('curved book page blocks'))
covers=world_vertices(ob('overhanging book covers'))
z_covers={round(v.z,5) for v in covers}
page_extremes=[1.96+i*.43+dz for i in range(7) for dz in [-.15,.15]]
gaps=[min(abs(z-cz) for cz in z_covers) for z in page_extremes]
clock_min=min(v.z for v in world_vertices(ob('upright clock book')))
checks={
    'page_cover_contacts':max(gaps)<1e-4,
    'upright_book_contacts_stack':abs(clock_min-max(v.z for v in covers))<1e-4,
}
# Probe the exposed treads, rather than inferring walkable steps from object names.
steps=ob('entry steps')
heights=[]
for y in [-8.05,-8.36,-8.67,-8.98]:
    inv=steps.matrix_world.inverted()
    hit,location,_,_=steps.ray_cast(inv @ Vector((3.7,y,10)),Vector((0,0,-1)))
    heights.append((steps.matrix_world @ location).z if hit else None)
checks['exposed_continuous_treads']=all(h is not None for h in heights) and all(.09 < heights[i]-heights[i+1] < .15 for i in range(3))
floor_min=min(v.y for v in world_vertices(ob('entry recess floor')))
checks['landing_does_not_cover_treads']=floor_min>=-7.81
coping=ob('sandstone plinth coping')
inv=coping.matrix_world.inverted()
hit,*_=coping.ray_cast(inv @ Vector((3.7,-10,.94)),Vector((0,1,0)),distance=4)
checks['front_entry_coping_clear']=not hit
side=ob('side sandstone plinth')
inv=side.matrix_world.inverted()
hit,*_=side.ray_cast(inv @ Vector((23,-4.45,.60)),Vector((-1,0,0)),distance=3)
checks['side_door_plinth_clear']=not hit
result={'checks':checks,'max_cover_gap':max(gaps),'upright_gap':clock_min-max(v.z for v in covers),'tread_heights':heights}
print('CONTACT_CHECKS',json.dumps(result))
assert all(checks.values()), 'Contact failures: '+', '.join(k for k,v in checks.items() if not v)
