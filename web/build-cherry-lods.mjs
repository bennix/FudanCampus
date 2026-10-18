import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {NodeIO} from '@gltf-transform/core';
import {ALL_EXTENSIONS} from '@gltf-transform/extensions';
import {prune,dedup,meshopt,dequantize,simplifyPrimitive,getBounds} from '@gltf-transform/functions';
import {MeshoptDecoder,MeshoptEncoder,MeshoptSimplifier} from 'meshoptimizer';
import {readModelBytes} from './read-model-bytes.mjs';
const pub=new URL('./public/',import.meta.url),path=new URL('campus-lod.json',pub),lod=JSON.parse(fs.readFileSync(path));
const source=JSON.parse(fs.readFileSync(new URL('campus-manifest.json',pub))).shared.find(a=>a.id==='guanghua-landscape');
await Promise.all([MeshoptDecoder.ready,MeshoptEncoder.ready,MeshoptSimplifier.ready]);
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({'meshopt.decoder':MeshoptDecoder,'meshopt.encoder':MeshoptEncoder});
const tiers=[];let bounds;
for(const level of ['far','middle','near']){
 const doc=await io.readBinary(readModelBytes(new URL(source.url,pub)));await doc.transform(dequantize());
 for(const n of [...doc.getRoot().listNodes()])if(n.getMesh()&&(n.getExtras().tree_group!=='V6 East spreading 01'||!['static',level].includes(n.getExtras().closeout_lod)))n.dispose();
 await doc.transform(prune());
 bounds??=getBounds(doc.getRoot().listScenes()[0]);
 for(const n of doc.getRoot().listNodes())if(n.getMesh()&&n.getExtras().closeout_lod==='static'&&level!=='near')for(const p of n.getMesh().listPrimitives())simplifyPrimitive(p,{simplifier:MeshoptSimplifier,ratio:level==='far'?.1:.5,error:.001,lockBorder:true});
 // Keep every original blossom/leaf card, texture and full near branch skeleton.
 await doc.transform(prune(),dedup(),meshopt({encoder:MeshoptEncoder,level:'medium',quantizePosition:16}));
 let triangles=0;for(const n of doc.getRoot().listNodes())for(const p of n.getMesh()?.listPrimitives()??[])triangles+=p.getIndices().getCount()/3;
 const bytes=await io.writeBinary(doc),url=`models/lod/guanghua-cherry-${level}.glb`;fs.writeFileSync(new URL(url,pub),bytes);tiers.push({url,bytes:bytes.length,triangles,revision:createHash('sha256').update(bytes).digest('hex').slice(0,12)});console.log('CHERRY_LOD',level,bytes.length,triangles);
}
lod.assets=lod.assets.filter(a=>a.id!=='guanghua-cherry');lod.assets.push({id:'guanghua-cherry',sourceId:'shared-guanghua-landscape',name:'东花园春樱',sourceRevision:source.revision,position:[0,0,0],rotation:[0,0,0],bounds,nearDistance:45,mediumDistance:140,tiers});fs.writeFileSync(path,JSON.stringify(lod,null,2)+'\n');
