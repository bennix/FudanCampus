import * as THREE from 'three';
import {inClaimedPlanting,legacyFacadeBounds,replacedIds} from '../lib/claimed-area.mjs';

// One translation for geometry, labels, cameras and picking. Map north stays -Z.
export const patchOffset = new THREE.Vector3(-167.2, .5, -116);
export const patchIds = new Set<string>(replacedIds);
export const patchPose = (p:number[]):[number,number,number] => [p[0]+patchOffset.x,p[1]+patchOffset.y,p[2]+patchOffset.z];

function identity(o:THREE.Object3D):string {
 for(let node:THREE.Object3D|null=o;node;node=node.parent){
  if(node.userData.building_id!==undefined)return String(node.userData.building_id);
 }
 return '';
}
const inPatch=(p:THREE.Vector3)=>inClaimedPlanting(p.x,p.z);

/** Remove old bodies and their batched facade triangles, preserving neighbours. */
export function pruneLegacyPatch(group:THREE.Group,assetUrl:string){
 group.updateMatrixWorld(true);
 const bodies:THREE.Object3D[]=[],bounds:THREE.Box3[]=[],names=new Set<string>();
 // Historic tiers batch the old roofs and glazing separately from tagged bodies.
 // Bounds measured from the three original 46 bodies in 01.glb, +1.3 margin.
 if(assetUrl==='shared-01'){
  bounds.push(...legacyFacadeBounds.map(([x0,z0,x1,z1]:number[])=>new THREE.Box3(new THREE.Vector3(x0,-10,z0),new THREE.Vector3(x1,40,z1))));
  names.add('第一教学楼');
 }
 group.traverse(o=>{
  if(o instanceof THREE.Mesh&&patchIds.has(identity(o))){
   bodies.push(o);bounds.push(new THREE.Box3().setFromObject(o).expandByScalar(1.3));
   if(o.userData.building_name)names.add(o.userData.building_name);
  }
 });
 bodies.forEach(o=>o.removeFromParent());
 const meshes:THREE.Mesh[]=[];
 group.traverse(o=>{if(o instanceof THREE.Mesh)meshes.push(o);});
 const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),centre=new THREE.Vector3();
 const vegetation=assetUrl==='shared-05'||assetUrl.startsWith('campus-tree-');
 for(const mesh of meshes){
  if(identity(mesh))continue;
  if([...names].some(name=>mesh.name.startsWith(name))){mesh.removeFromParent();continue;}
  const batch=/details/i.test(mesh.name);
  if(!vegetation&&!batch)continue;
  const box=new THREE.Box3().setFromObject(mesh);
  if(box.max.x<-255||box.min.x>-72||box.max.z<-168||box.min.z>-30)continue;
  const pos=mesh.geometry.getAttribute('position'),index=mesh.geometry.index;
  const count=index?.count??pos.count,keep:number[]=[];
  for(let i=0;i<count;i+=3){
   const ia=index?index.getX(i):i,ib=index?index.getX(i+1):i+1,ic=index?index.getX(i+2):i+2;
   a.fromBufferAttribute(pos,ia);b.fromBufferAttribute(pos,ib);c.fromBufferAttribute(pos,ic);
   centre.copy(a).add(b).add(c).multiplyScalar(1/3).applyMatrix4(mesh.matrixWorld);
   const remove=vegetation?inPatch(centre):bounds.some(bb=>centre.x>=bb.min.x&&centre.x<=bb.max.x&&centre.z>=bb.min.z&&centre.z<=bb.max.z);
   if(!remove)keep.push(ia,ib,ic);
  }
  if(keep.length===count)continue;
  if(!keep.length){mesh.removeFromParent();continue;}
  mesh.geometry=mesh.geometry.clone();mesh.geometry.setIndex(keep);
  mesh.geometry.computeBoundingBox();mesh.geometry.computeBoundingSphere();
 }
}
