import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import ts from 'typescript';
import * as THREE from 'three';
// Transpile the controller only, retaining real Three.js resource lifecycles.
let source=await readFile(new URL('../lib/campus-lod.ts',import.meta.url),'utf8');
source=source.replace("'three'",JSON.stringify(import.meta.resolve('three'))).replace("'three/addons/loaders/GLTFLoader.js'",JSON.stringify(import.meta.resolve('three/addons/loaders/GLTFLoader.js'))).replace("'three/addons/libs/meshopt_decoder.module.js'",JSON.stringify(import.meta.resolve('three/addons/libs/meshopt_decoder.module.js'))).replace("'./lod-policy'",JSON.stringify(new URL('../lib/lod-policy.ts',import.meta.url).href));
const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText;
const {CampusLod,disposeGroup}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
const tick=()=>new Promise(r=>setImmediate(r));
const asset={id:'statue',name:'Statue',position:[0,0,0],rotation:[0,0,0],bounds:{min:[0,0,0],max:[1,8,1]},nearDistance:35,mediumDistance:140,tiers:[{triangles:1000},{triangles:30000},{triangles:400000}]};
const camera=new THREE.PerspectiveCamera();
const group=()=>{const g=new THREE.Group();g.add(new THREE.Mesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial()));return g;};
test('departing during an upgrade discards the late result and retains overview',async()=>{
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});
 const far=group();lod.load=async()=>far;lod.initialize({assets:[asset]});lod.update(camera);await tick();
 let resolve;lod.load=()=>new Promise(r=>{resolve=r;});camera.position.set(0,0,10);lod.update(camera);
 camera.position.set(0,0,1000);lod.update(camera);
 const late=group();let disposed=false;late.children[0].geometry.addEventListener('dispose',()=>disposed=true);resolve(late);await tick();
 assert.equal(root.children.length,1);assert.equal(root.children[0],far);assert.equal(far.visible,true);assert.equal(disposed,true);lod.dispose();
});
test('leaving a loaded detail releases GPU geometry and restores overview',async()=>{
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});const far=group(),near=group();
 lod.load=async()=>far;lod.initialize({assets:[asset]});lod.update(camera);await tick();lod.load=async()=>near;
 let disposed=false;near.children[0].geometry.addEventListener('dispose',()=>disposed=true);
 camera.position.set(0,0,10);lod.update(camera);await tick();assert.equal(far.visible,false);
 camera.position.set(0,0,1000);lod.update(camera);assert.equal(disposed,true);assert.equal(far.visible,true);assert.equal(root.children.length,1);lod.dispose();assert.equal(root.children.length,0);
});
test('failed upgrade keeps overview and does not retry every frame',async(t)=>{
 t.mock.method(console,'warn',()=>{});
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});const far=group();lod.load=async()=>far;lod.initialize({assets:[asset]});lod.update(camera);await tick();let count=0;lod.load=async()=>{count++;throw Error('offline');};
 camera.position.set(0,0,10);lod.update(camera);await tick();lod.update(camera);assert.equal(count,1);assert.equal(far.visible,true);lod.dispose();
});

test('instanced foliage releases instance buffers as well as geometry',()=>{
 const g=new THREE.Group(),mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial(),2);g.add(mesh);let instancesDisposed=false;mesh.addEventListener('dispose',()=>instancesDisposed=true);disposeGroup(g);assert.equal(instancesDisposed,true);
});

