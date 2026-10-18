import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import sharp from 'sharp';

const root=new URL('../',import.meta.url),pub=new URL('./public/',import.meta.url);
const report=JSON.parse(fs.readFileSync(new URL('field-review/guanghua-campus-integration/integration.json',root)));
for(const [name,hash] of Object.entries(report.baselines))assert.equal(createHash('sha256').update(fs.readFileSync(new URL(name,root))).digest('hex'),hash,`Source changed: ${name}`);
globalThis.self=globalThis;
globalThis.createImageBitmap=async blob=>{
  const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  return {width:info.width,height:info.height,data,close(){}};
};
const loader=new GLTFLoader();
async function load(url){const b=fs.readFileSync(new URL(url,pub));return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const landscape=await load('models/landscape/guanghua-complete-v3.glb');
const colors=new Map();landscape.traverse(o=>{if(o.isMesh)for(const material of Array.isArray(o.material)?o.material:[o.material])colors.set(material.name,material.color.toArray());});
for(const [name,expected] of Object.entries(report.procedural_color_fallbacks??{})){
  const actual=colors.get(name+'_web');assert(actual,`Missing web material ${name}`);
  for(let i=0;i<3;i++)assert(Math.abs(actual[i]-expected[i])<1e-5,`Procedural color lost: ${name}`);
}
assert(colors.get('FIN_grass_web')?.[1]>colors.get('FIN_grass_web')?.[0],'Grass must retain green base color');
const ids=new Set();let meshes=0,textures=0,trees=0;
landscape.traverse(o=>{if(!o.isMesh)return;meshes++;ids.add(o.userData.feature_id);if(o.material.map)textures++;if(o.userData.campusVegetation)trees++;
  const p=o.geometry.attributes.position;for(let i=0;i<p.array.length;i++)assert(Number.isFinite(p.array[i]),o.name);
});
assert(!ids.has('CONTEXT_GUANGHUA'),'Duplicate building context exported');
for(const id of report.feature_ids)assert(ids.has(id),`Missing ${id}`);
assert(textures>0,'Embedded textures missing');assert(trees>=7,'Tree canopy/trunk toggle metadata missing');
const scene=new THREE.Group();scene.add(landscape);
const m=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub)));
for(const a of m.shared.filter(a=>a.id!=='guanghua-landscape'))scene.add(await load(a.id==='00'?'models/shared/00-guanghua-v3.glb':a.id==='05'?'models/shared/05-guanghua-v3.glb':a.url));
// Include the actual building, rather than the proportion-study reference.
const building=m.buildings.find(b=>b.id==='27'),g=await load(building.url);g.position.fromArray(building.position);scene.add(g);
scene.updateMatrixWorld(true);
const s=report.scale,[tx,ty,tz]=report.translation_blender;
const ray=new THREE.Raycaster();
const dx=JSON.parse(fs.readFileSync(new URL('field-review/guanghua-complete-v3/assembly.json',root))).east_translation_x;
const probes=[['LAWN',20,45,3],['WOPEN',-32,81,5],['WOPEN_S',-32,48,5],['EOPEN',79+dx,78,5],['EOPEN_S',78+dx,49.5,5],['WB1',-77,48,1],['WB2',-77,70,1]];
const hits=[];
for(const [id,x,y,h] of probes){
  ray.set(new THREE.Vector3(tx+x*s,tz+h*s,-ty-y*s),new THREE.Vector3(0,-1,0));
  const hit=ray.intersectObject(scene,true)[0];assert(hit,`No surface: ${id}`);
  assert.equal(hit.object.userData.feature_id,id,`${id} obscured by ${hit.object.name}`);
  hits.push({id,object:hit.object.name,height:hit.point.y});
}
// Every unchanged terrain object survives the round trip with the same world
// triangle positions (export may split vertices, reorder nodes and flip axes).
function triangles(group){const list=[];group.updateMatrixWorld(true);group.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,ix=o.geometry.index;
  for(let i=0;i<(ix?ix.count:p.count);i+=3){const vertices=[];for(let j=0;j<3;j++)vertices.push(new THREE.Vector3().fromBufferAttribute(p,ix?ix.getX(i+j):i+j).applyMatrix4(o.matrixWorld).toArray().map(n=>Math.round(n*1000)).join(','));list.push(vertices.sort().join(';'));}
});return list;}
const before=await load('models/shared/05.glb'),after=await load('models/shared/05-guanghua-v3.glb');
const old=new Set(triangles(before)),kept=triangles(after);for(const t of kept)assert(old.has(t),'Existing vegetation geometry moved');
const result={meshes,features:[...ids].sort(),texturedMeshes:textures,treeMeshes:trees,visibleEntryAndLawnProbes:hits,retainedVegetationTriangles:kept.length,baselinesUnchanged:true};
fs.writeFileSync(new URL('field-review/guanghua-campus-integration/validation.json',root),JSON.stringify(result,null,2)+'\n');
if(process.argv.includes('--activate')){
  const asset=url=>{const b=fs.readFileSync(new URL(url,pub));return {url,revision:createHash('sha256').update(b).digest('hex').slice(0,12),bytes:b.length};};
  for(const a of m.shared){if(a.id==='00')Object.assign(a,asset('models/shared/00-guanghua-v3.glb'));if(a.id==='05')Object.assign(a,asset('models/shared/05-guanghua-v3.glb'));}
  m.shared=m.shared.filter(a=>a.id!=='guanghua-landscape');
  m.shared.push({id:'guanghua-landscape',name:'Guanghua complete south landscape',...asset('models/landscape/guanghua-complete-v3.glb')});
  fs.writeFileSync(new URL('campus-manifest.json',pub),JSON.stringify(m,null,2)+'\n');
}
console.log(`PASS: Guanghua landscape ${meshes} meshes, ${report.feature_ids.length} features; seven campus surface probes; vegetation retained without moving; source hashes unchanged`);
