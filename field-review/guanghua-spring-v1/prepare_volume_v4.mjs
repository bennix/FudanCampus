import fs from 'node:fs';
const dir=new URL('./',import.meta.url);
let source=fs.readFileSync(new URL('rebuild_photo_v3.py',dir),'utf8');
function replace(a,b){if(!source.includes(a))throw Error('Missing '+a);source=source.replace(a,b);}
replace("BASE=O/'guanghua-spring-branch-led-v2.blend'", "BASE=O/'guanghua-spring-photo-v3.blend'");
source=source.replaceAll('guanghua-spring-photo-v3','guanghua-spring-volume-v4');
replace("BASE=O/'guanghua-spring-volume-v4.blend'", "BASE=O/'guanghua-spring-photo-v3.blend'");
source=source.replaceAll('cherry-photo-v3-native','cherry-volume-v4-native').replaceAll('photo-v3-native-validation','volume-v4-native-validation').replaceAll('photo-v3-branch-centerlines','volume-v4-branch-centerlines');
const ma=source.indexOf('def material('),mb=source.indexOf('wv=[];');
source=source.slice(0,ma)+"# Reuse accepted native materials exactly.\nbarks=list(wood.data.materials)[:3];white=wood.data.materials[3]\n"+source.slice(mb);
const fa=source.indexOf('atlas=bpy.data.images.load('),fb=source.indexOf('fv=[];');
source=source.slice(0,fa)+"flower_mats=list(flowers.data.materials)\n"+source.slice(fb);
replace('attach=mid.lerp(end,.05+ti*.105)', 'attach=mid.lerp(end,.04+ti*.105+rng.uniform(-.03,.03))');
replace('d=side*((-1 if ti%2 else 1)*rng.uniform(.55,1.0))+radial*rng.uniform(.1,.65)+Vector((0,0,rng.uniform(.35,1.05)))', `azimuth=rng.uniform(0,2*math.pi)
   d=side*(math.cos(azimuth)*rng.uniform(.35,.95))+radial*rng.uniform(-.40,.65)+Vector((0,0,rng.uniform(.15,.95)))`);
replace('fan=d.normalized()*.55+side*((fi-1.5)*.32)+Vector((0,0,.28+rng.uniform(-.12,.16)))', `angle=rng.uniform(0,2*math.pi)
    fan=d.normalized()*rng.uniform(.20,.48)+Vector((math.cos(angle)*rng.uniform(.15,.40),math.sin(angle)*rng.uniform(.15,.40),rng.uniform(-.12,.37)))`);
replace('spray=fan.normalized()*.32+side*((-1 if qi else 1)*.28)+Vector((0,0,.16))', `angle=rng.uniform(0,2*math.pi)
     spray=fan.normalized()*rng.uniform(.16,.30)+Vector((math.cos(angle)*rng.uniform(.12,.25),math.sin(angle)*rng.uniform(.12,.25),rng.uniform(-.12,.25)))`);
replace('# Low buttress roots are retained at the original root location.', `# Connected interior shoots bridge the sparse centre at several heights.
# Each is anchored to an existing main limb; no detached flower clouds.
interior_paths=[]
for ci in range(16):
 main=[Vector(p) for p in primary_specs[ci%len(primary_specs)]]
 start=main[1].lerp(main[2],rng.uniform(.35,.85))
 angle=ci*2.399963+ rng.uniform(-.22,.22)
 radius=rng.uniform(.35,2.1)
 end=Vector((math.cos(angle)*radius,math.sin(angle)*radius,rng.uniform(4.65,6.65)))
 mid=start.lerp(end,.52)+Vector((rng.uniform(-.22,.22),rng.uniform(-.22,.22),.14))
 stem=tube([start,mid,end],[.042,.021,.004],1,6)
 interior_paths.append(stem[1:])
 for ti in range(10):
  attach=mid.lerp(end,rng.uniform(.10,.95));az=rng.uniform(0,2*math.pi)
  delta=Vector((math.cos(az)*rng.uniform(.35,1.15),math.sin(az)*rng.uniform(.35,1.15),rng.uniform(-.2,.75)))
  tip=attach+delta
  twig=tube([attach,attach.lerp(tip,.48)+Vector((0,0,.06)),tip],[.015,.008,.0016],2,5)
  interior_paths.append(twig)
  for fi in range(4):
   at=twig[1].lerp(twig[2],rng.uniform(.10,.85));az=rng.uniform(0,2*math.pi)
   delta=Vector((math.cos(az)*rng.uniform(.16,.40),math.sin(az)*rng.uniform(.16,.40),rng.uniform(-.16,.40)))
   interior_paths.append(tube([at,at+delta*.47,at+delta],[.005,.0025,.0008],2,4))
flower_paths.extend(interior_paths)
# Low buttress roots are retained at the original root location.`);
replace('int(dist/.085)', 'int(dist/.075)');
replace('rng.choice([3,3,4])', 'rng.choice([4,4,5])');
replace('c=center+radial*rng.uniform(.035,.095);normal=(radial+tangent*rng.uniform(-.5,.5)).normalized()', `c=center+radial*rng.uniform(.045,.20)+tangent*rng.uniform(-.045,.045)
    normal=Vector((rng.uniform(-1,1),rng.uniform(-1,1),rng.uniform(-1,1))).normalized()`);
replace('size=rng.uniform(.19,.28)', 'size=rng.uniform(.105,.175)');
replace('start=len(fv);fv.extend([tuple(c-x-y),tuple(c+x-y),tuple(c+x+y),tuple(c-x+y)]);ff.append((start,start+1,start+2,start+3));fm.append(rng.choices([0,1,2],[.78,.20,.02])[0])', `# Six-vertex shallow curved spray: two differently facing halves.
    bulge=normal*size*rng.uniform(.16,.30)
    start=len(fv);fv.extend([tuple(c-x-y),tuple(c-y+bulge),tuple(c+x-y),tuple(c-x+y),tuple(c+y+bulge),tuple(c+x+y)])
    mi=rng.choices([0,1,2],[.78,.20,.02])[0]
    ff.extend([(start,start+1,start+4,start+3),(start+1,start+2,start+5,start+4)]);fm.extend([mi,mi])`);
replace("for p in me.polygons:\n for li,coord in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]):uv.data[li].uv=coord", `for pi,p in enumerate(me.polygons):
 coords=[(0,0),(.5,0),(.5,1),(0,1)] if pi%2==0 else [(.5,0),(1,0),(1,1),(.5,1)]
 for li,coord in zip(p.loop_indices,coords):uv.data[li].uv=coord`);
replace('blossom_cards=len(ff)', 'blossom_cards=len(ff)//2');
replace("report['wood_bounds_native']=bounds(wood)", "report['central_shoots']=16;report['generation']='Non-coplanar connected twigs; volumetric anchors; small curved two-half blossom sprays';report['materials_reused']=True\nreport['wood_bounds_native']=bounds(wood)");
fs.writeFileSync(new URL('rebuild_volume_v4.py',dir),source);
// Web integration is maintained separately in integrate_volume_v4.mjs.
console.log('Prepared v4 native tree generation; run integrate_volume_v4.mjs after Blender validation.');
