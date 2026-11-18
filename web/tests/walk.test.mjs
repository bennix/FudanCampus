import {test} from 'node:test';import assert from 'node:assert/strict';
import * as THREE from 'three';import {WalkWorld,Walker,blockedInterior} from '../lib/campus-walk.ts';
import fs from 'node:fs';
function box(x,y,z,w,h,d){const g=new THREE.BoxGeometry(w,h,d).toNonIndexed();g.translate(x,y,z);return [...g.attributes.position.array];}
const floor=box(0,-.1,0,100,.2,100);
const ring=[[-5,-5],[5,-5],[5,5],[-5,5],[-5,-5]],hole=[[-2,-2],[2,-2],[2,2],[-2,2],[-2,-2]];
test('closed building interior blocks doors while open courtyard stays accessible',()=>{const p=[{bounds:[-5,-5,5,5],rings:[ring,hole]}];assert.equal(blockedInterior(0,0,p),false);assert.equal(blockedInterior(3,0,p),true);assert.equal(blockedInterior(8,0,p),false);assert.equal(blockedInterior(1.9,0,p),true);});
test('open ground allows walking in arbitrary directions, keeps human eye height',()=>{const w=new Walker(new WalkWorld(new Float32Array(floor),[]),new THREE.Vector3());for(let i=0;i<120;i++)w.move(new THREE.Vector3(1,0,1).normalize(),1/60);assert(w.eye().x>3&&w.eye().z>3);assert(Math.abs(w.eye().y-1.67)<.03);});
test('sustained movement and long frames cannot tunnel through thin walls',()=>{const world=new WalkWorld(new Float32Array([...floor,...box(2,1,0,.1,2,12)]),[]);const w=new Walker(world,new THREE.Vector3());for(let i=0;i<180;i++)w.move(new THREE.Vector3(1,0,0),i%2?1/60:1,4.5);assert(w.eye().x<1.66,w.eye().x);assert(w.eye().x>1.5);});
test('sealed building cannot be entered through a geometrically open doorway',()=>{const world=new WalkWorld(new Float32Array(floor),[{bounds:[2,-3,6,3],rings:[[[2,-3],[6,-3],[6,3],[2,3],[2,-3]]]}]);const w=new Walker(world,new THREE.Vector3());for(let i=0;i<240;i++)w.move(new THREE.Vector3(1,0,0),1/60);assert(w.eye().x<=1.71);});
test('actual campus collision loads and new outdoor regions have safe spawns',()=>{const bytes=fs.readFileSync(new URL('../public/walk-collision.bin',import.meta.url));const data=new Float32Array(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength));const interiors=JSON.parse(fs.readFileSync(new URL('../public/walk-interiors.json',import.meta.url)));const world=new WalkWorld(data,interiors);for(const p of [[-40,0,14],[21,0,-85],[72,0,0],[30,0,-21]]){const w=new Walker(world,new THREE.Vector3(...p));for(let i=0;i<60;i++){w.move(new THREE.Vector3(0,0,-1),1/60);assert(!world.blocked(w.eye().x,w.eye().z));assert(Number.isFinite(w.eye().y));}assert(w.eye().y>0);}});
test('both gate lanes open from either side and allow a full crossing',async()=>{
 const {createGateArms}=await import('../lib/gate-arms.mjs');
 const bytes=fs.readFileSync(new URL('../public/walk-collision.bin',import.meta.url));
 const world=new WalkWorld(new Float32Array(bytes.buffer,bytes.byteOffset,bytes.length/4),JSON.parse(fs.readFileSync(new URL('../public/walk-interiors.json',import.meta.url))));
 for(const x of [-42,-38])for(const sign of [-1,1]){
  const gate=createGateArms(),walker=new Walker(world,new THREE.Vector3(x,0,-9.16-sign*12));
  const direction=new THREE.Vector3(0,0,sign);let passed=false;
  for(let i=0;i<380;i++){
   walker.move(direction,1/60,4.5);const eye=walker.eye();gate.update(eye,1/60);
   if(Math.abs(eye.z+9.16)<.3){passed=true;assert(gate.group.children[0].rotation.z>1.4);assert(gate.group.children[1].rotation.z< -1.4);}
  }
  assert(passed);assert((walker.eye().z+9.16)*sign>10);
  for(let i=0;i<100;i++)gate.update(walker.eye(),1/60);
  assert.equal(gate.group.children[0].rotation.z,0);
 }
});
test('walk from the default gate viewpoint across the raised road and through the entrance',()=>{
 const bytes=fs.readFileSync(new URL('../public/walk-collision.bin',import.meta.url));
 const world=new WalkWorld(new Float32Array(bytes.buffer,bytes.byteOffset,bytes.length/4),JSON.parse(fs.readFileSync(new URL('../public/walk-interiors.json',import.meta.url))));
 for(const fps of [20,30,60])for(const speed of [2.5,4.5]){
  const w=new Walker(world,new THREE.Vector3(-46,0,27.6));
  const direction=new THREE.Vector3(6,0,-34).normalize();
  for(let i=0;i<Math.ceil(46/speed*fps);i++)w.move(direction,1/fps,speed);
  assert(w.eye().z < -15,JSON.stringify(w.eye()));
 }
});
