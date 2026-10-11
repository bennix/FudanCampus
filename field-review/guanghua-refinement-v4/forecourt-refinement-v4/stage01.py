import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
bpy.ops.wm.open_mainfile(filepath=str(BASE));s=bpy.context.scene
before=all_digests();required={o.get('feature_id') for o in s.objects if o.get('feature_id')}
lock=dict(source=str(BASE),source_sha256=sha(BASE),all_meshes=before,required_ids=sorted(required),invariants=['主草坪原轮廓及变换','楼体主体：入口旧平台与10段台阶以外的全部网格','西花园入口及楼梯口、花钵、北端曲径接缝'],dimensions='All new dimensions inferred')
(O/'baseline-lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2),encoding='utf-8')
for ob in s.objects:
 if ob.get('feature_id') in ['LAWN','CONTEXT_GUANGHUA','W_ENTRY','WOPEN','WPATH']:
  ob.lock_location=(True,True,True);ob.lock_rotation=(True,True,True);ob.lock_scale=(True,True,True)
  ob['v4_protection']='Protected baseline geometry and world transform; building entry components excepted'
if not (O/'stage00-v3-copy.blend').exists():bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage00-v3-copy.blend'))
cams={
 'top':camera('V4 ENTRY overhead',(20,105,160),(20,105,0),153),
 '4464':camera('V4 approximate photo4464',(-42,88.5,2.2),(-48,111,2.8),lens=27),
 '4485':camera('V4 approximate photo4485',(100,100,2.15),(-20,102,1.5),lens=25)}
if not (O/'stage01-before-top.png').exists():render('stage01-before-top.png',cams['top'],True,width=1000,samples=10,ratio=.42)
if not (O/'stage01-before-4464.png').exists():render('stage01-before-4464.png',cams['4464'],width=1000,samples=10)
changed=[];preserved_components={}
# Separate the ten old steps and the old entrance slab from material-batched
# building meshes. Every remaining vertex and face stays byte-for-byte in place.
for ob in list(s.objects):
 if ob.type!='MESH' or ob.get('feature_id')!='CONTEXT_GUANGHUA':continue
 if not any(t in ob.name for t in ['light stone','rose grey']):continue
 bm=bmesh.new();bm.from_mesh(ob.data);unseen=set(bm.verts);remove=set();keep=[]
 while unseen:
  todo=[unseen.pop()];vs=set(todo)
  while todo:
   v=todo.pop()
   for e in v.link_edges:
    q=e.other_vert(v)
    if q in unseen:unseen.remove(q);vs.add(q);todo.append(q)
  ps=[ob.matrix_world@v.co for v in vs]
  if max(p.z for p in ps)<3.46 and min(p.y for p in ps)<121:remove|=vs
  else:keep.extend(tuple(v.co) for v in vs)
 if remove:
  changed.append(ob.name);preserved_components[ob.name]=sorted(keep)
  bmesh.ops.delete(bm,geom=list(remove),context='VERTS');bm.to_mesh(ob.data);ob.data.update()
  assert sorted(tuple(v.co) for v in ob.data.vertices)==preserved_components[ob.name]
 bm.free()
stone=bpy.data.materials['FC_warm_granite'];pale=bpy.data.materials['FC_light_band'];urnmat=bpy.data.materials['FC_fluted_white'];soil=bpy.data.materials['FIN_garden_grass']
burgundy=bpy.data.materials.new('V4 clipped burgundy foliage');burgundy.diffuse_color=(.18,.052,.082,1);burgundy.use_nodes=True
burgundy.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.18,.052,.082,1)
burgundy.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.88
fid='BUILDING_ENTRY';refs=[4464,4485];new=[];connections=[]
def add(ob):new.append(ob);return ob
add(box('BENTRY upper platform',(20,122.25,1.7425),(103.5,10.5,3.415),stone,fid,refs))
# Main staircase has a single watertight stepped body instead of overlapping boxes.
N=22;low=.035;high=3.45;y0=109.08;y1=117;rise=(high-low)/N;run=(y1-y0)/N
profile=[(y0,-.035),(y1,-.035),(y1,high)]
for i in range(N-1,-1,-1):profile.extend([(y0+i*run,low+(i+1)*rise),(y0+i*run,low+i*rise)])
profile=profile[:-1]
n=len(profile);vs=[(x,y,z) for x in (-16,56) for y,z in profile]
fs=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
steps=add(mesh('BENTRY continuous main stair',vs,fs,pale,fid,refs))
for i in range(N):
 y=y0+i*run;z=low+(i+1)*rise
 add(box('BENTRY stair nose %02d'%i,(20,y+.026,z+.006),(72,.052,.012),stone,fid,refs))
