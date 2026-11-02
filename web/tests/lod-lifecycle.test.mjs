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
 const far=group();lod.load=async()=>far;await lod.initialize({assets:[asset]});
 let resolve;lod.load=()=>new Promise(r=>{resolve=r;});camera.position.set(0,0,10);lod.update(camera);
 camera.position.set(0,0,1000);lod.update(camera);
 const late=group();let disposed=false;late.children[0].geometry.addEventListener('dispose',()=>disposed=true);resolve(late);await tick();
 assert.equal(root.children.length,1);assert.equal(root.children[0],far);assert.equal(far.visible,true);assert.equal(disposed,true);lod.dispose();
});
test('leaving a loaded detail releases GPU geometry and restores overview',async()=>{
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});const far=group(),near=group();
 lod.load=async()=>far;await lod.initialize({assets:[asset]});lod.load=async()=>near;
 let disposed=false;near.children[0].geometry.addEventListener('dispose',()=>disposed=true);
 camera.position.set(0,0,10);lod.update(camera);await tick();assert.equal(far.visible,false);
 camera.position.set(0,0,1000);lod.update(camera);assert.equal(disposed,true);assert.equal(far.visible,true);assert.equal(root.children.length,1);lod.dispose();assert.equal(root.children.length,0);
});
test('failed upgrade keeps overview and does not retry every frame',async(t)=>{
 t.mock.method(console,'warn',()=>{});
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});const far=group();lod.load=async()=>far;await lod.initialize({assets:[asset]});let count=0;lod.load=async()=>{count++;throw Error('offline');};
 camera.position.set(0,0,10);lod.update(camera);await tick();lod.update(camera);assert.equal(count,1);assert.equal(far.visible,true);lod.dispose();
});

test('instanced foliage releases instance buffers as well as geometry',()=>{
 const g=new THREE.Group(),mesh=new THREE.InstancedMesh(new THREE.BoxGeometry(),new THREE.MeshBasicMaterial(),2);g.add(mesh);let instancesDisposed=false;mesh.addEventListener('dispose',()=>instancesDisposed=true);disposeGroup(g);assert.equal(instancesDisposed,true);
});

test('all queued assets have boxes before downloads complete, replaced only when ready',async()=>{
 const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',true,()=>{},()=>{});let resolve;
 lod.load=()=>new Promise(r=>{resolve=r;});const initialized=lod.initialize({assets:[asset,{...asset,id:'second'}]});
 assert.equal(root.children.length,2);assert(root.children.every(g=>g.userData.loadingPlaceholder&&g.children.length===1));
 const box=root.children[0];let disposed=false;box.children[0].geometry.addEventListener('dispose',()=>disposed=true);
 const far=group();resolve(far);await tick();assert(root.children.includes(far));assert(!root.children.includes(box));assert(disposed);
 resolve(group());await initialized;assert(root.children.every(g=>!g.userData.loadingPlaceholder));lod.dispose();assert.equal(root.children.length,0);
});
test('failed overview retains placeholder, allows other assets and retries successfully',async(t)=>{
 t.mock.method(console,'warn',()=>{});const root=new THREE.Group(),lod=new CampusLod(root,'http://localhost/',false,()=>{},()=>{});
 lod.load=async a=>{if(a.id===asset.id)throw Error('offline');return group();};await lod.initialize({assets:[asset,{...asset,id:'other'}]});
 assert.equal(root.children.length,2);assert.equal(root.children.filter(g=>g.userData.loadingPlaceholder).length,1);
 lod.entries[0].retryAt=0;lod.load=async()=>group();camera.position.set(0,0,1000);lod.update(camera);await tick();assert(root.children.every(g=>!g.userData.loadingPlaceholder));lod.dispose();
});
