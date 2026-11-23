import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';
const source=fs.readFileSync(new URL('./app/CampusXR.ts',import.meta.url),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
// Resolve the same Three.js module as tests; no copied implementation.
const rewritten=js.replace("from 'three'",`from '${new URL('./node_modules/three/build/three.module.js',import.meta.url).href}'`);
const {teleportRig,pickTeleport,teleportStops}=await import('data:text/javascript;base64,'+Buffer.from(rewritten).toString('base64'));
const rig=new THREE.Group();rig.position.set(10,.56,15);
teleportRig(rig,new THREE.Vector3(10.4,2.2,14.7),new THREE.Vector3(-139,.56,-61));
assert(Math.abs(rig.position.x+.4+139)<1e-9);
assert(Math.abs(rig.position.z-.3+61)<1e-9);
assert.equal(rig.position.y,.56);
const target=new THREE.Mesh(new THREE.SphereGeometry(.4),new THREE.MeshBasicMaterial());target.position.z=-5;target.updateMatrixWorld();
const wall=new THREE.Mesh(new THREE.BoxGeometry(2,2,.5),new THREE.MeshBasicMaterial());wall.position.z=-2;wall.updateMatrixWorld();
const ray=new THREE.Raycaster(new THREE.Vector3(),new THREE.Vector3(0,0,-1),0,90);
assert.equal(pickTeleport(ray,[target],[]),target);
assert.equal(pickTeleport(ray,[target],[wall]),undefined);
const hidden=new THREE.Group();hidden.visible=false;hidden.add(wall);hidden.updateMatrixWorld(true);
assert.equal(pickTeleport(ray,[target],[wall]),target);
ray.ray.direction.set(1,0,0);assert.equal(pickTeleport(ray,[target],[]),undefined);
const trace=JSON.parse(fs.readFileSync(new URL('./public/map-review/trace.json',import.meta.url)));
const inside=(p,poly)=>{let hit=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])hit=!hit;}return hit;};
for(const stop of teleportStops){const [x,,z]=stop.position;const pixel=[(x+167.2)/.48+176,(z+116)/.48+107];for(const blocks of Object.values(trace.parts))for(const [,poly] of blocks)assert(!inside(pixel,poly),`${stop.id} inside building`);}
const result={passed:true,checks:['room-scale head offset preserved','floor elevation preserved','visible target selectable','wall occlusion rejects teleport','hidden ancestor ignored','ray miss rejected','all landing points outside traced buildings'],realHeadsetTested:false};
fs.mkdirSync(new URL('../output/',import.meta.url),{recursive:true});fs.writeFileSync(new URL('../output/xr-validation.json',import.meta.url),JSON.stringify(result,null,2));console.log(result);