test('all queued assets have boxes before downloads complete, replaced only when ready',async()=>{
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',true,()=>{},()=>{});let resolve;
 lod.load=()=>new Promise(r=>{resolve=r;});lod.initialize({assets:[asset,{...asset,id:'second'}]});camera.position.set(0,0,1000);lod.update(camera);
 assert.equal(root.children.length,2);assert(root.children.every(g=>g.userData.loadingPlaceholder&&g.children.length===1));
 const box=root.children[0];let disposed=false;box.children[0].geometry.addEventListener('dispose',()=>disposed=true);
 const far=group();resolve(far);await tick();assert(root.children.includes(far));assert(!root.children.includes(box));assert(disposed);
 lod.update(camera);resolve(group());await tick();assert(root.children.every(g=>!g.userData.loadingPlaceholder));lod.dispose();assert.equal(root.children.length,0);
});
test('failed overview retains placeholder, allows other assets and retries successfully',async(t)=>{
 t.mock.method(console,'warn',()=>{});const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});
 lod.load=async a=>{if(a.id===asset.id)throw Error('offline');return group();};lod.initialize({assets:[asset,{...asset,id:'other'}]});lod.update(camera);await tick();
 assert.equal(root.children.length,2);assert.equal(root.children.filter(g=>g.userData.loadingPlaceholder).length,1);
 lod.entries[0].retryAt=0;lod.load=async()=>group();camera.position.set(0,0,1000);lod.update(camera);await tick();assert(root.children.every(g=>!g.userData.loadingPlaceholder));lod.dispose();
});

test('a nearby building progresses through all three tiers before distant downloads on one connection',async()=>{
 const lod=new CampusLod(new THREE.Group(),'http://localhost/',true,()=>{},()=>{});
 const log=[];lod.load=async(a,tier)=>{log.push([a.id,tier]);return group();};
 const distant={...asset,id:'distant',bounds:{min:[800,0,800],max:[810,8,810]}};
 const near={...asset,tiers:[{triangles:1000},{triangles:2000},{triangles:3000}]};
 lod.initialize({assets:[distant,near]});camera.position.set(0,0,10);
 for(let i=0;i<4;i++){lod.update(camera);await tick();}
 assert.deepEqual(log,[[near.id,0],[near.id,1],[near.id,2],[distant.id,0]]);lod.dispose();
});
test('slow connection serializes downloads and defers large close-ups',async()=>{
 const lod=new CampusLod(new THREE.Group(),'http://localhost/',false,()=>{},()=>{});
 lod.constrained=()=>true;
 const levels=[{triangles:100,bytes:5000},{triangles:900,bytes:50000},{triangles:5000,bytes:9000000}];
 const calls=[];lod.load=async(a,t)=>{calls.push([a.id,t]);return group();};
 lod.initialize({assets:[{...asset,tiers:levels},{...asset,id:'other',tiers:levels}]});
 camera.position.set(0,0,10);lod.update(camera);assert.equal(calls.length,1);await tick();
 for(let i=0;i<6;i++){lod.update(camera);await tick();}
 assert.equal(calls.length,4);assert(calls.every(([,tier])=>tier<2));lod.dispose();
});

test('progress waits for all staged detail and resumes on viewpoint changes',async()=>{
 const updates=[],lod=new CampusLod(new THREE.Group(),'http://localhost/',false,()=>{},()=>{},p=>updates.push(p));
 lod.load=async()=>group();lod.initialize({assets:[asset]});camera.position.set(0,0,10);
 for(let i=0;i<3;i++){lod.update(camera);await tick();if(i<2)assert.equal(updates.at(-1).complete,false);}
 assert.equal(updates.at(-1).complete,true);assert.equal(updates.at(-1).loaded,1);
 camera.position.set(0,0,1000);lod.update(camera);
 let resolve;lod.load=()=>new Promise(r=>resolve=r);camera.position.set(0,0,10);lod.update(camera);
 assert.equal(updates.at(-1).complete,false);assert.equal(updates.at(-1).active,1);
 resolve(group());await tick();assert.equal(updates.at(-1).complete,false);lod.dispose();
});
test('failed resources are reported and never count as complete',async(t)=>{
 t.mock.method(console,'warn',()=>{});let progress;
 const lod=new CampusLod(new THREE.Group(),'http://localhost/',false,()=>{},()=>{},p=>progress=p);
 lod.load=async()=>{throw Error('offline');};lod.initialize({assets:[asset]});camera.position.set(0,0,1000);lod.update(camera);await tick();
 assert.equal(progress.failed,1);assert.equal(progress.complete,false);assert.equal(progress.loaded,0);
 lod.entries[0].retryAt=0;lod.load=async()=>group();lod.update(camera);await tick();assert.equal(progress.complete,true);assert.equal(progress.failed,0);lod.dispose();
});
