import fs from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
const manifest=JSON.parse(fs.readFileSync(new URL('./public/campus-manifest.json',import.meta.url)));
for(const asset of manifest.buildings){
  const bytes=fs.readFileSync(new URL('./public/'+asset.url,import.meta.url));
  const gltf=await new GLTFLoader().parseAsync(bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),'');
  const bounds=new THREE.Box3().setFromObject(gltf.scene);
  for(const key of ['min','max'])for(let axis=0;axis<3;axis++){
    if(Math.abs(bounds[key].toArray()[axis]-asset.bounds[key][axis])>.002)throw Error(`${asset.id}: local bounds mismatch`);
  }
}
console.log('PASS: all eight GLBs load in Three.js with correct local bounds');
