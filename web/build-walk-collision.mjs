// Fixed collision geometry is independent of visual LOD swaps.
import fs from 'node:fs';
import {Matrix4,Vector3,Quaternion} from 'three';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {MeshoptDecoder} from 'meshoptimizer';
import {createHash} from 'node:crypto';
const pub=new URL('./public/',import.meta.url);await MeshoptDecoder.ready;
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder});
const lod=JSON.parse(fs.readFileSync(new URL('campus-lod.json',pub))),triangles=[],roofs=[];
for(const a of lod.assets){
 if(/^(campus-tree-|landscape-shrub-)/.test(a.id))continue;
 const doc=await io.read(new URL(a.tiers[0].url,pub).pathname);
 for(const n of doc.getRoot().listNodes()){
  const mesh=n.getMesh();if(!mesh)continue;
  const name=n.getName().toLowerCase();let extras={};for(let o=n;o;o=o.getParentNode())extras={...o.getExtras(),...extras};
  // Match the renderer: replaced legacy buildings must not leave invisible walls.
  if(['shared-02','shared-03'].includes(a.id)&&['3','5','7'].includes(String(extras.building_id??'')))continue;
  const trunk=/trunk|bark|tree stem/.test(name);
  if(!trunk&&(extras.campusVegetation||/canop|leav|leaf|foliage|blossom|flower|grass|shrub|lotus|lily|twig/.test(name)))continue;
  if(/joint|grout|letter|text|sign|ceiling grid|downlight|pebble|water|glazing|glass/.test(name))continue;
  const base=new Matrix4().fromArray(n.getWorldMatrix()),offset=a.position??[0,0,0],instance=n.getExtension('EXT_mesh_gpu_instancing');
  const translations=instance?.getAttribute('TRANSLATION'),rotations=instance?.getAttribute('ROTATION'),scales=instance?.getAttribute('SCALE');
  for(let inst=0;inst<(translations?.getCount()??rotations?.getCount()??scales?.getCount()??1);inst++){
  const transform=instance?new Matrix4().compose(new Vector3().fromArray(translations?.getElement(inst,[])??[0,0,0]),new Quaternion().fromArray(rotations?.getElement(inst,[])??[0,0,0,1]),new Vector3().fromArray(scales?.getElement(inst,[])??[1,1,1])):new Matrix4();const m=base.clone().multiply(transform).elements;
  const building=a.id.startsWith('buildings-')&&!['buildings-65'].includes(a.id)||a.sourceId==='shared-photo-teaching3'||a.sourceId==='shared-photo-yeyaozhen'||(extras.building_id&&!['3','5','7','65'].includes(String(extras.building_id)));
  for(const p of mesh.listPrimitives()){
   if(p.getMaterial()?.getAlphaMode()==='MASK'||p.getMode()!==4)continue;
   const pos=p.getAttribute('POSITION'),ix=p.getIndices();if(!pos)continue;
   for(let i=0;i<(ix?.getCount()??pos.getCount());i+=3){
    const v=[0,1,2].map(j=>{const q=pos.getElement(ix?ix.getScalar(i+j):i+j,[]);return [0,1,2].map(k=>m[k]*q[0]+m[k+4]*q[1]+m[k+8]*q[2]+m[k+12]+offset[k]);});
    const u=v[1].map((q,k)=>q-v[0][k]),w=v[2].map((q,k)=>q-v[0][k]);const cross=[u[1]*w[2]-u[2]*w[1],u[2]*w[0]-u[0]*w[2],u[0]*w[1]-u[1]*w[0]];
    if(Math.hypot(...cross)<.008)continue;
    triangles.push(...v.flat().map(q=>Math.round(q*1000)/1000));
    if(building&&!trunk&&Math.abs(cross[1])>.2&&Math.min(...v.map(q=>q[1]))>2&&Math.abs(cross[1])/Math.hypot(...cross)>.85)roofs.push(v.map(q=>[q[0],q[2]]));
   }
  }
 }
}
}
const data=Buffer.from(new Float32Array(triangles).buffer);fs.writeFileSync(new URL('walk-collision.bin',pub),data);
fs.writeFileSync(new URL('../field-review/campus-photo-integration/walk-roofs.json',import.meta.url),JSON.stringify(roofs));
fs.writeFileSync(new URL('walk-collision.json',pub),JSON.stringify({version:1,triangles:triangles.length/9,bytes:data.length,sha256:createHash('sha256').update(data).digest('hex'),sourceRevisions:lod.assets.map(a=>[a.id,a.tiers[0].revision])},null,2)+'\n');
console.log('WALK_COLLISION',triangles.length/9,'triangles',data.length,'bytes',roofs.length,'roof faces');
