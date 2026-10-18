import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {MeshoptDecoder} from 'three/addons/libs/meshopt_decoder.module.js';
import {allocateTiers,type Tier} from './lod-policy';
export type LodAsset={id:string;name:string;labelPosition?:[number,number,number];position:[number,number,number];rotation:[number,number,number];bounds:{min:[number,number,number];max:[number,number,number]};nearDistance:number;mediumDistance:number;tiers:{url:string;revision:string;bytes:number;triangles:number}[]};
export type LodManifest={version:number;assets:LodAsset[]};
export function disposeGroup(group:THREE.Object3D){
 const geometries=new Set<THREE.BufferGeometry>(),materials=new Set<THREE.Material>(),textures=new Set<THREE.Texture>();
 group.traverse(o=>{if(o instanceof THREE.Mesh){geometries.add(o.geometry);for(const m of Array.isArray(o.material)?o.material:[o.material]){materials.add(m);for(const v of Object.values(m))if(v instanceof THREE.Texture)textures.add(v);}}});
 geometries.forEach(g=>g.dispose());textures.forEach(t=>t.dispose());materials.forEach(m=>m.dispose());
}
export class CampusLod {
 private loader=new GLTFLoader().setMeshoptDecoder(MeshoptDecoder);
 private stopped=false;
 private active=0;
 private entries:{asset:LodAsset;box:THREE.Box3;far:THREE.Group;detail?:THREE.Group;current:Tier;wanted:Tier;request?:AbortController;retryAt:number;failures:number}[]=[];
 private pending=new Set<AbortController>();
 constructor(private root:THREE.Group,private base:string,private mobile:boolean,private prepare:(g:THREE.Group)=>void,private changed:()=>void){}
 private async load(asset:LodAsset,tier:Tier,signal:AbortSignal){
  const file=asset.tiers[tier];const url=new URL(file.url,this.base);url.searchParams.set('v',file.revision);
  const response=await fetch(url,{signal});if(!response.ok)throw Error(`${asset.name}: ${response.status}`);
  const data=await response.arrayBuffer();if(signal.aborted)throw new DOMException('Aborted','AbortError');
  const gltf=await this.loader.parseAsync(data,new URL('.',url).href);const g=gltf.scene;
  if(this.stopped||signal.aborted){disposeGroup(g);throw new DOMException('Aborted','AbortError');}
  g.userData.lodAssetId=asset.id;g.position.fromArray(asset.position);g.rotation.fromArray(asset.rotation);this.prepare(g);return g;
 }
 async initialize(manifest:LodManifest){
  const queue=[...manifest.assets];
  await Promise.all(Array.from({length:this.mobile?1:2},async()=>{while(queue.length&&!this.stopped){
   const asset=queue.shift()!;const request=new AbortController();this.pending.add(request);
   try{const far=await this.load(asset,0,request.signal);this.root.add(far);this.entries.push({asset,box:new THREE.Box3(new THREE.Vector3(...asset.bounds.min),new THREE.Vector3(...asset.bounds.max)),far,current:0,wanted:0,retryAt:0,failures:0});this.changed();}
   finally{this.pending.delete(request);}
  }}));
 }
 update(camera:THREE.Camera){
  if(this.stopped)return;
  const items=this.entries.map(e=>({id:e.asset.id,distance:e.box.distanceToPoint(camera.position),priority:e.box.distanceToPoint(camera.position)+e.box.getSize(new THREE.Vector3()).length()*.075,current:e.current,nearDistance:e.asset.nearDistance,mediumDistance:e.asset.mediumDistance,triangles:e.asset.tiers.map(t=>t.triangles)}));
  const targets=allocateTiers(items,this.mobile);
  for(const e of this.entries){
   const wanted=targets.get(e.asset.id)!;
   if(e.wanted!==wanted){e.request?.abort();e.retryAt=0;e.failures=0;}
   e.wanted=wanted;
   // Downgrade immediately, retain the overview while a replacement is loading.
   if(e.current>wanted){if(e.detail){this.root.remove(e.detail);disposeGroup(e.detail);e.detail=undefined;}e.far.visible=true;e.current=0;this.changed();}
  }
  for(const item of items.sort((a,b)=>a.priority-b.priority)){
   if(this.active>=(this.mobile?1:2))break;
   const e=this.entries.find(e=>e.asset.id===item.id)!;
   if(e.request||e.wanted===e.current||performance.now()<e.retryAt)continue;
   const tier=e.wanted,request=new AbortController();e.request=request;this.pending.add(request);this.active++;
   this.load(e.asset,tier,request.signal).then(g=>{
    if(this.stopped||e.wanted!==tier||request.signal.aborted){disposeGroup(g);return;}
    if(e.detail){this.root.remove(e.detail);disposeGroup(e.detail);}
    e.detail=g;this.root.add(g);e.far.visible=false;e.current=tier;e.failures=0;this.changed();
   }).catch(error=>{if(!request.signal.aborted&&!this.stopped){console.warn('LOD detail unavailable; overview retained',e.asset.id,error);e.failures++;e.retryAt=performance.now()+Math.min(60000,5000*2**e.failures);}}).finally(()=>{if(e.request===request)e.request=undefined;this.pending.delete(request);this.active--;});
  }
 }
 dispose(){this.stopped=true;this.pending.forEach(r=>r.abort());for(const e of this.entries){this.root.remove(e.far);disposeGroup(e.far);if(e.detail){this.root.remove(e.detail);disposeGroup(e.detail);}}this.entries=[];}
}
