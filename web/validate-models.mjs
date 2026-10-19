import fs from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import sharp from 'sharp';
import { createHash } from 'node:crypto';
const protection=JSON.parse(fs.readFileSync(new URL('../assets/protected-buildings.json',import.meta.url)));
for(const [relative,expected] of Object.entries(protection.files)){
  let bytes=fs.readFileSync(new URL('../'+relative,import.meta.url));
  if(protection.textFiles?.includes(relative))bytes=Buffer.from(bytes.toString('utf8').replace(/\r\n/g,'\n'));
  const actual=createHash('sha256').update(bytes).digest('hex');
  if(actual!==expected)throw Error(`Protected accepted file changed: ${relative}`);
}
// Decode embedded images during Node validation; browser QA checks actual GPU rendering.
globalThis.self=globalThis;
globalThis.createImageBitmap=async blob=>{
  const {data,info}=await sharp(Buffer.from(await blob.arrayBuffer())).ensureAlpha().raw().toBuffer({resolveWithObject:true});
  return {width:info.width,height:info.height,data,close(){}};
};
const manifest=JSON.parse(fs.readFileSync(new URL('./public/campus-manifest.json',import.meta.url)));
for(const asset of manifest.buildings){
  if(asset.overviewMode==='full'){
    for(const key of ['url','revision','bytes'])if(asset.overview[key]!==asset[key])throw Error(`${asset.id}: intact overview must reuse detail ${key}`);
  }
  const bytes=fs.readFileSync(new URL('./public/'+asset.url,import.meta.url));
  const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const bounds=new THREE.Box3().setFromObject(gltf.scene);
  for(const key of ['min','max'])for(let axis=0;axis<3;axis++){
    if(Math.abs(bounds[key].toArray()[axis]-asset.bounds[key][axis])>.002)throw Error(`${asset.id}: local bounds mismatch`);
  }
  const overviewBytes=fs.readFileSync(new URL('./public/'+asset.overview.url,import.meta.url));
  const overview=await new GLTFLoader().parseAsync(overviewBytes.buffer.slice(overviewBytes.byteOffset,overviewBytes.byteOffset+overviewBytes.byteLength),'');
  const overviewBounds=new THREE.Box3().setFromObject(overview.scene);
  if(overviewBounds.isEmpty())throw Error(`${asset.id}: empty overview`);
  if(asset.id==='42')for(const key of ['min','max'])for(let axis=0;axis<3;axis++){
    if(Math.abs(overviewBounds[key].toArray()[axis]-asset.bounds[key][axis])>.1)throw Error('42: overview silhouette bounds changed');
  }
}
console.log(`PASS: ${manifest.buildings.length} detail and overview GLBs load in Three.js; embedded images decode and local bounds match`);
await import('./validate-hanbing-context.mjs');
if(manifest.buildings.some(a=>a.id==='17'))await import('./validate-teaching4.mjs');
if(manifest.shared.some(a=>a.id==='guanghua-landscape'))await import('./validate-guanghua-integration.mjs');