# Left and right mirrored studies preserve the existing building access level.
# Symmetry of the hidden plan is explicitly inferred, not confirmed by photos.
for side in (1,-1):
 tag='east' if side==1 else 'west';mirror=lambda p:(20+side*(p[0]-20),p[1])
 def grade(x,y):return low+(high-low)*max(0,min(1,(y-100)/20))
 def walltop(x,y):return grade(x,y)+.75
 ramp_pts=[mirror(p) for p in [(87.25,100),(92.75,100),(76.75,120),(71.25,120)]]
 ramp=add(prism('BENTRY '+tag+' sloping ramp',ramp_pts,-.035,grade,stone,fid,refs))
 ramp['estimated_rise_run']=[3.415,25.6125];ramp['ramp_grade_status']='推定：继承楼前标高的比例研究，未作实测或规范认证'
 wing=add(box('BENTRY '+tag+' upper landing wing',(20+side*54.25,122,1.7425),(5.5,4,3.415),stone,fid,refs))
 # One curb chain becomes the round plinth and ramp retaining wall by exact union.
 outer=[mirror((92.75-16*t,100+20*t)) for t in [i/50 for i in range(51)]]
 wall=add(ribbon('BENTRY '+tag+' outer retaining wall',outer,.52,-.035,walltop,stone,fid,refs))
 pl=lathe('BENTRY '+tag+' outer round plinth',*mirror((92.75,100)),[(1.38,-.035),(1.38,.785)],stone,fid,refs)
 union(wall,pl)
 cap=add(ribbon('BENTRY '+tag+' outer coping',outer,.64,lambda x,y:walltop(x,y)-.005,lambda x,y:walltop(x,y)+.13,pale,fid,refs))
 plcap=lathe('BENTRY '+tag+' outer cap join',*mirror((92.75,100)),[(1.47,.78),(1.50,.81),(1.50,.87),(1.47,.915)],pale,fid,refs)
 union(cap,plcap)
 # Broad convex arc + the inner ramp edge form a closed planted terrace.
 arc=bezier((87.25,100),(70,98.5),(56,107),(56,117),50)
 plan=arc+[(71.25,120)]
 plantpoly=[mirror(p) for p in plan]
 bed=add(prism('BENTRY '+tag+' curved planter soil',plantpoly,-.035,lambda x,y:walltop(x,y)-.03,soil,fid,refs))
 chain=[mirror(p) for p in arc]+[mirror((71.25,120)),mirror((87.25,100))]
 bedwall=add(ribbon('BENTRY '+tag+' curved planter wall',chain,.50,-.035,walltop,stone,fid,refs))
 inner=lathe('BENTRY '+tag+' inner round plinth',*mirror((87.25,100)),[(1.38,-.035),(1.38,.785)],stone,fid,refs);union(bedwall,inner)
 bedcap=add(ribbon('BENTRY '+tag+' curved coping',chain,.62,lambda x,y:walltop(x,y)-.005,lambda x,y:walltop(x,y)+.13,pale,fid,refs))
 innercap=lathe('BENTRY '+tag+' inner cap join',*mirror((87.25,100)),[(1.47,.78),(1.50,.81),(1.50,.87),(1.47,.915)],pale,fid,refs);union(bedcap,innercap)
 # Decorative urns sit exactly on the continuous cap, rather than float above it.
 for kind,cx in [('outer',92.75),('inner',87.25)]:
  qx,qy=mirror((cx,100))
  profile=[(.55,.915),(.66,.94),(.66,1.02),(.58,1.07),(.43,1.22),(.43,1.32),(.62,1.38),(.88,1.60),(1.18,1.79),(1.22,1.86),(1.12,1.87),(.99,1.71),(.68,1.48),(0,1.46)]
  bowl=add(lathe('BENTRY '+tag+' '+kind+' urn',qx,qy,profile,urnmat,fid,refs,.016))
  for component in ['broad leaves','red flowers','soil']:
   src=bpy.data.objects['E_ENTRY 0 '+component];ob=src.copy();ob.data=src.data.copy();ob.parent=None;collection('09_V4 photo refinement').objects.link(ob);ob.name='BENTRY '+tag+' '+kind+' '+component
   # Source coordinates are world authored; copied foliage is translated as a whole.
   xs=[v.co.x for v in ob.data.vertices];ys=[v.co.y for v in ob.data.vertices]
   scx=(min(xs)+max(xs))/2;scy=(min(ys)+max(ys))/2
   for v in ob.data.vertices:v.co+=Vector((qx-scx,qy-scy,0))
   ob.matrix_world.identity();ob['feature_id']=fid;ob['source_photos']=refs;ob['dimension_status']='推定';new.append(ob)
 connections.append(dict(side=tag,wall_and_round_plinth='Boolean union: no shared open edge',coping_and_round_cap='Boolean union',urn_foot_z=.915,cap_top_z=.915,landing_z=high,ramp_end_z=high))
 # Simple clipped hedge volumes follow the planted region; no hidden plant species claim.
 hedge=burgundy
 center=(73,108);outerline=[Vector(p) for p in arc]
 inset=[tuple(Vector(center).lerp(p,.83)) for p in outerline]+[(70.5,117)]
 add(prism('BENTRY '+tag+' burgundy planting',[mirror(p) for p in inset],lambda x,y:walltop(x,y),lambda x,y:walltop(x,y)+.35,hedge,fid,refs))
 green=bpy.data.materials['FIN_hedge'];small=[(70,106),(62,111),(61.5,115.5),(66,117),(72,114.5),(76,104.5)]
 add(prism('BENTRY '+tag+' clipped green planting',[mirror(p) for p in small],lambda x,y:walltop(x,y)+.15,lambda x,y:walltop(x,y)+.42,green,fid,refs))
 # A continuous apron fills the former scene gap immediately below the landing.
 add(prism('BENTRY '+tag+' platform apron',[mirror(p) for p in [(71,113),(79,113),(77,124),(71,124)]],-.035,.035,stone,fid,refs))
solids=[solid_check(ob) for ob in new if ob.type=='MESH' and not any(k in ob.name for k in ['leaves','flowers','soil'])]
unchanged=verify_unchanged(before,changed)
s['active_checkpoint']='v4 stage01 building access';s['dimension_status']='推定 / not surveyed'
s.camera=cams['4464'];bpy.ops.wm.save_as_mainfile(filepath=str(O/'stage01-building-entry.blend'))
report=dict(protected_meshes_unchanged=unchanged,building_mesh_exceptions=changed,remaining_building_components_unchanged=True,connections=connections,solids=solids,step_count=N,inferred=dict(stair_rise=rise,stair_tread=run,landing_height=high,ramp_run=25.61,symmetry='Unseen mirrored plan inferred'),views=['top','4464','4485'])
save_report('stage01',report)
for k,cam in cams.items():render('stage01-after-'+k+'.png',cam,k=='top',width=1400,samples=24,ratio=.42 if k=='top' else .75)
print('STAGE01_COMPLETE',flush=True)
