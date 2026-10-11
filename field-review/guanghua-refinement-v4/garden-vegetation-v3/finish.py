"""Final visual corrections after two diagnostic batches; garden plants only."""
import bpy,math,random,json,ast
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
O=Path(__file__).resolve().parent;OUT=O/'garden-vegetation-v3.blend'
bpy.ops.wm.open_mainfile(filepath=str(OUT));S=bpy.context.scene
C=bpy.data.collections['12_Garden vegetation v3'];rng=random.Random(93084);B={};leaf_count=0;trees=[]
M=[bpy.data.materials['GV3 '+n] for n in ['deep olive','olive','grey green','fresh green','leaf underside','burgundy','bronze','autumn','fissured grey bark']]
report=json.loads((O/'validation.json').read_text(encoding='utf-8'))
script=(O/'build.py').read_text(encoding='utf-8');t=ast.parse(script)
exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef) and n.name in ['add','leaf','tube','flush','tree']],type_ignores=[]),'<garden plant helpers>','exec'))
block=script.split('# Ground and hardscape queries only constrain the new planting. No source edit.')[1].split('trees=[]')[0]
block=block.replace("'E_PLANTING'}","'E_PLANTING','GARDEN_VEGETATION_V3'}")
exec(block)
prototypes=[[me for me in bpy.data.meshes if me.name.startswith('GV3 shrub prototype '+str(k)+' ')] for k in range(6)]
added=[]
for i,(x,y) in enumerate([(-76.5,y) for y in [38,42,46,54,58,62,66,70,74,78]]+[(-70,78),(-66,80),(-62,79),(-57,77),(94,73),(96,77),(96,81)]):
    z=ground(x,y,.70)
    if z is None:continue
    kind=rng.choice([0,1,2,4]);h=rng.uniform(2.6,4.1)
    for me in prototypes[kind]:
        ob=bpy.data.objects.new('GV3 tall understory %02d '%i+me.name,me);C.objects.link(ob);ob.location=(x,y,z);ob.scale=(rng.uniform(1.25,1.72),rng.uniform(1.25,1.72),h/1.23);ob.rotation_euler.z=rng.uniform(0,math.tau);ob['feature_id']='GARDEN_VEGETATION_V3';ob['source_photos']=[4384,4390,4582];ob['geometry_confidence']='Tall garden understory inferred from photographic habit'
    added.append(dict(x=x,y=y,z=z,height=h,kind=kind))

# Recover the photographed tree inside the existing circular bench.
seat=next(ob for ob in S.objects if ob.type=='MESH' and 'ring-seat' in ob.name)
pts=[seat.matrix_world@Vector(p) for p in seat.bound_box]
cx=(min(p.x for p in pts)+max(p.x for p in pts))/2;cy=(min(p.y for p in pts)+max(p.y for p in pts))/2
tree('East ring-seat mature tree',cx,cy,.025,13.4,5.25,True,1)
tube('East ring-seat mature tree bark',[(cx+.22,cy,.025),(cx+.42,cy+.07,2.1),(cx+.65,cy+.12,4.3),(cx+1.2,cy+.28,6.1)],.23,.10)
flush()
report['trees'].extend(trees)
# Fine vine foliage replaces the conspicuous balls along the existing pergola.
for name in ['ERAMP__vine-leaf-clusters__leaf-green']:
    ob=bpy.data.objects[name];ob.data.calc_loop_triangles()
    for tri in ob.data.loop_triangles:
        a,b,c=[ob.matrix_world@ob.data.vertices[i].co for i in tri.vertices];normal=(b-a).cross(c-a);area=normal.length*.5
        if area<1e-7:continue
        normal.normalize()
        for _ in range(round(area*780)):
            u=math.sqrt(rng.random());v=rng.random();p=a*(1-u)+b*u*(1-v)+c*u*v+normal*.035
            leaf('GV3 pergola fine vine leaves',p,rng.uniform(.033,.064),rng.choice([1,1,2,3]),width=.52)
    for old in [ob,bpy.data.objects['V2 leaves ERAMP']]:
        old.hide_render=True;old.hide_set(True);report['hidden_old_garden_plants'].append(old.name)
flush()
# Bend new tree skeletons and their attached leaves together to soften straight forks.
for idx,d in enumerate(report['trees']):
    for ob in list(C.objects):
        if ob.type!='MESH' or not ob.name.startswith(d['name']+' '):continue
        a=np.empty(len(ob.data.vertices)*3,np.float32);ob.data.vertices.foreach_get('co',a);a=a.reshape(-1,3)
        z=np.maximum(0,a[:,2]-d['z']);phase=idx*1.871
        a[:,0]+=(np.sin(z/d['height']*7+phase)-math.sin(phase))*.23*z/d['height']
        a[:,1]+=(np.cos(z/d['height']*6+phase)-math.cos(phase))*.32*z/d['height']
        ob.data.vertices.foreach_set('co',a.ravel());ob.data.update()
overlay=bpy.data.objects.get('GV3 garden turf surface')
if overlay:bpy.data.objects.remove(overlay,do_unlink=True)
report['tall_understory_added']=added;report['pergola_vines_refined']=True;report['ring_bench_tree_restored']=True
report['generated_leaf_count']+=leaf_count
S['garden_v3_finish']='Mixed shrub layers, continuous mature west crowns, fine pergola vines, tree in ring bench; turf overlay rejected after visual review'
S.view_settings.exposure=.65
bpy.ops.wm.save_as_mainfile(filepath=str(OUT),compress=True)
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('FINISH_SAVED',len(added),leaf_count,cx,cy,flush=True)
