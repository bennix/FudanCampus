import fs from 'node:fs';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import sharp from 'sharp';
import {readModelBytes} from './read-model-bytes.mjs';

const root=new URL('../',import.meta.url),pub=new URL('./public/',import.meta.url);
const manifest=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub)));
const asset=manifest.shared.find(a=>a.id==='guanghua-landscape');
assert(asset?.closeoutReport,'Unified landscape requires an explicit closeoutReport; the obsolete hardcoded v3 entry is retired');
const reportUrl=new URL(asset.closeoutReport,root),out=new URL('./',reportUrl);
const report=JSON.parse(fs.readFileSync(reportUrl));
const hash=p=>createHash('sha256').update(fs.readFileSync(p)).digest('hex');
if(fs.existsSync(report.source))assert.equal(hash(report.source),report.source_sha256,'Native source changed after export');
else console.log('Native Blender source archived locally; validating delivered web geometry');
for(const [relative,expected] of Object.entries(report.baselines))assert.equal(hash(new URL(relative,pub)),expected,`Protected previous asset changed: ${relative}`);
const before=JSON.parse(fs.readFileSync(new URL('campus-manifest-before.json',out)));
for(const b of manifest.buildings.filter(b=>b.id!=='27'))assert.deepEqual(b,report.upstream_merge?.buildings?.find(a=>a.id===b.id)??before.buildings.find(a=>a.id===b.id),`Other building manifest changed: ${b.id}`);
for(const a of manifest.shared.filter(a=>!['guanghua-landscape','05'].includes(a.id))){const expected=a.id==='00'&&report.upstream_merge?report.upstream_merge.terrain:a.id==='58'&&report.upstream_merge?report.upstream_merge.statue:before.shared.find(b=>b.id===a.id);if(a.id==='58'){assert.equal(a.url,'models/shared/58.glb');assert.equal(a.sourceModel,'https://sketchfab.com/3d-models/ef18c25e1e094cf99e2b377ad7377d05');assert.equal(a.license,'CC BY 4.0');}else assert.deepEqual(a,expected,`Other shared manifest changed: ${a.id}`);const bytes=readModelBytes(new URL(a.url,pub));assert.equal(bytes.length,a.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),a.revision);}
for(const a of [report.landscape,report.building,report.vegetation_reused]){const bytes=readModelBytes(new URL(a.url,pub));assert.equal(bytes.length,a.bytes);assert.equal(createHash('sha256').update(bytes).digest('hex').slice(0,12),a.revision);}
assert(report.landscape.bytes+report.building.bytes+report.vegetation_reused.bytes<=150*1024*1024,'Combined new assets exceed 150 MiB');
globalThis.self=globalThis;
globalThis.createImageBitmap=async blob=>{const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});return {width:info.width,height:info.height,data,close(){}};};
await MeshoptDecoder.ready;
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
async function load(url){const b=readModelBytes(new URL(url,pub));return (await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'')).scene;}
const landscape=await load(report.landscape.url);landscape.updateMatrixWorld(true);
function inherit(o,key){for(let n=o;n;n=n.parent)if(n.userData[key]!==undefined)return n.userData[key];}
const ids=new Set(),texts=[],lod={near:0,middle:0,far:0,static:0},geometries=new Map(),sources=new Map(),textures=new Set();let meshes=0;
landscape.traverse(o=>{
 if(o.userData.text_content){const box=new THREE.Box3().setFromObject(o);assert(!box.isEmpty(),`Empty text ${o.name}`);texts.push({name:o.name,body:o.userData.text_content,feature:o.userData.feature_id,min:box.min.toArray(),max:box.max.toArray()});}
 if(!o.isMesh)return;
 for(const key of ['feature_id','closeout_lod','source_object','campusVegetation'])if(o.userData[key]===undefined)o.userData[key]=inherit(o,key);
 meshes++;ids.add(o.userData.feature_id);assert.notEqual(o.userData.feature_id,'CONTEXT_GUANGHUA','Reference building duplicated in landscape');
 const p=o.geometry.attributes.position;assert(p?.count>0,o.name);for(let i=0;i<p.array.length;i++)assert(Number.isFinite(p.array[i]),`Non-finite ${o.name}`);
 const level=o.userData.closeout_lod||'static';lod[level]+=(o.geometry.index?.count||p.count)/3;
 geometries.set(o.geometry,(geometries.get(o.geometry)||0)+1);
 if(level!=='static'){
  const key=o.userData.source_object;const set=sources.get(key)||new Set();set.add(level);sources.set(key,set);
 }
 for(const m of Array.isArray(o.material)?o.material:[o.material])for(const k of ['map','normalMap','roughnessMap','metalnessMap','alphaMap'])if(m[k])textures.add(m[k]);
});
for(const fid of report.feature_ids)assert(ids.has(fid),`Feature missing: ${fid}`);
for(const [key,set] of sources)assert.deepEqual([...set].sort(),['far','middle','near'],`Incomplete levels: ${key}`);
assert(textures.size>0);assert([...geometries.values()].some(n=>n>1),'Prototype sharing missing');
const fontRecords=texts.filter(t=>['FUDAN','光华楼广场自行车库'].includes(t.body));
assert.equal(fontRecords.length,3,'Three editable native texts must become three named GLB text nodes');
for(const fid of ['WB1','WB2']){const t=fontRecords.find(t=>t.feature===fid);assert(t);assert(Math.abs(t.max[2]-t.min[2]-5.12*report.scale)<.004,'Garage text world width changed');}
assert(texts.some(t=>t.body==='驢背詩思'),'Traditional sculpture inscription missing');
const building=manifest.buildings.find(b=>b.id==='27'),house=await load(building.url);house.position.fromArray(building.position);house.rotation.fromArray(building.rotation);house.updateMatrixWorld(true);
const scene=new THREE.Group();scene.add(landscape,house);
for(const a of manifest.shared.filter(a=>a.id!=='guanghua-landscape'))scene.add(await load(a.url));scene.updateMatrixWorld(true);
scene.traverse(o=>{if(o.isMesh&&o.userData.feature_id===undefined)o.userData.feature_id=inherit(o,'feature_id');});
const s=report.scale,[tx,ty,tz]=report.translation_blender;
const probeSpecs=[['LAWN',20,45],['WOPEN',-32,71],['WOPEN_S',-32,47],['EOPEN',72.30211756,71],['EOPEN_S',71.30211756,48.5]];
const hits=[];const ray=new THREE.Raycaster();
const hard=[];scene.traverse(o=>{if(o.isMesh&&!o.userData.campusVegetation&&!['GARDEN_VEGETATION_V3','TREE_CANOPY_V6','VEGETATION','VEGETATION_V2','VEGETATION_PILOT'].includes(o.userData.feature_id))hard.push(o);});
for(const [id,x,y] of probeSpecs){ray.set(new THREE.Vector3(tx+x*s,tz+30*s,-ty-y*s),new THREE.Vector3(0,-1,0));const h=ray.intersectObjects(hard,false)[0];assert(h,`No surface ${id}`);assert.equal(h.object.userData.feature_id,id,`${id} obscured by ${h.object.name}`);hits.push({id,object:h.object.name,height:h.point.y});}
// Retained shared vegetation is a subset of the original world triangles.
function triangles(group){const list=[];group.updateMatrixWorld(true);group.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position,ix=o.geometry.index;for(let i=0;i<(ix?.count||p.count);i+=3){const v=[];for(let j=0;j<3;j++)v.push(new THREE.Vector3().fromBufferAttribute(p,ix?ix.getX(i+j):i+j).applyMatrix4(o.matrixWorld).toArray().map(n=>Math.round(n*1000)).join(','));list.push(v.sort().join(';'));}});return list;}
const original=new Set(triangles(await load('models/shared/05.glb'))),retained=triangles(await load(report.vegetation_reused.url));
assert(retained.every(t=>original.has(t)),'Retained outside vegetation moved');
// No old shared terrain/vegetation may enter the inherited interior envelope.
const rectangle=report.inherited_footprint;const violations=[];
for(const a of [report.terrain_reused,report.vegetation_reused]){
 const g=await load(a.url);g.updateMatrixWorld(true);g.traverse(o=>{if(!o.isMesh)return;const p=o.geometry.attributes.position;for(let i=0;i<p.count;i++){const q=new THREE.Vector3().fromBufferAttribute(p,i).applyMatrix4(o.matrixWorld),x=(q.x-tx)/s,y=(-q.z-ty)/s;
 if(x>rectangle[0]+.004&&x<rectangle[1]-.004&&y>rectangle[2]+.004&&y<rectangle[3]-.004){violations.push({asset:a.url,object:o.name,x,y});break;}}});
}
assert.equal(violations.length,0,JSON.stringify(violations));
const textureBytes=[...textures].reduce((n,t)=>n+(t.image?.width||0)*(t.image?.height||0)*4*4/3,0);
const result={source_sha256:report.source_sha256,production_assets:[report.landscape,report.building],meshes,features:[...ids].sort(),textNodes:texts,trianglesByLod:lod,threeLevelGroups:sources.size,sharedGeometries:[...geometries.values()].filter(n=>n>1).length,textures:textures.size,estimatedRgbaTextureBytesWithMipmaps:Math.ceil(textureBytes),surfaceProbes:hits,retainedVegetationTriangles:retained.length,duplicateOutsideAssetVertices:violations,otherCampusAssetsUnchanged:true,compressedProductionGLBLoadsInThree:true};
fs.writeFileSync(new URL('glb-validation.json',out),JSON.stringify(result,null,2)+'\n');
console.log(`PASS: unified Guanghua ${meshes} meshes; ${texts.length} text nodes; ${sources.size} complete LOD groups; surface and duplication probes; protected campus assets unchanged`);
