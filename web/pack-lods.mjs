import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {textureCompress,meshopt} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
import sharp from 'sharp';
const pub=new URL('./public/',import.meta.url),path=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(path));
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
for(const a of lod.assets){
 if(a.id==='shared-guanghua-landscape'||(process.argv[2]&&a.id!==process.argv[2]))continue;
 for(let i=0;i<2;i++){
  const t=a.tiers[i],file=new URL(t.url,pub),doc=await io.read(file.pathname);
  await doc.transform(textureCompress({encoder:sharp,resize:i===0?[128,128]:[512,512]}),meshopt({encoder:MeshoptEncoder,level:'medium'}));
  const bytes=await io.writeBinary(doc);fs.writeFileSync(file,bytes);t.bytes=bytes.length;t.revision=createHash('sha256').update(bytes).digest('hex').slice(0,12);
 }
}
for(const a of lod.assets)for(const t of a.tiers){const b=fs.readFileSync(new URL(t.url,pub));const g=JSON.parse(b.subarray(20,20+b.readUInt32LE(12)));t.triangles=g.nodes.filter(n=>n.mesh!=null).reduce((sum,n)=>sum+g.meshes[n.mesh].primitives.reduce((s,p)=>s+g.accessors[p.indices].count/3,0)*(n.extensions?.EXT_mesh_gpu_instancing?g.accessors[Object.values(n.extensions.EXT_mesh_gpu_instancing.attributes)[0]].count:1),0);}
fs.writeFileSync(path,JSON.stringify(lod,null,2)+'\n');console.log('PACKED_LODS',lod.assets.length,lod.assets.reduce((sum,a)=>sum+a.tiers[0].bytes,0));
