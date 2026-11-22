// The renderer and fixed collision builder share the same legacy replacement area.
export const legacy46Bounds=[-184.5,-132.9,-149.9,-99.1];
export function inClaimedPlanting(x,z){
 const u=(x+167.2)/.48+176,v=(z+116)/.48+107;
 return u>=110&&u<=242&&v>=35&&v<=255;
}
export function legacyClaimedTriangle(assetId,buildingId,name,vertices){
 if(['buildings-46','buildings-51','shared-claimed-46-51-landscape'].includes(assetId))return false;
 if(['46','51'].includes(String(buildingId??'')))return true;
 const x=vertices.reduce((s,v)=>s+v[0],0)/3,z=vertices.reduce((s,v)=>s+v[2],0)/3;
 if(assetId==='shared-01'&&/details/i.test(name))return x>=legacy46Bounds[0]&&x<=legacy46Bounds[2]&&z>=legacy46Bounds[1]&&z<=legacy46Bounds[3];
 return (assetId==='shared-05'||assetId.startsWith('campus-tree-'))&&inClaimedPlanting(x,z);
}
