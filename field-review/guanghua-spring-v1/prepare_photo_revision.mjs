import fs from 'node:fs';
const dir = new URL('./', import.meta.url);
let source = fs.readFileSync(new URL('rebuild_tree.py', dir), 'utf8');
function replace(a,b) { if(!source.includes(a)) throw Error('Missing source: '+a); source=source.replace(a,b); }
replace("BASE=R/'field-review/guanghua-refinement-v4/closeout-final/guanghua-closeout-final.blend'", "BASE=O/'guanghua-spring-branch-led-v2.blend'");
replace("OUT=O/'guanghua-spring-branch-led-v2.blend'", "OUT=O/'guanghua-spring-photo-v3.blend'");
replace('changed={wood.name,flowers.name,heart.name}', 'changed={wood.name,flowers.name}');
const start=source.indexOf('# Assign the old web batch');
const end=source.indexOf('def bounds(ob):');
source=source.slice(0,start)+source.slice(end);
replace('wv=[];wf=[];wm=[];coarse_faces=[];branch_paths=[];flower_paths=[]', `wv=[];wf=[];wm=[];coarse_faces=[];branch_paths=[];flower_paths=[]
def photo_shape(p):
 return Vector((p[0]*1.30,p[1]*1.20,p[2] if p[2]<1.55 else 1.55+(p[2]-1.55)*.91))`);
replace('pts.append(control[-1]);rs.append(radii[-1]);start=len(wv);face_start=len(wf)', 'pts.append(control[-1]);rs.append(radii[-1]);pts=[photo_shape(p) for p in pts];start=len(wv);face_start=len(wf)');
replace('for ti in range(6):', 'for ti in range(9):');
replace('.05+ti*.16', '.05+ti*.105');
replace('for fi in range(3):', 'for fi in range(4):');
replace('side*((fi-1)*.38)', 'side*((fi-1.5)*.32)');
replace('flower_paths.append(small)', `flower_paths.append(small)
    for qi in range(2):
     stem=small[0].lerp(small[-1],.45+qi*.28)
     spray=fan.normalized()*.32+side*((-1 if qi else 1)*.28)+Vector((0,0,.16))
     fine_tip=tube([stem,stem+spray*.48,stem+spray],[.0045,.0025,.0009],2,4)
     flower_paths.append(fine_tip)`);
replace("int(dist/.11)", "int(dist/.085)");
replace('if rng.random()<.14:continue', 'if rng.random()<.055:continue');
replace('rng.choice([2,2,3])', 'rng.choice([3,3,4])');
replace('rng.uniform(.025,.075)', 'rng.uniform(.035,.095)');
replace('size=rng.uniform(.14,.22)', 'size=rng.uniform(.19,.28)');
replace("[.52,.42,.06]", "[.78,.20,.02]");
replace("me=bpy.data.meshes.new(target+' blossom sprays attached to twigs')", "fv=[tuple(photo_shape(p)) for p in fv];anchors=[list(photo_shape(p)) for p in anchors]\nme=bpy.data.meshes.new(target+' blossom sprays attached to twigs')");
replace("O/'cherry-replacement-native.glb'", "O/'cherry-photo-v3-native.glb'");
replace('non_target_meshes_preserved=len(before)-3', 'non_target_meshes_preserved=len(before)-2');
replace("wood_batch_owner_counts=counts,wood_batch_ambiguities=ambiguities,heart_translation_native=[0,.32,0],", "canopy_horizontal_scale=[1.30,1.20],");
replace("write(O/'native-validation.json',report);write(O/'branch-centerlines.json'", "report['wood_bounds_native']=bounds(wood);report['flower_bounds_native']=bounds(flowers)\nwrite(O/'photo-v3-native-validation.json',report);write(O/'photo-v3-branch-centerlines.json'");
replace("report['wood_bounds_native']=bounds(wood)", "wood=bpy.data.objects[target+' wood'];flowers=bpy.data.objects[target+' leaves']\nreport['wood_bounds_native']=bounds(wood)");
fs.writeFileSync(new URL('rebuild_photo_v3.py', dir), source);
console.log('Prepared tree-only photo revision; original scripts and assets preserved.');
