// The renderer and fixed collision builder share the same legacy replacement area.
export const legacy46Bounds=[-184.5,-132.9,-149.9,-99.1];
export const contextIds=['44','45','47','48','50','52','56'];
export const replacedIds=['46','51','A05'];
// Historic shared meshes have untagged facade batches. These measured bounds
// remove their remnants without touching 42/43 or any source GLB on disk.
export const legacyFacadeBounds=[legacy46Bounds];
export const patchGroundPixels=[[30,0],[252,0],[252,100],[370,100],[370,240],[252,240],[252,250],[242,250],[242,278],[126,278],[126,260],[0,260],[0,160],[30,160]];
export function inClaimedPlanting(x,z){
 const u=(x+167.2)/.48+176,v=(z+116)/.48+107;
 let inside=false;
 for(let i=0,j=patchGroundPixels.length-1;i<patchGroundPixels.length;j=i++){
  const a=patchGroundPixels[i],b=patchGroundPixels[j];
  if((a[1]>v)!==(b[1]>v)&&u<(b[0]-a[0])*(v-a[1])/(b[1]-a[1])+a[0])inside=!inside;
 }
 return inside;
}
export function legacyClaimedTriangle(assetId,buildingId,name,vertices){
 if(['buildings-46','buildings-51','shared-claimed-46-51-landscape'].includes(assetId))return false;
 if(replacedIds.includes(String(buildingId??'')))return true;
 const x=vertices.reduce((s,v)=>s+v[0],0)/3,z=vertices.reduce((s,v)=>s+v[2],0)/3;
 if(assetId==='shared-01'&&/details/i.test(name))return legacyFacadeBounds.some(b=>x>=b[0]&&x<=b[2]&&z>=b[1]&&z<=b[3]);
 return (assetId==='shared-05'||assetId.startsWith('campus-tree-'))&&inClaimedPlanting(x,z);
}
