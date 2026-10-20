import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {textureCompress,meshopt} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder} from 'meshoptimizer';
import sharp from 'sharp';
const pub=new URL('./public/',import.meta.url),file=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(file));
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
// Only new resources are compressed. Accepted resources retain their original bytes.
for(const a of lod.assets.filter(a=>a.sourceId?.startsWith('shared-photo-'))){
 for(let i=0;i<3;i++){
  const t=a.tiers[i],path=new URL(t.url,pub);const d=await io.read(path.pathname);
  await d.transform(textureCompress({encoder:sharp,resize:i===0?[128,128]:[512,512]}),meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));
  const b=await io.writeBinary(d);fs.writeFileSync(path,b);t.bytes=b.length;t.revision=createHash('sha256').update(b).digest('hex').slice(0,12);
 }
}
fs.writeFileSync(file,JSON.stringify(lod,null,2)+'\n');console.log('PHOTO_LODS_PACKED',lod.assets.length);
