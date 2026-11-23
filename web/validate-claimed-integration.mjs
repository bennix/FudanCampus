import fs from 'node:fs';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import sharp from 'sharp';
import {legacyClaimedTriangle} from './lib/claimed-area.mjs';
const src=fs.readFileSync(new URL('./app/CampusPatch.ts',import.meta.url),'utf8');
let js=ts.transpileModule(src,{compilerOptions:{module:ts.ModuleKind.ESNext,target:ts.ScriptTarget.ES2022}}).outputText;
js=js.replace("from 'three'",`from '${import.meta.resolve('three')}'`).replace("from '../lib/claimed-area.mjs'",`from '${new URL('./lib/claimed-area.mjs',import.meta.url).href}'`);
const {pruneLegacyPatch,patchIds}=await import('data:text/javascript;base64,'+Buffer.from(js).toString('base64'));
assert.deepEqual([...patchIds].sort(),['46','51','A05'],'Replacement is restricted to the approved map neighbourhood');
globalThis.self=globalThis;globalThis.createImageBitmap=async blob=>{const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});return {width:info.width,height:info.height,data,close(){}};};
const loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder),results=[];
for(const file of ['models/shared/01-hanbing-v14.glb','models/lod/shared-01-far.glb']){
 const b=fs.readFileSync(new URL('./public/'+file,import.meta.url));
 const {scene}=await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');scene.updateMatrixWorld(true);
 const saved=[];scene.traverse(o=>{if(o instanceof THREE.Mesh&&['42','43','44','45','47','48','50','52'].includes(String(o.userData.building_id??'')))saved.push([o,o.geometry.getAttribute('position').array.slice()]);});
 const count=()=>{let n=0;const v=new THREE.Vector3(),p=new THREE.Vector3();scene.traverse(o=>{if(!(o instanceof THREE.Mesh)||!/details/i.test(o.name))return;const a=o.geometry.getAttribute('position'),ix=o.geometry.index;for(let i=0;i<(ix?.count??a.count);i+=3){p.set(0,0,0);for(let j=0;j<3;j++)p.add(v.fromBufferAttribute(a,ix?ix.getX(i+j):i+j));p.multiplyScalar(1/3).applyMatrix4(o.matrixWorld);if(p.x>=-184.5&&p.x<=-149.9&&p.z>=-132.9&&p.z<=-99.1)n++;}});return n;};
 const before=count();assert(before>0);pruneLegacyPatch(scene,'shared-01');assert.equal(count(),0);
 scene.traverse(o=>assert(!patchIds.has(String(o.userData.building_id??'')),`Legacy building remains: ${o.name}`));
 for(const [object,positions] of saved){assert(object.parent);assert.deepEqual(object.geometry.getAttribute('position').array,positions);}
 results.push({file,before,after:count(),protectedMeshes:saved.length});
}
assert(legacyClaimedTriangle('shared-01','46','body',[[0,0,0],[0,0,1],[1,0,0]]));
assert(!legacyClaimedTriangle('buildings-46','46','body',[[0,0,0],[0,0,1],[1,0,0]]));
assert(!legacyClaimedTriangle('shared-01','43','neighbour',[[-230,0,-100],[-230,1,-100],[-229,0,-100]]));
const lod=JSON.parse(fs.readFileSync(new URL('./public/campus-lod.json',import.meta.url)));
assert(lod.assets.some(a=>a.id==='buildings-46')&&lod.assets.some(a=>a.id==='buildings-51'));
const contextIds=['44','45','47','48','50','52','56'];
for(const tier of lod.assets.find(a=>a.id==='shared-claimed-46-51-landscape').tiers){
 const b=fs.readFileSync(new URL('./public/'+tier.url,import.meta.url));
 const {scene}=await loader.parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');scene.updateMatrixWorld(true);
 scene.traverse(o=>assert(!contextIds.includes(String(o.userData.building_id??'')),`Simplified neighbour remains in ${tier.url}`));
}
assert(lod.assets.some(a=>a.id==='buildings-56'&&a.tiers[2].triangles>400000),'Detailed library must remain available');
const landing=fs.readFileSync(new URL('./app/page.tsx',import.meta.url),'utf8');assert(landing.includes('campus-gate.webp')&&landing.includes('CampusScene=lazy'));
const report={passed:true,fixtures:results,landingPreserved:true,protected42and43Preserved:true,mapContextIds:contextIds,simplifiedNeighboursExcludedAcrossThreeTiers:true,legacyA05Removed:true};
fs.writeFileSync(new URL('../field-review/zheng-dehong-46-51/integration-validation.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log('PASS',report);
